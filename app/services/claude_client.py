import os
import json
import time
import anthropic
from flask import current_app
import pandas as pd
from ..models import Dataset

class ClaudeClient:
    """Service for interacting with the Anthropic Claude API."""
    
    def __init__(self):
        """Initialize the Claude client with placeholders."""
        self.client = None
        # Reverted to your original model name as a default.
        # This should ideally be configured via ANTHROPIC_MODEL_NAME in .env
        self.model_name = "claude-3-7-sonnet-20250219" 
        self.api_key = None
        self.max_retries = 3
        self.retry_delay = 5 
        self.max_tokens_dashboard = 15000
        self.temperature_dashboard = 0.7
        self.max_tokens_analysis = 4000
        self.temperature_analysis = 0.5

    def init_app(self, app):
        """Initialize with application-specific configuration."""
        self.model_name = app.config.get("ANTHROPIC_MODEL_NAME", self.model_name)
        self.api_key = app.config.get('ANTHROPIC_API_KEY')
        self.max_retries = app.config.get("ANTHROPIC_MAX_RETRIES", self.max_retries)
        self.retry_delay = app.config.get("ANTHROPIC_RETRY_DELAY", self.retry_delay)
        self.max_tokens_dashboard = app.config.get("ANTHROPIC_MAX_TOKENS_DASHBOARD", self.max_tokens_dashboard)
        self.temperature_dashboard = app.config.get("ANTHROPIC_TEMPERATURE_DASHBOARD", self.temperature_dashboard)
        self.max_tokens_analysis = app.config.get("ANTHROPIC_MAX_TOKENS_ANALYSIS", self.max_tokens_analysis)
        self.temperature_analysis = app.config.get("ANTHROPIC_TEMPERATURE_ANALYSIS", self.temperature_analysis)

        if not self.api_key:
            app.logger.warning("Anthropic API key is not set in config. ClaudeClient will not function if API calls are made.")

    def _initialize_client(self):
        if not self.client:
            if not self.api_key:
                current_app.logger.error("Anthropic API key is missing. Cannot initialize client.")
                raise ValueError("Anthropic API key is not set. ClaudeClient cannot be initialized.")
            
            try:
                current_app.logger.info(f"Initializing Anthropic client with model: {self.model_name}, SDK version: {anthropic.__version__}")
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                current_app.logger.error(f"Error initializing Anthropic client: {str(e)}", exc_info=True)
                raise
    
    def _get_dataset_metadata(self, dataset_id):
        dataset = Dataset.query.get_or_404(dataset_id)
        file_path = dataset.file_path

        if not os.path.exists(file_path):
            current_app.logger.error(f"Dataset file not found for metadata: {file_path}")
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        column_info = {}
        df_preview = None 
        full_df_for_stats = None

        try:
            if dataset.file_type.lower() == 'csv':
                df_preview = pd.read_csv(file_path, nrows=5) 
                full_df_for_stats = pd.read_csv(file_path)
            elif dataset.file_type.lower() == 'json':
                full_df_for_stats = pd.read_json(file_path) 
                df_preview = full_df_for_stats.head(5)
            else:
                current_app.logger.error(f"Unsupported file type for metadata: {dataset.file_type}")
                raise ValueError(f"Unsupported file type: {dataset.file_type}")
                
            for col_name_original in full_df_for_stats.columns:
                col_name = str(col_name_original)
                col_series = full_df_for_stats[col_name_original]
                col_type_str = str(col_series.dtype)
                stats = {"type": col_type_str, "name": col_name}

                if pd.api.types.is_numeric_dtype(col_series):
                    stats.update({
                        "min": float(col_series.min()) if pd.notna(col_series.min()) else None,
                        "max": float(col_series.max()) if pd.notna(col_series.max()) else None,
                        "mean": float(col_series.mean()) if pd.notna(col_series.mean()) else None,
                        "median": float(col_series.median()) if pd.notna(col_series.median()) else None,
                        "std": float(col_series.std()) if pd.notna(col_series.std()) else None
                    })
                elif pd.api.types.is_datetime64_any_dtype(col_series):
                    stats["type"] = "datetime"
                    stats.update({
                        "min": col_series.min().isoformat() if pd.notna(col_series.min()) else None,
                        "max": col_series.max().isoformat() if pd.notna(col_series.max()) else None
                    })
                elif pd.api.types.is_categorical_dtype(col_series) or pd.api.types.is_object_dtype(col_series) or pd.api.types.is_string_dtype(col_series):
                    unique_values_count = col_series.nunique()
                    stats["unique_values"] = int(unique_values_count)
                    if unique_values_count > 0 and unique_values_count < 10 : # Check if series is not all NaN for value_counts
                         stats["top_values"] = col_series.value_counts().head(5).to_dict()
                    elif unique_values_count > 0:
                        stats["example_values"] = col_series.dropna().unique()[:3].tolist()
                    else: # All NaN case
                        stats["example_values"] = []


                column_info[col_name] = stats
                
        except Exception as e:
            current_app.logger.warning(f"Could not generate detailed column statistics for dataset {dataset_id}: {str(e)}", exc_info=True)
            if df_preview is not None:
                for col_name_original in df_preview.columns:
                    col_name = str(col_name_original)
                    column_info[col_name] = {"type": str(df_preview[col_name_original].dtype), "name": col_name}
            else:
                 column_info = {"error": "Could not load dataframe to extract column info."}

        return {
            "original_filename": dataset.original_filename,
            "file_type": dataset.file_type,
            "n_rows": dataset.n_rows,
            "n_columns": dataset.n_columns,
            "column_info": column_info
        }

    def _create_dashboard_prompt(self, dataset_metadata, title, description=""):
        column_info_str = json.dumps(dataset_metadata["column_info"], indent=2)
        
        prompt = f"""
        You are an expert data visualization web developer. Your task is to create a complete, interactive, self-contained HTML file (with embedded CSS and JavaScript) that serves as a template for a dashboard. This template will later be populated with actual data.

        # Dashboard Information
        Title: {title}
        Description: {description} (Use this to guide the theme and focus of the dashboard)

        # Dataset Structure (Metadata only)
        Filename: {dataset_metadata['original_filename']}
        Type: {dataset_metadata['file_type']}
        Approximate Rows: {dataset_metadata['n_rows']}
        Number of Columns: {dataset_metadata['n_columns']}
        
        # Column Information (Schema and basic statistics):
        {column_info_str}
        
        # CRITICAL DATA INJECTION INSTRUCTION:
        The actual dataset will be injected into the dashboard via a global JavaScript variable: `window.dynadashData`.
        This `window.dynadashData` will be an array of JavaScript objects, where each object represents a row from the dataset.
        For example, if the dataset has columns "Name" (string) and "Age" (number), `window.dynadashData` would look like:
        `[
          {{ "Name": "Alice", "Age": 30, ... }},
          {{ "Name": "Bob", "Age": 24, ... }},
          ...
        ]`
        Your generated JavaScript code MUST:
        1. Access the data exclusively from `window.dynadashData`.
        2. Perform any necessary data transformations (e.g., string to number, date parsing if strings) on `window.dynadashData` before using it in charts.
        3. Do NOT embed any static example data directly into the script for the main visualizations. Placeholder data for UI layout during development is fine, but it should be replaced by `window.dynadashData`.
        4. Initialize all charts and interactive elements using the data from `window.dynadashData`.

        # Requirements for the Dashboard Template:
        1.  **Self-Contained HTML:** Produce a single HTML file with all CSS (in `<style>` tags) and JavaScript (in `<script>` tags) embedded.
        2.  **Multiple Visualizations:** Include at least 3-5 diverse and complementary charts (e.g., bar, line, scatter, pie, heatmap) suitable for the provided column types and dataset description.
        3.  **Interactivity:** Implement interactive elements (e.g., filters based on categorical columns, date range selectors if applicable, tooltips on charts). These interactive elements should dynamically update the visualizations based on `window.dynadashData`.
        4.  **Layout & Styling:**
            *   Professionally designed, responsive, and visually appealing.
            *   Clear sections, headers, and potentially a summary/KPI section.
            *   Use a modern, clean aesthetic.
        5.  **Chart Libraries:** Use Chart.js (preferred for simplicity and wide compatibility) or D3.js for visualizations. Ensure the necessary library is linked via CDN if not fully embedded.
        6.  **Chart Best Practices:** Ensure charts have titles, axis labels, and legends where appropriate.
        7.  **Robust Initialization:** All JavaScript code for chart creation (e.g., `new Chart(ctx, config)`) must be complete and self-initializing on DOM load, using `window.dynadashData`.
        8.  **Error Handling (Basic):** The JavaScript should be robust enough not to break completely if `window.dynadashData` is empty or has unexpected minor variations (though assume the schema provided is generally correct).
        9.  **No External File Dependencies:** All assets like CSS or JS code snippets must be embedded. CDN links for major libraries (Chart.js, D3.js) are acceptable.

        # Response Format:
        Return ONLY the complete HTML code for the dashboard template, starting with `<!DOCTYPE html>`. Do not include any explanations, comments, or markdown formatting outside the HTML itself.
        The HTML should be ready to have the `window.dynadashData` variable populated and then viewed in a browser.
        """
        return prompt.strip()
    
    def generate_dashboard(self, dataset_id, title, description="", use_thinking=False):
        self._initialize_client()
        
        dataset_metadata = self._get_dataset_metadata(dataset_id)
        prompt = self._create_dashboard_prompt(dataset_metadata, title, description)
        
        current_app.logger.info(f"Requesting dashboard generation from Claude for dataset_id: {dataset_id}, title: '{title}'")

        for attempt in range(self.max_retries):
            try:
                params = {
                    "model": self.model_name,
                    "max_tokens": self.max_tokens_dashboard,
                    "temperature": self.temperature_dashboard,
                    "system": "You are a data visualization expert that creates beautiful, interactive dashboard HTML templates using HTML, CSS, and JavaScript. The data will be injected via a `window.dynadashData` variable. You only respond with complete HTML code, with no explanations or Markdown outside the HTML itself.",
                    "messages": [{"role": "user", "content": prompt}]
                }
                
                if use_thinking:
                     current_app.logger.info("Note: 'use_thinking' parameter usage is illustrative.")

                response = self.client.messages.create(**params)
                
                dashboard_html_template = None
                if response.content and isinstance(response.content, list):
                    for block in response.content:
                        if block.type == 'text':
                            dashboard_html_template = block.text
                            break
                
                if not dashboard_html_template:
                    current_app.logger.error("No text content found in Claude's response.")
                    raise ValueError("No text content found in the response from Claude.")
                
                if dashboard_html_template.strip().startswith("```html"):
                    dashboard_html_template = dashboard_html_template.split("```html", 1)[-1]
                    if dashboard_html_template.strip().endswith("```"):
                        dashboard_html_template = dashboard_html_template.rsplit("```", 1)[0]
                elif dashboard_html_template.strip().startswith("```"):
                     dashboard_html_template = dashboard_html_template.strip()[3:-3] if dashboard_html_template.strip().endswith("```") else dashboard_html_template.strip()[3:]

                dashboard_html_template = dashboard_html_template.strip()
                
                sanitized_template = self._sanitize_dashboard_html(dashboard_html_template)
                
                current_app.logger.debug(f"Generated dashboard HTML template (first 500 chars): {sanitized_template[:500]}...")
                current_app.logger.info(f"Successfully generated dashboard template from Claude for dataset_id: {dataset_id}.")
                return sanitized_template
                    
            except anthropic.APIConnectionError as e:
                current_app.logger.error(f"Claude API connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1: raise
                time.sleep(self.retry_delay * (attempt + 1))
            except anthropic.RateLimitError as e:
                current_app.logger.error(f"Claude API rate limit error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1: raise
                time.sleep(self.retry_delay * (attempt + 1) * 2) 
            except anthropic.APIStatusError as e: # Specific check for NotFoundError which indicates model name issue
                if isinstance(e, anthropic.NotFoundError):
                    current_app.logger.error(f"Claude API NotFoundError (attempt {attempt + 1}/{self.max_retries}): Model '{self.model_name}' not found or access denied. {e.response}")
                else:
                    current_app.logger.error(f"Claude API status error {e.status_code} (attempt {attempt + 1}/{self.max_retries}): {e.response}")
                if attempt == self.max_retries - 1: raise
                time.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                current_app.logger.error(f"Claude API request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}", exc_info=True)
                if attempt == self.max_retries - 1: raise
                time.sleep(self.retry_delay)
        
        current_app.logger.error(f"Failed to generate dashboard from Claude after {self.max_retries} attempts for dataset_id: {dataset_id}.")
        raise Exception(f"Failed to generate dashboard from Claude after {self.max_retries} attempts.")

    def _sanitize_dashboard_html(self, html_content):
        if not html_content:
            current_app.logger.warning("Empty HTML content provided to _sanitize_dashboard_html.")
            return "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Error</title></head><body><h2>No dashboard content generated.</h2></body></html>"

        if not html_content.strip().lower().startswith("<!doctype html"):
            html_content = "<!DOCTYPE html>\n" + html_content
        
        if "<html" not in html_content.lower():
            html_content = html_content.replace("<!DOCTYPE html>", "<!DOCTYPE html>\n<html lang='en'>", 1)
            if "</html>" not in html_content.lower(): html_content += "\n</html>"
        
        head_start_idx = html_content.lower().find("<head>")
        head_end_idx = html_content.lower().find("</head>")

        if head_start_idx == -1: 
            html_tag_end = html_content.lower().find("<html>")
            insert_pos = html_tag_end + len("<html>") if html_tag_end != -1 else len("<!DOCTYPE html>")
            html_content = html_content[:insert_pos] + "\n<head><meta charset=\"UTF-8\"><title>Dashboard</title></head>\n" + html_content[insert_pos:]
            head_start_idx = html_content.lower().find("<head>") 
            head_end_idx = html_content.lower().find("</head>")


        if head_start_idx != -1 and "<meta charset" not in html_content[head_start_idx:head_end_idx if head_end_idx!=-1 else len(html_content)].lower():
            html_content = html_content[:head_start_idx+6] + "<meta charset=\"UTF-8\">\n" + html_content[head_start_idx+6:]
            head_end_idx = html_content.lower().find("</head>") 

        if "<body" not in html_content.lower():
            if head_end_idx != -1:
                html_content = html_content[:head_end_idx+7] + "\n<body>\n</body>" + html_content[head_end_idx+7:]
            elif "</html>" in html_content.lower():
                idx = html_content.lower().find("</html>")
                html_content = html_content[:idx] + "\n<body>\n</body>\n" + html_content[idx:]
            else:
                html_content += "\n<body>\n</body>"
        
        current_head_content = html_content[head_start_idx:head_end_idx if head_end_idx!=-1 else len(html_content)]

        if head_start_idx != -1 and '<meta name="viewport"' not in current_head_content.lower():
            viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            html_content = html_content[:head_start_idx+6] + viewport_meta + html_content[head_start_idx+6:]
            head_end_idx = html_content.lower().find("</head>")

        if head_start_idx != -1 and '<meta http-equiv="Content-Security-Policy"' not in current_head_content:
            # Adjusted CSP for broader CDN compatibility if needed, but keep it reasonably tight
            csp_tag = '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' \'unsafe-inline\' https://*.jsdelivr.net https://*.d3js.org https://cdnjs.cloudflare.com; style-src \'self\' \'unsafe-inline\' https://*.jsdelivr.net https://cdnjs.cloudflare.com; img-src \'self\' data: blob:; connect-src \'self\'; font-src \'self\' https://*.jsdelivr.net https://cdnjs.cloudflare.com;">\n'
            html_content = html_content[:head_start_idx+6] + csp_tag + html_content[head_start_idx+6:]
            head_end_idx = html_content.lower().find("</head>")
        
        libraries_to_check = [
            {"reference": "Chart", "cdn": "https://cdn.jsdelivr.net/npm/chart.js", "check_tag": "chart.js"},
            {"reference": "d3", "cdn": "https://d3js.org/d3.v7.min.js", "check_tag": "d3.v7.min.js"},
        ]
        
        if head_end_idx != -1: # Ensure head_end_idx is valid before using
            insertion_point = head_end_idx
            for lib in libraries_to_check:
                # Check if library is referenced (e.g. "new Chart" or "d3.select") AND script tag is missing
                if lib["reference"] in html_content and lib["check_tag"] not in html_content:
                    script_tag = f'<script src="{lib["cdn"]}"></script>\n'
                    html_content = html_content[:insertion_point] + script_tag + html_content[insertion_point:]
                    insertion_point += len(script_tag) 
        
        if "console.error('Dashboard error:'" not in html_content:
            error_handling_script = """
            <script>
            window.addEventListener('error', function(event) {
                console.error('Dashboard error:', event.message, 'at', event.filename, ':', event.lineno);
                var errorDisplay = document.getElementById('dynadashInternalErrorDisplay');
                if (!errorDisplay && document.body) {
                    errorDisplay = document.createElement('div');
                    errorDisplay.id = 'dynadashInternalErrorDisplay';
                    errorDisplay.style.cssText = 'position:fixed;top:5px;left:5px;right:5px;padding:10px;background:rgba(220,50,50,0.9);color:white;border-radius:4px;z-index:20000;font-family:sans-serif;font-size:14px;';
                    document.body.insertBefore(errorDisplay, document.body.firstChild);
                }
                if(errorDisplay) errorDisplay.textContent = 'Dashboard Error: ' + event.message + ' (in ' + (event.filename || 'inline script') + ':' + event.lineno + ')';
            });
            document.addEventListener('DOMContentLoaded', function() {
                if (typeof window.dynadashData === 'undefined' || window.dynadashData === null || (Array.isArray(window.dynadashData) && window.dynadashData.length === 0)) {
                    console.warn('window.dynadashData is not defined or is empty. Dashboard might not render correctly.');
                    var dataWarningDiv = document.getElementById('dynadashDataWarningDisplay');
                    if(!dataWarningDiv && document.body) {
                        dataWarningDiv = document.createElement('div');
                        dataWarningDiv.id = 'dynadashDataWarningDisplay';
                        dataWarningDiv.style.cssText = 'padding:10px;background:rgba(255,220,50,0.8);color:black;text-align:center;font-family:sans-serif;font-size:14px;';
                        dataWarningDiv.textContent = 'Notice: Data for this dashboard (window.dynadashData) was not loaded or is empty. Visualizations may not appear as expected.';
                        document.body.insertBefore(dataWarningDiv, document.body.firstChild);
                    }
                }
                setTimeout(function() {
                    if (typeof Chart !== 'undefined' && typeof window.dynadashData !== 'undefined') {
                        var canvases = document.querySelectorAll('canvas');
                        canvases.forEach(function(canvas) {
                            try {
                                var chartInstance = Chart.getChart(canvas); 
                                if (chartInstance) { chartInstance.update('none'); } 
                            } catch(e) { console.warn('Could not update chart on canvas ' + (canvas.id || '(no id)') + ':', e); }
                        });
                    }
                }, 1200);
            });
            </script>
            """
            body_end_idx = html_content.lower().rfind('</body>')
            if body_end_idx != -1:
                 html_content = html_content[:body_end_idx] + error_handling_script + html_content[body_end_idx:]
            else:
                 html_content += error_handling_script
        
        return html_content

    def analyze_dataset(self, dataset_id, use_thinking=True):
        self._initialize_client()
        dataset_metadata_and_content = self._read_dataset_file(dataset_id)
        
        prompt = f"""
        You are a data analysis expert. Analyze the following dataset and provide insights.
        
        Dataset Information:
        - Filename: {dataset_metadata_and_content['original_filename']}
        - Type: {dataset_metadata_and_content['file_type']}
        - Rows: {dataset_metadata_and_content['n_rows']}
        - Columns: {dataset_metadata_and_content['n_columns']}
        - Column Details: {json.dumps(dataset_metadata_and_content['column_info'])}
        
        Dataset Content (first 50 rows or 2000 characters):
        ```{dataset_metadata_and_content['file_type']}
        { (dataset_metadata_and_content['content'][:2000] + '...' if len(dataset_metadata_and_content['content']) > 2000 else dataset_metadata_and_content['content']) }
        ```
        
        Please provide:
        1. A concise summary of the dataset's nature and potential use.
        2. Key statistical insights for important columns.
        3. Interesting patterns, correlations, or anomalies you observe or hypothesize.
        4. Potential data quality issues.
        5. Recommendations for 3-5 specific visualizations.
        
        Format your response STRICTLY as JSON:
        {{
            "summary": "string",
            "key_statistics_insights": [{{ "column_name": "string", "insight": "string" }}],
            "patterns_correlations": [{{ "observation": "string", "implication_or_hypothesis": "string" }}],
            "data_quality_issues": [{{ "issue_type": "string", "description": "string", "affected_columns": ["string"] }}],
            "visualization_recommendations": [{{ "chart_type": "string", "description": "string", "relevant_columns": ["string"] }}]
        }}
        """
        
        current_app.logger.info(f"Requesting dataset analysis from Claude for dataset_id: {dataset_id}")

        for attempt in range(self.max_retries):
            try:
                params = {
                    "model": self.model_name,
                    "max_tokens": self.max_tokens_analysis,
                    "temperature": self.temperature_analysis,
                    "system": "You are a data analysis expert. Respond strictly with JSON.",
                    "messages": [{"role": "user", "content": prompt}]
                }

                response = self.client.messages.create(**params)
                
                analysis_text = None
                if response.content and isinstance(response.content, list):
                     for block in response.content:
                        if block.type == 'text': analysis_text = block.text; break
                
                if not analysis_text:
                    current_app.logger.error("No text content found in Claude's analysis response.")
                    raise ValueError("No text content found in the analysis response from Claude.")

                if analysis_text.strip().startswith("```json"):
                    analysis_text = analysis_text.split("```json",1)[-1]
                    if analysis_text.strip().endswith("```"): analysis_text = analysis_text.rsplit("```",1)[0]
                elif analysis_text.strip().startswith("```"):
                    analysis_text = analysis_text.strip()[3:-3] if analysis_text.strip().endswith("```") else analysis_text.strip()[3:]
                
                analysis_text = analysis_text.strip()
                analysis = json.loads(analysis_text)
                current_app.logger.info(f"Successfully received dataset analysis from Claude for dataset_id: {dataset_id}.")
                return analysis
            
            except json.JSONDecodeError as e:
                current_app.logger.error(f"Failed to parse JSON from Claude's analysis response (attempt {attempt + 1}/{self.max_retries}): {e}. Response: {analysis_text[:500]}", exc_info=True)
                if attempt == self.max_retries - 1: raise ValueError(f"Invalid JSON response from Claude after retries: {e}")
                time.sleep(self.retry_delay)
            except anthropic.APIError as e: 
                current_app.logger.error(f"Claude API Error for analysis (attempt {attempt + 1}/{self.max_retries}): {type(e).__name__} - {e}")
                if attempt == self.max_retries - 1: raise
                delay_multiplier = 2 if isinstance(e, anthropic.RateLimitError) else 1
                time.sleep(self.retry_delay * (attempt + 1) * delay_multiplier)
            except Exception as e:
                current_app.logger.error(f"Claude analysis request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}", exc_info=True)
                if attempt == self.max_retries - 1: raise
                time.sleep(self.retry_delay)
        
        current_app.logger.error(f"Failed to get dataset analysis from Claude after {self.max_retries} attempts for dataset_id: {dataset_id}.")
        raise Exception(f"Failed to get dataset analysis from Claude after {self.max_retries} attempts.")

    def _read_dataset_file(self, dataset_id):
        dataset = Dataset.query.get_or_404(dataset_id)
        file_path = dataset.file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        metadata = self._get_dataset_metadata(dataset_id)
        
        return {
            "content": file_content,
            "file_type": dataset.file_type,
            "original_filename": dataset.original_filename,
            "n_rows": dataset.n_rows,
            "n_columns": dataset.n_columns,
            "column_info": metadata['column_info']
        }