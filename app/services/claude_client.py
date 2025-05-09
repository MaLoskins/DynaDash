import os
import json
import time
import base64
import anthropic
from flask import current_app
import pandas as pd
from ..models import Dataset, db

class ClaudeClient:
    """Service for interacting with the Anthropic Claude API."""
    
    def __init__(self):
        """Initialize the Claude client."""
        self.client = None
        self.model = "claude-3-7-sonnet-20250219"  # Updated to Claude 3.7
    
    def _initialize_client(self):
        """Initialize the Anthropic client with API key."""
        if not self.client:
            api_key = current_app.config.get('ANTHROPIC_API_KEY')
            if not api_key:
                raise ValueError("Anthropic API key is not set")
            
            try:
                # For Anthropic SDK v0.7.0, we need to use Anthropic class
                current_app.logger.info(f"Initializing Anthropic client with version: {anthropic.__version__}")
                
                # Simple initialization for v0.7.0+
                if hasattr(anthropic, 'Anthropic'):
                    # In newer versions, Anthropic() takes only specific parameters
                    # No 'proxies' parameter is supported - proxy settings should be configured
                    # through HTTP_PROXY/HTTPS_PROXY environment variables instead
                    
                    # Temporarily set environment variable for initialization
                    original_api_key = os.environ.get('ANTHROPIC_API_KEY')
                    os.environ['ANTHROPIC_API_KEY'] = api_key
                    try:
                        # Initialize with only supported parameters, no 'proxies'
                        self.client = anthropic.Anthropic()
                    finally:
                        # Restore original environment variable
                        if original_api_key:
                            os.environ['ANTHROPIC_API_KEY'] = original_api_key
                        else:
                            os.environ.pop('ANTHROPIC_API_KEY', None)
                # Fallback for older versions that use Client class
                elif hasattr(anthropic, 'Client'):
                    # Only pass the api_key parameter, not proxies
                    self.client = anthropic.Client(api_key=api_key)
                else:
                    raise TypeError("Could not find appropriate Anthropic client class")
                    
            except Exception as e:
                current_app.logger.error(f"Error initializing Anthropic client: {str(e)}")
                raise
    
    def _read_dataset_file(self, dataset_id):
        """Read the entire dataset file content."""
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Read the dataset file
        file_path = dataset.file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        # Read the file content based on file type
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        # Get column information and additional statistics
        try:
            if dataset.file_type.lower() == 'csv':
                df = pd.read_csv(file_path)
            elif dataset.file_type.lower() == 'json':
                df = pd.read_json(file_path)
            else:
                raise ValueError(f"Unsupported file type: {dataset.file_type}")
                
            # Get column data types and basic stats
            column_info = {}
            for col in df.columns:
                col_type = str(df[col].dtype)
                
                # Add additional info based on data type
                if pd.api.types.is_numeric_dtype(df[col]):
                    stats = {
                        "type": col_type,
                        "min": float(df[col].min()) if not pd.isna(df[col].min()) else None,
                        "max": float(df[col].max()) if not pd.isna(df[col].max()) else None,
                        "mean": float(df[col].mean()) if not pd.isna(df[col].mean()) else None,
                        "median": float(df[col].median()) if not pd.isna(df[col].median()) else None
                    }
                elif pd.api.types.is_datetime64_dtype(df[col]):
                    stats = {
                        "type": "datetime",
                        "min": df[col].min().strftime('%Y-%m-%d') if not pd.isna(df[col].min()) else None,
                        "max": df[col].max().strftime('%Y-%m-%d') if not pd.isna(df[col].max()) else None
                    }
                else:
                    unique_values = df[col].nunique()
                    stats = {
                        "type": col_type,
                        "unique_values": int(unique_values),
                        "most_common": df[col].value_counts().head(3).to_dict() if unique_values < 100 else None
                    }
                
                column_info[col] = stats
                
        except Exception as e:
            current_app.logger.warning(f"Could not generate column statistics: {str(e)}")
            column_info = {}
        
        return {
            "content": file_content,
            "file_type": dataset.file_type,
            "original_filename": dataset.original_filename,
            "n_rows": dataset.n_rows,
            "n_columns": dataset.n_columns,
            "column_info": column_info
        }

    def _create_dashboard_prompt(self, dataset_id, title, description=""):
        """Create a prompt for generating a complete dashboard visualization."""
        dataset_info = self._read_dataset_file(dataset_id)
        
        column_info_str = json.dumps(dataset_info["column_info"], indent=2)
        
        prompt = f"""
        You are a data visualization expert. Create a complete, interactive dashboard for the following dataset using HTML, CSS, and JavaScript.

        # Dashboard Information
        Title: {title}
        Description: {description}

        # Dataset Information
        Filename: {dataset_info['original_filename']}
        Type: {dataset_info['file_type']}
        Rows: {dataset_info['n_rows']}
        Columns: {dataset_info['n_columns']}
        
        # Column Information
        {column_info_str}
        
        # Dataset Content
        ```{dataset_info['file_type']}
        {dataset_info['content']}
        ```

        # Requirements
        1. Create a complete, self-contained HTML file with embedded CSS and JavaScript that implements a full interactive dashboard.
        2. Include multiple visualizations (at least 3-5 different charts) that provide complementary views of the data.
        3. Add interactive elements such as filters, dropdowns, or date selectors that allow users to explore the data.
        4. Include a summary section with key insights, trends, and statistics derived from the data.
        5. Structure the dashboard with clear sections, headers, and navigation.
        6. Use appropriate chart types based on the data variables and relationships (bar charts, line charts, scatter plots, heatmaps, etc.).
        7. Ensure all visualizations have proper titles, labels, legends, and tooltips.
        8. The dashboard should be responsive and visually appealing with a professional color scheme.
        9. Include data tables or summary statistics where appropriate.
        10. Use modern JavaScript libraries like Chart.js, D3.js, or other popular visualization libraries.
        11. All JavaScript, CSS, and HTML must be in a single file.
        12. Ensure all charts and visualizations load and initialize properly when the page loads.
        13. Handle potential data issues gracefully (missing values, outliers, etc.).
        14. IMPORTANT: Include complete JavaScript code that creates charts using 'new Chart(ctx, config)' for each canvas element. Never omit chart initialization code.
        15. IMPORTANT: Use D3.js or Chart.js to parse and process the CSV data for the visualization.
        16. IMPORTANT: Make sure to properly parse the CSV data and convert it into a format suitable for the charts.
        17. IMPORTANT: Each chart or visualization must have corresponding JavaScript that FULLY initializes it.

        # Response Format
        Return ONLY the complete HTML code for the dashboard, with no explanation or markdown formatting.
        Your response should begin with <!DOCTYPE html> and be ready to view in a browser.
        """
        
        return prompt.strip()
    
    def generate_dashboard(self, dataset_id, title, description="", use_thinking=False):
        """Generate a complete dashboard visualization for a dataset using Claude."""
        self._initialize_client()
        
        # Create the prompt
        prompt = self._create_dashboard_prompt(dataset_id, title, description)
        
        # Send the request to Claude
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Create the API request parameters
                params = {
                    "model": self.model,
                    "max_tokens": 12000,  # Increased token limit for larger responses
                    "temperature": 1,
                    "system": "You are a data visualization expert that creates beautiful, interactive dashboards using HTML, CSS, and JavaScript. You only respond with complete HTML code for a dashboard, with no explanations or Markdown.",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
                
                # Add thinking parameter if enabled
                if use_thinking:
                    params["thinking"] = {"type": "enabled", "budget_tokens": 4000}
                
                response = self.client.messages.create(**params)
                
                # Extract the dashboard HTML from the response
                dashboard_html = None
                for block in response.content:
                    if hasattr(block, 'text'):
                        dashboard_html = block.text
                        break
                        
                if dashboard_html is None:
                    raise ValueError("No text content found in the response")
                
                # Clean up the code (remove markdown code blocks if present)
                if dashboard_html.startswith("```html"):
                    # Extract code from markdown code blocks
                    lines = dashboard_html.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].startswith("```"):
                        lines = lines[:-1]
                    dashboard_html = "\n".join(lines)
                elif dashboard_html.startswith("```"):
                    # Generic code block without language specifier
                    dashboard_html = dashboard_html.replace("```", "").strip()
                
                # Check if the dashboard has proper chart initialization code
                if "const csvData =" in dashboard_html and "new Chart" not in dashboard_html:
                    current_app.logger.warning("Generated dashboard is missing chart initialization, trying again with a stronger prompt")
                    if attempt < max_retries - 1:
                        # Add a more specific chart initialization requirement for next attempt
                        prompt += "\n\nIMPORTANT: Make sure to include complete JavaScript code that processes the CSV data and initializes Chart.js charts using 'new Chart(ctx, config)' syntax. Your HTML must include proper chart initialization code."
                        continue
                
                # Systematically sanitize the HTML/JS output
                dashboard_html = self._sanitize_dashboard_html(dashboard_html)
                
                # Log the first 500 characters of the response for debugging
                current_app.logger.debug(f"Dashboard HTML (first 500 chars): {dashboard_html[:500]}...")
                
                return dashboard_html
                    
            except Exception as e:
                if attempt < max_retries - 1:
                    current_app.logger.warning(f"Claude API request failed, retrying in {retry_delay} seconds: {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    current_app.logger.error(f"Claude API request failed after {max_retries} attempts: {str(e)}")
                    raise
    
    def _sanitize_dashboard_html(self, html_content):
        """
        Systematically sanitize the HTML/JavaScript to fix common issues with Claude-generated code.
        This function handles corruptions and makes the dashboard more robust.
        """
        if not html_content:
            return html_content
        
        # Check if the dashboard HTML is incomplete (missing charts initialization)
        if "const csvData =" in html_content and (
            html_content.strip().endswith("</script>") or 
            "new Chart" not in html_content or
            html_content.count("canvas") > html_content.count("new Chart")
        ):
            current_app.logger.warning("Detected incomplete chart initialization in dashboard HTML")
            
            # Add fallback chart initialization if necessary
            if "</body>" in html_content:
                fallback_charts = """
                <script>
                // Fallback chart initialization
                document.addEventListener('DOMContentLoaded', function() {
                    console.log("Adding fallback chart initialization");
                    
                    // Parse CSV data if it exists but charts weren't created
                    try {
                        // Process any canvas elements that don't have charts
                        const canvases = document.querySelectorAll('canvas');
                        canvases.forEach(function(canvas) {
                            if (!canvas.chart && canvas.id) {
                                console.log("Creating fallback chart for:", canvas.id);
                                
                                // Get chart type from canvas ID
                                const isBarChart = canvas.id.includes('bar') || canvas.id.includes('distribution');
                                const isLineChart = canvas.id.includes('timeline') || canvas.id.includes('time');
                                const isScatterChart = canvas.id.includes('scatter');
                                const isPieChart = canvas.id.includes('pie') || canvas.id.includes('topic');
                                
                                // Create simple placeholder chart
                                let chartType = 'bar';
                                if (isLineChart) chartType = 'line';
                                if (isScatterChart) chartType = 'scatter';
                                if (isPieChart) chartType = 'pie';
                                
                                // Create simple data
                                let data = {
                                    labels: ['Category 1', 'Category 2', 'Category 3', 'Category 4'],
                                    datasets: [{
                                        label: 'Sample Data',
                                        data: [12, 19, 3, 5],
                                        backgroundColor: [
                                            'rgba(75, 192, 192, 0.5)',
                                            'rgba(54, 162, 235, 0.5)',
                                            'rgba(255, 206, 86, 0.5)',
                                            'rgba(255, 99, 132, 0.5)'
                                        ],
                                        borderColor: [
                                            'rgba(75, 192, 192, 1)',
                                            'rgba(54, 162, 235, 1)',
                                            'rgba(255, 206, 86, 1)',
                                            'rgba(255, 99, 132, 1)'
                                        ],
                                        borderWidth: 1
                                    }]
                                };
                                
                                // Configure chart
                                const config = {
                                    type: chartType,
                                    data: data,
                                    options: {
                                        responsive: true,
                                        maintainAspectRatio: false,
                                        plugins: {
                                            title: {
                                                display: true,
                                                text: 'Data Visualization',
                                                font: { size: 16 }
                                            },
                                            legend: {
                                                position: 'top'
                                            },
                                            tooltip: {
                                                enabled: true
                                            }
                                        }
                                    }
                                };
                                
                                // Create chart
                                if (typeof Chart !== 'undefined') {
                                    canvas.chart = new Chart(canvas, config);
                                }
                            }
                        });
                    } catch (err) {
                        console.error("Error creating fallback charts:", err);
                    }
                });
                </script>
                """
                html_content = html_content.replace('</body>', fallback_charts + '</body>')
        
        # Fix corrupted patterns - these appear consistently in thinking-mode generated HTML
        corrupted_patterns = {
            "cdata-disabled-event": "",
            "cdata-disabled": "",
            "mentidata-disabled-event": "mentions",
            "chartCdata-disabled-event": "chartContainers",
            "textCdata-disabled-event": "textContent",
            "containerCdata": "container",
        }
        
        for pattern, replacement in corrupted_patterns.items():
            html_content = html_content.replace(pattern, replacement)
        
        # Ensure all required JavaScript libraries are present
        libraries_to_check = [
            {
                "reference": "Chart",
                "src": "https://cdn.jsdelivr.net/npm/chart.js"
            },
            {
                "reference": "d3",
                "src": "https://d3js.org/d3.v7.min.js"
            },
            {
                "reference": "dayjs",
                "src": "https://cdn.jsdelivr.net/npm/dayjs@1.10.7/dayjs.min.js"
            },
            {
                "reference": "lodash",
                "src": "https://cdn.jsdelivr.net/npm/lodash@4.17.21/lodash.min.js"
            }
        ]
        
        for lib in libraries_to_check:
            if lib["reference"] in html_content and lib["src"] not in html_content:
                script_tag = f'<script src="{lib["src"]}"></script>'
                # Insert before closing head tag if it exists
                if '</head>' in html_content:
                    html_content = html_content.replace('</head>', f'{script_tag}\n</head>')
                # Otherwise insert at the beginning of the document
                else:
                    html_content = f'{script_tag}\n{html_content}'
        
        # Add safety checks to JavaScript to prevent errors from undefined objects
        js_safety_patterns = [
            ("Chart.defaults", "Chart && Chart.defaults"),
            ("d3.select", "d3 && d3.select"),
            ("dayjs(", "dayjs && dayjs("),
            ("_.map", "_ && _.map")
        ]
        
        for pattern, replacement in js_safety_patterns:
            html_content = html_content.replace(pattern, replacement)
        
        # Find and fix any broken event listeners
        broken_event_patterns = [
            # Fix broken event listeners
            ("document.addEvent", "document.addEventListener"),
            ("window.addEvent", "window.addEventListener")
        ]
        
        for pattern, replacement in broken_event_patterns:
            html_content = html_content.replace(pattern, replacement)
        
        # Ensure proper HTML structure
        if not html_content.strip().startswith("<!DOCTYPE"):
            html_content = "<!DOCTYPE html>\n" + html_content
        
        if "<html" not in html_content:
            html_content = html_content.replace("<!DOCTYPE html>", "<!DOCTYPE html>\n<html>")
            if "</html>" not in html_content:
                html_content += "\n</html>"
        
        if "<head>" not in html_content:
            html_content = html_content.replace("<html>", "<html>\n<head>\n</head>")
        
        if "<body>" not in html_content:
            if "</head>" in html_content:
                html_content = html_content.replace("</head>", "</head>\n<body>")
                if "</body>" not in html_content and "</html>" in html_content:
                    html_content = html_content.replace("</html>", "</body>\n</html>")
        
        # Add a basic error handling mechanism for the dashboard
        # Make sure we don't add duplicate error handlers
        if "Dashboard error:" not in html_content or html_content.count("Dashboard error:") < 2:
            error_handling_script = """
        <script>
        // Add basic error handling to prevent dashboard from getting stuck
        window.addEventListener('error', function(e) {
            console.error('Dashboard error:', e.message, e.filename, e.lineno);
            
            // If the page is still showing loading after errors, try to hide the loading indicator
            setTimeout(function() {
                var loadingElements = document.querySelectorAll('.loading, #loading, [id*="loading"], [class*="loading"]');
                loadingElements.forEach(function(el) {
                    el.style.display = 'none';
                });
                
                // Try to fix any broken charts
                if (typeof Chart !== 'undefined') {
                    var canvases = document.querySelectorAll('canvas');
                    canvases.forEach(function(canvas) {
                        if (!canvas.chart && canvas.id) {
                            try {
                                console.log("Attempting to create chart for:", canvas.id);
                                const ctx = canvas.getContext('2d');
                                if (ctx) {
                                    canvas.chart = new Chart(ctx, {
                                        type: 'bar',
                                        data: {
                                            labels: ['Sample'],
                                            datasets: [{
                                                label: 'Data',
                                                data: [5],
                                                backgroundColor: 'rgba(75, 192, 192, 0.5)'
                                            }]
                                        },
                                        options: {
                                            responsive: true,
                                            plugins: {
                                                title: {
                                                    display: true,
                                                    text: 'Data Preview'
                                                }
                                            }
                                        }
                                    });
                                }
                            } catch (err) {
                                console.warn('Could not create fallback chart:', err);
                            }
                        }
                    });
                }
            }, 2000);
        });

        // Ensure all charts are properly initialized
        document.addEventListener('DOMContentLoaded', function() {
            console.log("DOM loaded - initializing any uninitialized charts");
            
            // Force charts to render after a delay
            setTimeout(function() {
                if (typeof Chart !== 'undefined') {
                    // Force all canvases to update
                    var canvases = document.querySelectorAll('canvas');
                    canvases.forEach(function(canvas) {
                        if (canvas.chart) {
                            try {
                                canvas.chart.update();
                            } catch (e) {
                                console.warn('Could not update chart:', e);
                            }
                        } else if (canvas.id) {
                            console.log("Found canvas without chart:", canvas.id);
                        }
                    });
                }
            }, 1000);
        });
        </script>
        """
            
            # Add the error handling script before the closing body tag
            if "</body>" in html_content:
                html_content = html_content.replace("</body>", error_handling_script + "\n</body>")
            else:
                # If there's no body tag, add it at the end
                html_content += "\n" + error_handling_script
        
        # Fix any truncated CSV data
        if "const csvData =" in html_content and not ";</script>" in html_content:
            current_app.logger.warning("Detected truncated CSV data in dashboard HTML")
            fix_script = """
        <script>
        // Fix for truncated CSV data
        document.addEventListener('DOMContentLoaded', function() {
            console.log("Handling potentially truncated CSV data");
            // Check all scripts for truncated CSV data
            const scripts = document.querySelectorAll('script');
            scripts.forEach(function(script) {
                const content = script.textContent || script.innerText;
                if (content && content.includes('const csvData =') && !content.includes(';</script>')) {
                    console.warn("Detected truncated CSV data, attempting to fix");
                    // This script has truncated CSV, let's fix variable declaration
                    try {
                        // Try to extract what we have and make it valid
                        const csvLines = content.split('\\n').filter(line => line.trim().length > 0);
                        if (csvLines.length > 1) {
                            // Create a valid array of records from available data
                            const headers = csvLines[0].split(',');
                            const validData = [];
                            
                            for (let i = 1; i < csvLines.length; i++) {
                                const values = csvLines[i].split(',');
                                if (values.length >= headers.length) {
                                    const record = {};
                                    headers.forEach((header, index) => {
                                        record[header] = values[index];
                                    });
                                    validData.push(record);
                                }
                            }
                            
                            // Make global variable available with the fixed data
                            window.fixedCsvData = validData;
                            console.log("Created fixedCsvData with", validData.length, "records");
                        }
                    } catch (err) {
                        console.error("Could not fix truncated CSV:", err);
                    }
                }
            });
        });
        </script>
        """
            if "</body>" in html_content:
                html_content = html_content.replace("</body>", fix_script + "\n</body>")
        
        return html_content
            
      
    # Keep the legacy method for backward compatibility if needed
    def generate_visualization(self, dataset_id, title):
        """Legacy method - now redirects to generate_dashboard."""
        current_app.logger.info("Legacy generate_visualization method called - redirecting to generate_dashboard")
        return self.generate_dashboard(dataset_id, title)
    
    def analyze_dataset(self, dataset_id, use_thinking=True):
        """Analyze a dataset and provide insights."""
        self._initialize_client()
        
        # Get dataset information
        dataset_info = self._read_dataset_file(dataset_id)
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Create the prompt
        prompt = f"""
        You are a data analysis expert. Analyze the following dataset and provide insights.
        
        Dataset Information:
        - Filename: {dataset_info['original_filename']}
        - Type: {dataset_info['file_type']}
        - Rows: {dataset_info['n_rows']}
        - Columns: {dataset_info['n_columns']}
        
        Dataset Content:
        ```{dataset_info['file_type']}
        {dataset_info['content']}
        ```
        
        Please provide:
        1. A summary of the dataset
        2. Key statistics for each column
        3. Interesting patterns or correlations
        4. Potential issues with the data (missing values, outliers, etc.)
        5. Recommendations for visualizations
        
        Format your response as JSON with the following structure:
        {{
            "summary": "...",
            "statistics": {{...}},
            "patterns": [...],
            "issues": [...],
            "visualization_recommendations": [...]
        }}
        """
        
        # Send the request to Claude
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                # Create the API request parameters
                params = {
                    "model": self.model,
                    "max_tokens": 4000,
                    "temperature": 1,
                    "system": "You are a data analysis expert that provides insights and recommendations. You respond with JSON only.",
                    "messages": [
                        {"role": "user", "content": prompt}
                    ]
                }
                
                # Add thinking parameter if enabled
                if use_thinking:
                    params["thinking"] = {"type": "enabled", "budget_tokens": 4000}
                
                response = self.client.messages.create(**params)
                
                # Extract the analysis from the response
                # Find the text block in the content (when thinking is enabled, there will be both thinking and text blocks)
                analysis_text = None
                for block in response.content:
                    if hasattr(block, 'text'):
                        analysis_text = block.text
                        break
                        
                if analysis_text is None:
                    raise ValueError("No text content found in the response")
                
                # Clean up the response (remove markdown code blocks if present)
                if analysis_text.startswith("```json"):
                    analysis_text = analysis_text.replace("```json", "").replace("```", "").strip()
                elif analysis_text.startswith("```"):
                    analysis_text = analysis_text.replace("```", "").strip()
                
                # Parse the JSON response
                analysis = json.loads(analysis_text)
                
                return analysis
            
            except Exception as e:
                if attempt < max_retries - 1:
                    current_app.logger.warning(f"Claude API request failed, retrying in {retry_delay} seconds: {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    current_app.logger.error(f"Claude API request failed after {max_retries} attempts: {str(e)}")
                    raise