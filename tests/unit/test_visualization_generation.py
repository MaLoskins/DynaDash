import unittest
from unittest.mock import patch, MagicMock, ANY
import os
import sys
import json
import anthropic
from flask import Flask

# Add the app directory to the path so we can import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.services.claude_client import ClaudeClient
from app.models import Dataset, db

class TestVisualizationGeneration(unittest.TestCase):
    """Tests for the visualization generation functionality."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config['ANTHROPIC_API_KEY'] = 'test_api_key'
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = ClaudeClient()
        
        # Mock the dataset
        self.mock_dataset = MagicMock(spec=Dataset)
        self.mock_dataset.id = 1
        self.mock_dataset.file_path = 'test_path.csv'
        self.mock_dataset.file_type = 'csv'
        self.mock_dataset.original_filename = 'test_dataset.csv'
        self.mock_dataset.n_rows = 100
        self.mock_dataset.n_columns = 5
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.app_context.pop()
    
    @patch('app.services.claude_client.Dataset')
    @patch('app.services.claude_client.pd')
    @patch('app.services.claude_client.os.path')
    @patch('app.services.claude_client.anthropic', spec=anthropic)
    def test_generate_visualization(self, mock_anthropic, mock_os_path, mock_pd, mock_dataset):
        """Test the generation of a visualization."""
        # Configure mocks
        mock_anthropic_instance = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_anthropic_instance
        mock_anthropic.__version__ = '0.7.0'
        
        # Mock the dataset query
        mock_dataset.query.get_or_404.return_value = self.mock_dataset
        
        # Mock os.path.exists to return True
        mock_os_path.exists.return_value = True
        
        # Mock pandas DataFrame
        mock_df = MagicMock()
        mock_df.shape = (10, 5)
        mock_df.columns = ['col1', 'col2', 'col3', 'col4', 'col5']
        mock_df.__len__.return_value = 10
        mock_pd.read_csv.return_value = mock_df
        
        # Mock column operations
        # Setup column operations with proper return values for all methods
        mock_col = MagicMock()
        mock_df.__getitem__.return_value = mock_col
        mock_col.dtype = 'int64'
        mock_col.isna.return_value.sum.return_value = 0
        mock_col.isna.return_value.mean.return_value = 0
        mock_col.min.return_value = 0
        mock_col.max.return_value = 100
        mock_col.mean.return_value = 50
        mock_col.median.return_value = 50
        mock_col.std.return_value = 25
        mock_col.value_counts.return_value.head.return_value.to_dict.return_value = {'val1': 5, 'val2': 3}
        mock_col.nunique.return_value = 2
        
        # Handle the grouped_info functionality by setting up the comparison correctly
        mock_pd.api.types.is_numeric_dtype.return_value = True
        mock_pd.api.types.is_object_dtype.return_value = False
        mock_pd.api.types.is_categorical_dtype.return_value = False
        mock_pd.api.types.is_datetime64_dtype.return_value = False
        mock_pd.isna.return_value = False
        
        # Mock the anthropic.Anthropic().messages.create method
        mock_response = MagicMock()
        mock_response.content = [MagicMock(text='<div id="visualization-container">Test Visualization</div>')]
        mock_anthropic_instance.messages.create.return_value = mock_response
        
        # Mock the _create_visualization_prompt method to avoid dataset_stats generation
        with patch.object(self.client, '_create_visualization_prompt', return_value='mocked prompt'):
            # Call the method being tested
            result = self.client.generate_visualization(1, 'bar', 'Test Visualization')
        
        # Assertions
        self.assertEqual(result, '<div id="visualization-container">Test Visualization</div>')
        mock_anthropic_instance.messages.create.assert_called_once()
    
    @patch('app.services.claude_client.Dataset')
    @patch('app.services.claude_client.pd')
    @patch('app.services.claude_client.os.path')
    @patch('app.services.claude_client.anthropic', spec=anthropic)
    def test_generate_visualization_with_markdown_response(self, mock_anthropic, mock_os_path, mock_pd, mock_dataset):
        """Test handling of markdown-formatted response from Claude."""
        # Configure mocks as in previous test
        mock_anthropic_instance = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_anthropic_instance
        mock_anthropic.__version__ = '0.7.0'
        mock_dataset.query.get_or_404.return_value = self.mock_dataset
        mock_os_path.exists.return_value = True
        mock_df = MagicMock()
        mock_df.shape = (10, 5)
        mock_df.columns = ['col1', 'col2', 'col3', 'col4', 'col5']
        mock_df.__len__.return_value = 10
        mock_pd.read_csv.return_value = mock_df
        # Setup column with proper nunique handling
        mock_col = MagicMock()
        mock_df.__getitem__.return_value = mock_col
        mock_col.dtype = 'int64'
        mock_col.isna.return_value.sum.return_value = 0
        mock_col.isna.return_value.mean.return_value = 0
        mock_col.nunique.return_value = 2
        
        # Mock pandas type check methods
        mock_pd.api.types.is_numeric_dtype.return_value = True
        mock_pd.api.types.is_object_dtype.return_value = False
        mock_pd.api.types.is_categorical_dtype.return_value = False
        mock_pd.api.types.is_datetime64_dtype.return_value = False
        mock_pd.isna.return_value = False
        
        # Mock response with markdown code blocks
        mock_response = MagicMock()
        markdown_response = """```html
<div id="visualization-container">Markdown Test Visualization</div>
```"""
        mock_response.content = [MagicMock(text=markdown_response)]
        mock_anthropic_instance.messages.create.return_value = mock_response
        
        # Mock the _create_visualization_prompt method to avoid dataset_stats generation
        with patch.object(self.client, '_create_visualization_prompt', return_value='mocked prompt'):
            # Call the method being tested
            result = self.client.generate_visualization(1, 'bar', 'Test Visualization')
        
        # Assertions
        self.assertIn('<div id="visualization-container">Markdown Test Visualization</div>', result)
        mock_anthropic_instance.messages.create.assert_called_once()
    
    @patch('app.services.claude_client.Dataset')
    @patch('app.services.claude_client.pd')
    @patch('app.services.claude_client.os.path')
    @patch('app.services.claude_client.anthropic', spec=anthropic)
    def test_generate_visualization_no_container_div(self, mock_anthropic, mock_os_path, mock_pd, mock_dataset):
        """Test handling of response without the visualization container div."""
        # Configure mocks as in previous tests
        mock_anthropic_instance = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_anthropic_instance
        mock_anthropic.__version__ = '0.7.0'
        mock_dataset.query.get_or_404.return_value = self.mock_dataset
        mock_os_path.exists.return_value = True
        mock_df = MagicMock()
        mock_df.shape = (10, 5)
        mock_df.columns = ['col1', 'col2', 'col3', 'col4', 'col5']
        mock_df.__len__.return_value = 10
        mock_pd.read_csv.return_value = mock_df
        # Setup column with proper nunique handling
        mock_col = MagicMock()
        mock_df.__getitem__.return_value = mock_col
        mock_col.dtype = 'int64'
        mock_col.isna.return_value.sum.return_value = 0
        mock_col.isna.return_value.mean.return_value = 0
        mock_col.nunique.return_value = 2
        
        # Mock pandas type check methods
        mock_pd.api.types.is_numeric_dtype.return_value = True
        mock_pd.api.types.is_object_dtype.return_value = False
        mock_pd.api.types.is_categorical_dtype.return_value = False
        mock_pd.api.types.is_datetime64_dtype.return_value = False
        mock_pd.isna.return_value = False
        
        # Mock response without the visualization container div
        mock_response = MagicMock()
        response_without_div = """<canvas id="myChart"></canvas>
<script>
  const ctx = document.getElementById('myChart').getContext('2d');
  const chart = new Chart(ctx, {
    type: 'bar',
    data: {
      labels: ['Red', 'Blue', 'Yellow'],
      datasets: []
    }
  });
</script>"""
        mock_response.content = [MagicMock(text=response_without_div)]
        mock_anthropic_instance.messages.create.return_value = mock_response
        
        # Mock the _create_visualization_prompt method to avoid dataset_stats generation
        with patch.object(self.client, '_create_visualization_prompt', return_value='mocked prompt'):
            # Mock the _create_visualization_prompt method to avoid dataset_stats generation
            with patch.object(self.client, '_create_visualization_prompt', return_value='mocked prompt'):
                # Call the method being tested
                result = self.client.generate_visualization(1, 'bar', 'Test Visualization')
        
        # Assertions
        self.assertEqual(result, f'<div id="visualization-container">{response_without_div}</div>')
        mock_anthropic_instance.messages.create.assert_called_once()
    
    @patch('app.services.claude_client.Dataset')
    @patch('app.services.claude_client.pd')
    @patch('app.services.claude_client.os.path')
    @patch('app.services.claude_client.anthropic', spec=anthropic)
    @patch('app.services.claude_client.time')
    def test_generate_visualization_with_retry(self, mock_time, mock_anthropic, mock_os_path, mock_pd, mock_dataset):
        """Test that visualization generation retries on failure."""
        # Configure mocks
        mock_anthropic_instance = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_anthropic_instance
        mock_anthropic.__version__ = '0.7.0'
        mock_dataset.query.get_or_404.return_value = self.mock_dataset
        mock_os_path.exists.return_value = True
        mock_df = MagicMock()
        mock_df.shape = (10, 5)
        mock_df.columns = ['col1', 'col2', 'col3', 'col4', 'col5']
        mock_df.__len__.return_value = 10
        mock_pd.read_csv.return_value = mock_df
        # Setup column with proper nunique handling
        mock_col = MagicMock()
        mock_df.__getitem__.return_value = mock_col
        mock_col.dtype = 'int64'
        mock_col.isna.return_value.sum.return_value = 0
        mock_col.isna.return_value.mean.return_value = 0
        mock_col.nunique.return_value = 2
        
        # Mock pandas type check methods
        mock_pd.api.types.is_numeric_dtype.return_value = True
        mock_pd.api.types.is_object_dtype.return_value = False
        mock_pd.api.types.is_categorical_dtype.return_value = False
        mock_pd.api.types.is_datetime64_dtype.return_value = False
        mock_pd.isna.return_value = False
        
        # Configure messages.create to fail once then succeed
        mock_anthropic_instance.messages.create.side_effect = [
            Exception("API Error"),
            MagicMock(content=[MagicMock(text='<div id="visualization-container">Retry Success</div>')])
        ]
        
        # Call the method being tested
        result = self.client.generate_visualization(1, 'bar', 'Test Visualization')
        
        # Assertions
        self.assertEqual(result, '<div id="visualization-container">Retry Success</div>')
        self.assertEqual(mock_anthropic_instance.messages.create.call_count, 2)
        mock_time.sleep.assert_called_once()
    
    @patch('app.services.claude_client.Dataset')
    @patch('app.services.claude_client.pd')
    @patch('app.services.claude_client.os.path')
    @patch('app.services.claude_client.anthropic', spec=anthropic)
    @patch('app.services.claude_client.time')
    def test_generate_visualization_max_retries_exceeded(self, mock_time, mock_anthropic, mock_os_path, mock_pd, mock_dataset):
        """Test that visualization generation fails after max retries."""
        # Configure mocks
        mock_anthropic_instance = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_anthropic_instance
        mock_anthropic.__version__ = '0.7.0'
        mock_dataset.query.get_or_404.return_value = self.mock_dataset
        mock_os_path.exists.return_value = True
        mock_df = MagicMock()
        mock_df.shape = (10, 5)
        mock_df.columns = ['col1', 'col2', 'col3', 'col4', 'col5']
        mock_df.__len__.return_value = 10
        mock_pd.read_csv.return_value = mock_df
        # Setup column with proper nunique handling
        mock_col = MagicMock()
        mock_df.__getitem__.return_value = mock_col
        mock_col.dtype = 'int64'
        mock_col.isna.return_value.sum.return_value = 0
        mock_col.isna.return_value.mean.return_value = 0
        mock_col.nunique.return_value = 2
        
        # Mock pandas type check methods
        mock_pd.api.types.is_numeric_dtype.return_value = True
        mock_pd.api.types.is_object_dtype.return_value = False
        mock_pd.api.types.is_categorical_dtype.return_value = False
        mock_pd.api.types.is_datetime64_dtype.return_value = False
        mock_pd.isna.return_value = False
        
        # Mock the _create_visualization_prompt method to avoid dataset_stats generation
        with patch.object(self.client, '_create_visualization_prompt', return_value='mocked prompt'):
            # Configure messages.create to always fail
            mock_anthropic_instance.messages.create.side_effect = Exception("API Error")
        
        # Call the method being tested and verify it raises an exception
        with self.assertRaises(Exception):
            self.client.generate_visualization(1, 'bar', 'Test Visualization')
        
        # Assertions
            # Call should happen 3 times
            self.assertEqual(mock_anthropic_instance.messages.create.call_count, 3)  # max_retries is 3
        self.assertEqual(mock_time.sleep.call_count, 2)  # Should sleep between retries, but not after last attempt


if __name__ == '__main__':
    unittest.main()