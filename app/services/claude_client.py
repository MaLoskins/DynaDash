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

        # Response Format
        Return ONLY the complete HTML code for the dashboard, with no explanation or markdown formatting.
        Your response should begin with <!DOCTYPE html> and be ready to view in a browser.
        """
        
        return prompt.strip()
    
    def generate_dashboard(self, dataset_id, title, description=""):
        """Generate a complete dashboard visualization for a dataset using Claude."""
        self._initialize_client()
        
        # Create the prompt
        prompt = self._create_dashboard_prompt(dataset_id, title, description)
        
        # Send the request to Claude
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=12000,  # Increased token limit for larger responses
                    temperature=0.3,
                    system="You are a data visualization expert that creates beautiful, interactive dashboards using HTML, CSS, and JavaScript. You only respond with complete HTML code for a dashboard, with no explanations or Markdown.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extract the dashboard HTML from the response
                dashboard_html = response.content[0].text
                
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
    
    # Keep the legacy method for backward compatibility if needed
    def generate_visualization(self, dataset_id, title):
        """Legacy method - now redirects to generate_dashboard."""
        current_app.logger.info("Legacy generate_visualization method called - redirecting to generate_dashboard")
        return self.generate_dashboard(dataset_id, title)
    
    # Keep this method for backward compatibility
    def analyze_dataset(self, dataset_id):
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
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=0.2,
                    system="You are a data analysis expert that provides insights and recommendations. You respond with JSON only.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extract the analysis from the response
                analysis_text = response.content[0].text
                
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