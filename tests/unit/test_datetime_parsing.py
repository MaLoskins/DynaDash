import unittest
import pandas as pd
import numpy as np
import warnings
from app.services.data_processor import DataProcessor

class DatetimeParsingTestCase(unittest.TestCase):
    """Test cases for datetime parsing in DataProcessor after removing infer_datetime_format parameter"""
    
    def setUp(self):
        self.processor = DataProcessor()
        
    def test_datetime_parsing_without_infer_parameter(self):
        """Test datetime parsing works correctly without the deprecated parameter"""
        # Create a test DataFrame with datetime columns
        data = {
            'id': [1, 2, 3, 4, 5],
            'name': ['Item1', 'Item2', 'Item3', 'Item4', 'Item5'],
            'date_col': ['2025-01-01', '2025-01-02', '2025-01-03', '2025-01-04', '2025-01-05'],
            'timestamp_col': ['2025-01-01 12:30:45', '2025-01-02 13:40:50', '2025-01-03 14:50:55', 
                             '2025-01-04 15:10:20', '2025-01-05 16:20:30']
        }
        df = pd.DataFrame(data)
        
        # Process the DataFrame with our cleaning method
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            processed_df = self.processor._clean_data(df)
            
            # Check if there are any warnings related to infer_datetime_format
            infer_warnings = [warning for warning in w if "infer_datetime_format" in str(warning)]
            self.assertEqual(len(infer_warnings), 0, "There should be no warnings about infer_datetime_format")
        
        # Check that datetime columns were properly detected and parsed
        self.assertIn('date_col_date', processed_df.columns)
        self.assertIn('timestamp_col_date', processed_df.columns)
            
        # Check the values are properly parsed to datetime strings
        self.assertEqual(processed_df['date_col_date'].iloc[0], '2025-01-01')
        self.assertTrue(all(date.startswith('2025-01-') for date in processed_df['date_col_date']))
            
    def test_more_than_half_valid_dates(self):
        """Test parsing when more than 50% of values are valid dates"""
        # Create test data with mostly valid dates
        data = {
            'id': [1, 2, 3, 4],
            'dates': ['2025-01-15', '2025-02-20', '2025-03-25', 'invalid']
        }
        df = pd.DataFrame(data)
        
        # Process the DataFrame with our cleaning method
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            processed_df = self.processor._clean_data(df)
            
            # Check warnings - we expect no warnings about infer_datetime_format
            infer_warnings = [warning for warning in w if "infer_datetime_format" in str(warning)]
            self.assertEqual(len(infer_warnings), 0, "There should be no warnings about infer_datetime_format")
        
        # Check that date column was properly detected and parsed
        self.assertIn('dates_date', processed_df.columns)
        
        # Check the valid dates are properly formatted
        self.assertEqual(processed_df['dates_date'].iloc[0], '2025-01-15')
        
    def test_less_than_half_valid_dates(self):
        """Test parsing when less than 50% of values are valid dates"""
        # Create test data with mostly invalid dates
        data = {
            'id': [1, 2, 3, 4, 5],
            'mostly_invalid': ['valid_date 2025-01-01', 'invalid1', 'invalid2', 'invalid3', 'invalid4']
        }
        df = pd.DataFrame(data)
        
        # Process the DataFrame with our cleaning method
        with warnings.catch_warnings(record=True) as w:
            warnings.simplefilter("always")
            processed_df = self.processor._clean_data(df)
            
            # Check warnings - we expect no warnings about infer_datetime_format
            infer_warnings = [warning for warning in w if "infer_datetime_format" in str(warning)]
            self.assertEqual(len(infer_warnings), 0, "There should be no warnings about infer_datetime_format")
        
        # Since less than 50% are valid dates, the _date column should be dropped
        self.assertNotIn('mostly_invalid_date', processed_df.columns)

if __name__ == '__main__':
    unittest.main()