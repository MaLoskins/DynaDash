import os
import json
import time
import anthropic
from flask import current_app
import pandas as pd
from ..models import Dataset, db

class ClaudeClient:
    """Service for interacting with the Anthropic Claude API."""
    
    def __init__(self):
        """Initialize the Claude client."""
        self.client = None
        self.model = "claude-3-opus-20240229"  # Default model
    
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
    
    def _get_dataset_statistics(self, dataset_id, max_rows=100):
        """Get statistics of the dataset for visualization."""
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Read the dataset file
        file_path = dataset.file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        # Read the dataset based on file type
        if dataset.file_type.lower() == 'csv':
            df = pd.read_csv(file_path, nrows=max_rows)
        elif dataset.file_type.lower() == 'json':
            df = pd.read_json(file_path)
            if len(df) > max_rows:
                df = df.head(max_rows)
        else:
            raise ValueError(f"Unsupported file type: {dataset.file_type}")
        sampled_rows = len(df)

        # Generate statistics
        stats = {
        "dataset_info": {
            "name":        dataset.original_filename,
            "rows":        dataset.n_rows,          # full table (already present)
            "columns":     dataset.n_columns,
            "file_type":   dataset.file_type,
            "sampled_rows": sampled_rows,           # NEW: prompt-level input size
            "sampled_cells": int(sampled_rows * df.shape[1])  # optional extra
        },
        "column_stats": {},
        "grouped_info": {},        # NEW: lives alongside column_stats
        "sample_data": {}
    }
        
        # Add column statistics
        for col in df.columns:
            col_stats = {}
            
            # Get data type
            dtype = str(df[col].dtype)
            col_stats["type"] = dtype
            
            # For numeric columns
            if pd.api.types.is_numeric_dtype(df[col]):
                col_stats["min"] = float(df[col].min()) if not pd.isna(df[col].min()) else None
                col_stats["max"] = float(df[col].max()) if not pd.isna(df[col].max()) else None
                col_stats["mean"] = float(df[col].mean()) if not pd.isna(df[col].mean()) else None
                col_stats["median"] = float(df[col].median()) if not pd.isna(df[col].median()) else None
                col_stats["std"] = float(df[col].std()) if not pd.isna(df[col].std()) else None
                
            # For categorical/object columns
            elif pd.api.types.is_object_dtype(df[col]) or pd.api.types.is_categorical_dtype(df[col]):
                # Get value counts for top 5 categories
                value_counts = df[col].value_counts().head(5).to_dict()
                col_stats["top_values"] = {str(k): int(v) for k, v in value_counts.items()}
                col_stats["unique_count"] = int(df[col].nunique())
            
            # For datetime columns
            elif pd.api.types.is_datetime64_dtype(df[col]):
                col_stats["min"] = df[col].min().strftime('%Y-%m-%d') if not pd.isna(df[col].min()) else None
                col_stats["max"] = df[col].max().strftime('%Y-%m-%d') if not pd.isna(df[col].max()) else None
            
            # Add missing value count
            col_stats["missing_count"] = int(df[col].isna().sum())
            col_stats["missing_percentage"] = float(df[col].isna().mean() * 100)
            
            stats["column_stats"][col] = col_stats

            # NEW: detect "grouping" columns  (re-used values < total rows)
            nunique = df[col].nunique(dropna=True)
            if nunique < sampled_rows:                      # repeats exist → groups
                top_groups = (
                    df[col]
                    .value_counts(dropna=True)
                    .head(5)
                    .to_dict()
                )
                stats["grouped_info"][col] = {
                    "unique_values": int(nunique),
                    "largest_groups": {str(k): int(v) for k, v in top_groups.items()}
                }
        
        # Add a small sample of data (first 5 rows)
        sample = df.head(5)
        for col in sample.columns:
            stats["sample_data"][col] = sample[col].tolist()
        
        # Convert to JSON for the prompt
        return json.dumps(stats)
    
    def _create_visualization_prompt(self, dataset_id, title):
        """Create a prompt for generating a visualization."""
        dataset_stats = self._get_dataset_statistics(dataset_id)
        
        prompt = r"""
        You are a data visualization expert. Create a visualization for the following dataset statistics using HTML, CSS, and JavaScript.

        Dataset Statistics: """ + dataset_stats + r"""

        Title: """ + title + r"""

        Requirements:
        1. Choose the most appropriate visualization type for the dataset. Do NOT ask the user for a chart type; select the type yourself based on the data characteristics.
        2. Use Chart.js for the visualization (preferred) or D3.js if more appropriate
        3. Make the visualization logically based on the data types of the sample dataset
        4. Use appropriate colors and styling
        5. Include proper labels and legends
        6. Ensure that the visualisation x and y axis is ordered logically (where applicable).
        7. Return ONLY the HTML/CSS/JavaScript code for the visualization, with no explanation or markdown
        8. The code should be self-contained and ready to be inserted into a webpage
        9. CRITICAL: Use a div with id="visualization-container" as the container for the visualization
        10. IMPORTANT: Return ONLY the <div id="visualization-container"> element and its contents
        11. Do not include <html>, <head>, <body> tags or any external script loading
        12. Include all necessary JavaScript libraries as CDN links inside the visualization container
        13. Make sure to properly initialize and render the chart
        14. Ensure all script tags are placed in the correct order - libraries first, then visualization code

        Example format of your response:
        <div id="visualization-container">
         <!-- Chart.js (core) --> <script src="https://cdn.jsdelivr.net/npm/chart.js@4.4.3"></script>
          <canvas id="myChart"></canvas>
          <script>
            const ctx = document.getElementById('myChart').getContext('2d');
            const chart = new Chart(ctx, {
              type: 'bar',
              data: {
                labels: ['Red', 'Blue', 'Yellow', 'Green', 'Purple', 'Orange'],
                datasets: []
              }
            });
          </script>
        </div>

        The visualization should be informative and help users understand the data better.
        """
        
        return prompt.strip()
    
    def generate_visualization(self, dataset_id, title):
        """Generate a visualization for a dataset using Claude."""
        self._initialize_client()
        
        # Create the prompt
        prompt = self._create_visualization_prompt(dataset_id, title)
        
        # Send the request to Claude
        max_retries = 3
        retry_delay = 2  # seconds
        
        for attempt in range(max_retries):
            try:
                response = self.client.messages.create(
                    model=self.model,
                    max_tokens=4000,
                    temperature=0.2,
                    system="You are a data visualization expert that creates beautiful, interactive <div> visualizations using HTML, CSS, and JavaScript. You only respond with code, no explanations.",
                    messages=[
                        {"role": "user", "content": prompt}
                    ]
                )
                
                # Extract the visualization code from the response
                visualization_code = response.content[0].text
                
                # Clean up the code (remove markdown code blocks if present)
                if visualization_code.startswith("```"):
                    # Extract code from markdown code blocks
                    lines = visualization_code.split("\n")
                    if lines[0].startswith("```"):
                        lines = lines[1:]
                    if lines[-1].startswith("```"):
                        lines = lines[:-1]
                    visualization_code = "\n".join(lines)
                
                # Log the original visualization code for debugging
                current_app.logger.debug(f"Original visualization code from Claude: {visualization_code}")
                
                # Extract only the visualization container div
                import re
                
                # Try different regex patterns to find the visualization container
                # Pattern 1: Standard div with id
                div_pattern1 = re.compile(r'<div\s+id=["\']visualization-container["\'][^>]*>.*?</div>', re.DOTALL)
                # Pattern 2: More flexible pattern that might catch variations
                div_pattern2 = re.compile(r'<div[^>]*id=["\']visualization-container["\'][^>]*>.*?</div>', re.DOTALL)
                # Pattern 3: Even more flexible, might catch malformed HTML
                div_pattern3 = re.compile(r'<div[^>]*id=["\']visualization-container["\'][^>]*>[\s\S]*?</div>', re.DOTALL)
                
                # Try each pattern in order
                match = div_pattern1.search(visualization_code)
                if match:
                    result = match.group(0)
                    current_app.logger.debug(f"Found visualization container with pattern 1: {result}")
                    return result
                
                match = div_pattern2.search(visualization_code)
                if match:
                    result = match.group(0)
                    current_app.logger.debug(f"Found visualization container with pattern 2: {result}")
                    return result
                
                match = div_pattern3.search(visualization_code)
                if match:
                    result = match.group(0)
                    current_app.logger.debug(f"Found visualization container with pattern 3: {result}")
                    return result
                
                # If no match found with any pattern, create a container div and wrap the code
                current_app.logger.warning("Visualization container div not found in Claude response, creating wrapper")
                
                # NEW: Improved wrapping logic to handle scripts properly
                if "<script" in visualization_code:
                    # Extract all scripts and other HTML content
                    script_pattern = re.compile(r'<script.*?</script>', re.DOTALL)
                    script_tags = script_pattern.findall(visualization_code)
                    
                    # Separate library scripts (CDN links) from code scripts
                    lib_scripts = []
                    code_scripts = []
                    
                    for script in script_tags:
                        if "cdn" in script.lower() or "https://" in script:
                            lib_scripts.append(script)
                        else:
                            code_scripts.append(script)
                    
                    # Remove script tags from the original content
                    content_without_scripts = script_pattern.sub('', visualization_code)
                    
                    # Extract any div elements that might contain the chart
                    div_pattern = re.compile(r'<div.*?</div>', re.DOTALL)
                    div_elements = div_pattern.findall(content_without_scripts)
                    
                    # Construct the final HTML in the proper order
                    wrapped_code = '<div id="visualization-container">\n'
                    
                    # Add library scripts first
                    for script in lib_scripts:
                        wrapped_code += script + '\n'
                    
                    # Add the HTML content (divs, canvas, etc.)
                    if div_elements:
                        for div in div_elements:
                            wrapped_code += div + '\n'
                    else:
                        # If no divs found, add generic chart container
                        wrapped_code += '<div style="width: 100%; height: 400px;">\n'
                        wrapped_code += '  <canvas id="chart"></canvas>\n'
                        wrapped_code += '</div>\n'
                    
                    # Add canvas elements if missing but referenced in scripts
                    if 'getElementById("chart")' in str(code_scripts) and '<canvas id="chart"' not in wrapped_code:
                        wrapped_code += '<canvas id="chart"></canvas>\n'
                        
                    # Add code scripts last
                    for script in code_scripts:
                        wrapped_code += script + '\n'
                    
                    wrapped_code += '</div>'
                else:
                    # If no scripts found, just wrap the content
                    wrapped_code = f'<div id="visualization-container">{visualization_code}</div>'
                
                current_app.logger.debug(f"Wrapped visualization code: {wrapped_code}")
                return wrapped_code
            
            except Exception as e:
                if attempt < max_retries - 1:
                    current_app.logger.warning(f"Claude API request failed, retrying in {retry_delay} seconds: {str(e)}")
                    time.sleep(retry_delay)
                    retry_delay *= 2  # Exponential backoff
                else:
                    current_app.logger.error(f"Claude API request failed after {max_retries} attempts: {str(e)}")
                    raise
    
    def analyze_dataset(self, dataset_id):
        """Analyze a dataset and provide insights."""
        self._initialize_client()
        
        # Get dataset statistics
        dataset_stats = self._get_dataset_statistics(dataset_id)
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Create the prompt
        prompt = f"""
        You are a data analysis expert. Analyze the following dataset statistics and provide insights.
        
        Dataset Statistics: {dataset_stats}
        
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