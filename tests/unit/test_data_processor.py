import os
import unittest
import pandas as pd
import numpy as np
import tempfile
import warnings
import uuid
import io
from datetime import datetime
from app.services import DataProcessor
from app.models import Dataset
from app import create_app, db
from werkzeug.datastructures import FileStorage

class TestDataProcessor(unittest.TestCase):
    """Test cases for the DataProcessor class."""
    
    def setUp(self):
        """Set up the test environment."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        self.processor = DataProcessor()
        
        # Create a temporary directory for test uploads
        self.test_upload_dir = tempfile.mkdtemp()
        self.app.config['UPLOAD_FOLDER'] = self.test_upload_dir
        
    def tearDown(self):
        """Clean up after the tests."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
        
        # Clean up temporary files
        for filename in os.listdir(self.test_upload_dir):
            os.remove(os.path.join(self.test_upload_dir, filename))
        os.rmdir(self.test_upload_dir)
    
    def test_clean_data_datetime_parsing(self):
        """Test that datetime columns are properly parsed without infer_datetime_format."""
        # Create a dataframe with various datetime formats
        data = {
            'date_ymd': ['2023-01-01', '2023-02-15', '2023-03-30'],
            'date_mdy': ['01/15/2023', '02/20/2023', '03/25/2023'],
            'date_dmy': ['31/01/2023', '28/02/2023', '31/03/2023'],
            'date_with_time': ['2023-01-01 12:30:45', '2023-02-15 08:15:30', '2023-03-30 18:45:10'],
            'text_col': ['abc', 'def', 'ghi']
        }
        df = pd.DataFrame(data)
        
        # Capture warnings during processing
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            # Process the dataframe
            cleaned_df = self.processor._clean_data(df)
            
            # Check that no warnings about infer_datetime_format were raised
            infer_datetime_warnings = [
                warning for warning in w 
                if 'infer_datetime_format' in str(warning.message)
            ]
            self.assertEqual(len(infer_datetime_warnings), 0, 
                            "Warnings about infer_datetime_format were detected")
        
        # Check that datetime columns were correctly identified and converted
        self.assertIn('date_ymd_date', cleaned_df.columns)
        self.assertIn('date_mdy_date', cleaned_df.columns)
        self.assertIn('date_dmy_date', cleaned_df.columns)
        self.assertIn('date_with_time_date', cleaned_df.columns)
        
        # Verify the values are correctly formatted
        self.assertEqual(cleaned_df['date_ymd_date'].iloc[0], '2023-01-01')
        self.assertEqual(cleaned_df['date_mdy_date'].iloc[0], '2023-01-15')
        self.assertEqual(cleaned_df['date_dmy_date'].iloc[0], '2023-01-31')
        
    def test_clean_data_empty_and_invalid_datetime(self):
        """Test handling of empty and invalid datetime values."""
        # Create a dataframe with empty and invalid datetime values
        data = {
            'date_with_empty': ['2023-01-01', '', '2023-03-30'],
            'date_with_invalid': ['2023-01-01', 'not-a-date', '2023-03-30'],
            'mostly_invalid_dates': ['not-a-date', 'also-not-a-date', '2023-03-30']
        }
        df = pd.DataFrame(data)
        
        # Process the dataframe
        cleaned_df = self.processor._clean_data(df)
        
        # Check that columns with valid dates are kept
        self.assertIn('date_with_empty_date', cleaned_df.columns)
        self.assertIn('date_with_invalid_date', cleaned_df.columns)
        
        # Column where most values are invalid should be dropped
        self.assertNotIn('mostly_invalid_dates_date', cleaned_df.columns)
        
    def test_process_csv_with_datetime(self):
        """Test processing a CSV file with datetime columns."""
        # Create a test CSV file with datetime columns
        test_data = pd.DataFrame({
            'date_col': ['2023-01-01', '2023-02-15', '2023-03-30'],
            'value': [100, 200, 300]
        })
        
        # Create a temporary file
        with tempfile.NamedTemporaryFile(suffix='.csv', delete=False) as temp_file:
            test_data.to_csv(temp_file.name, index=False)
            temp_file_path = temp_file.name
        
        # Create a file storage object that will be closed properly
        file_content = open(temp_file_path, 'rb').read()
        file_storage = FileStorage(
            stream=io.BytesIO(file_content),
            filename='test_datetime.csv',
            content_type='text/csv'
        )
        
        # Process the file
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            
            try:
                dataset = self.processor.process(file_storage, user_id=1)
                
                # Check for infer_datetime_format warnings
                infer_datetime_warnings = [
                    warning for warning in w
                    if 'infer_datetime_format' in str(warning.message)
                ]
                self.assertEqual(len(infer_datetime_warnings), 0,
                                "Warnings about infer_datetime_format were detected")
                
                # Check that the dataset was created correctly
                self.assertIsInstance(dataset, Dataset)
                self.assertEqual(dataset.n_rows, 3)
                
                # Load the processed file to verify datetime parsing
                processed_df = pd.read_csv(dataset.file_path)
                self.assertIn('date_col_date', processed_df.columns)
                
            finally:
                # Clean up
                if os.path.exists(temp_file_path):
                    try:
                        os.remove(temp_file_path)
                    except (PermissionError, OSError):
                        # On Windows, sometimes the file is still in use
                        pass
                
                # Also clean up any dataset files
                if 'dataset' in locals():
                    if os.path.exists(dataset.file_path):
                        os.remove(dataset.file_path)

    def test_recursion_base_case(self):
        """Test base case for datetime parsing (simple formats)."""
        # Create a dataframe with a simple date format
        data = {'date': ['2023-01-01']}
        df = pd.DataFrame(data)
        
        # Process the dataframe
        cleaned_df = self.processor._clean_data(df)
        
        # Check that date column was converted
        self.assertIn('date_date', cleaned_df.columns)
        self.assertEqual(cleaned_df['date_date'].iloc[0], '2023-01-01')
    
    def test_recursion_typical_case(self):
        """Test typical case for datetime parsing (common formats, multiple rows)."""
        # Create a dataframe with multiple rows and common formats
        data = {
            'date1': ['2023-01-01', '2023-02-15', '2023-03-30'],
            'date2': ['01/15/2023', '02/20/2023', '03/25/2023']
        }
        df = pd.DataFrame(data)
        
        # Process the dataframe
        cleaned_df = self.processor._clean_data(df)
        
        # Check conversion
        self.assertIn('date1_date', cleaned_df.columns)
        self.assertIn('date2_date', cleaned_df.columns)
        self.assertEqual(len(cleaned_df), 3)
    
    def test_recursion_edge_case(self):
        """Test edge cases for datetime parsing (mixed formats, empty values)."""
        # Create a dataframe with edge cases
        data = {
            'mixed_formats': ['2023-01-01', '02/15/2023', '30-Mar-2023'],
            'with_empty': ['2023-01-01', '', '2023-03-30'],
            'all_empty': ['', '', '']
        }
        df = pd.DataFrame(data)
        
        # Process the dataframe
        cleaned_df = self.processor._clean_data(df)
        
        # Without infer_datetime_format, the mixed formats might be harder to parse
        # but at least the column with consistent empty values should work
        self.assertIn('with_empty_date', cleaned_df.columns)
        
        # All empty should not create a date column
        self.assertNotIn('all_empty_date', cleaned_df.columns)
        
        # Check for any warnings about infer_datetime_format
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            pd.to_datetime(df['mixed_formats'], errors='coerce')
            
            infer_warnings = [
                warning for warning in w
                if 'infer_datetime_format' in str(warning.message)
            ]
            self.assertEqual(len(infer_warnings), 0,
                            "infer_datetime_format still being used in pandas")
    
    def test_recursion_depth_stress(self):
        """Test depth stress for datetime parsing (many formats, complex cases)."""
        # Create a large dataset with various datetime formats
        formats = [
            '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
            '%b %d, %Y', '%d %b %Y', '%B %d, %Y', '%d %B %Y',
            '%m-%d-%Y', '%d-%m-%Y', '%Y.%m.%d', '%d.%m.%Y'
        ]
        
        now = datetime.now()
        
        # Generate sample dates in different formats
        data = {}
        for i, fmt in enumerate(formats):
            col_name = f'date_format_{i}'
            try:
                data[col_name] = [now.strftime(fmt) for _ in range(100)]
            except ValueError:
                # Skip invalid formats
                continue
        
        df = pd.DataFrame(data)
        
        # Process the dataframe - should handle all formats without issues
        cleaned_df = self.processor._clean_data(df)
        
        # Check that date columns were created
        for col_name in data.keys():
            date_col = f'{col_name}_date'
            self.assertIn(date_col, cleaned_df.columns)

if __name__ == '__main__':
    unittest.main()