import os
import pandas as pd
import numpy as np
import json
from flask import current_app
from flask_socketio import emit
from ..models import db, Dataset
import uuid
from werkzeug.utils import secure_filename

class DataProcessor:
    """Service for processing and cleaning uploaded datasets."""
    
    def __init__(self):
        """Initialize the data processor."""
        self.supported_file_types = ['csv', 'json']
    
    def process(self, file, user_id, is_public=False, socket_id=None):
        """
        Process an uploaded file and save it to the database.
        
        Args:
            file: The uploaded file object
            user_id: The ID of the user who uploaded the file
            is_public: Whether the dataset should be public
            socket_id: The Socket.IO session ID for progress updates
        
        Returns:
            The created Dataset object
        """
        # Validate file type
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in self.supported_file_types:
            raise ValueError(f"Unsupported file type: {file_ext}. Supported types: {', '.join(self.supported_file_types)}")
        
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the file
        file.save(file_path)
        
        # Process the file based on its type
        if file_ext == 'csv':
            return self._process_csv(file_path, filename, user_id, is_public, socket_id)
        elif file_ext == 'json':
            return self._process_json(file_path, filename, user_id, is_public, socket_id)
    
    def _process_csv(self, file_path, original_filename, user_id, is_public, socket_id):
        """Process a CSV file."""
        try:
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 10, 'message': 'Reading CSV file...'}, room=socket_id)
            
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 30, 'message': 'Cleaning data...'}, room=socket_id)
            
            # Clean the data
            df = self._clean_data(df)
            
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 60, 'message': 'Saving cleaned data...'}, room=socket_id)
            
            # Save the cleaned data back to the file
            df.to_csv(file_path, index=False)
            
            # Create a dataset record
            dataset = Dataset(
                user_id=user_id,
                filename=os.path.basename(file_path),
                original_filename=original_filename,
                file_path=file_path,
                file_type='csv',
                n_rows=len(df),
                n_columns=len(df.columns),
                is_public=is_public
            )
            
            db.session.add(dataset)
            db.session.commit()
            
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 100, 'message': 'Processing complete!'}, room=socket_id)
                emit('processing_complete', room=socket_id)
            
            return dataset
        
        except Exception as e:
            # Clean up the file if there was an error
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Emit error
            if socket_id:
                emit('processing_error', {'message': str(e)}, room=socket_id)
            
            raise
    
    def _process_json(self, file_path, original_filename, user_id, is_public, socket_id):
        """Process a JSON file."""
        try:
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 10, 'message': 'Reading JSON file...'}, room=socket_id)
            
            # Read the JSON file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Handle nested JSON structures
                if any(isinstance(v, (list, dict)) for v in data.values()):
                    # Flatten the structure
                    flattened = []
                    for key, value in data.items():
                        if isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    item['_key'] = key
                                    flattened.append(item)
                        elif isinstance(value, dict):
                            value['_key'] = key
                            flattened.append(value)
                    df = pd.DataFrame(flattened)
                else:
                    # Simple key-value pairs
                    df = pd.DataFrame([data])
            else:
                raise ValueError("Invalid JSON structure. Expected a list or dictionary.")
            
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 30, 'message': 'Cleaning data...'}, room=socket_id)
            
            # Clean the data
            df = self._clean_data(df)
            
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 60, 'message': 'Saving cleaned data...'}, room=socket_id)
            
            # Save the cleaned data back to the file
            df.to_json(file_path, orient='records')
            
            # Create a dataset record
            dataset = Dataset(
                user_id=user_id,
                filename=os.path.basename(file_path),
                original_filename=original_filename,
                file_path=file_path,
                file_type='json',
                n_rows=len(df),
                n_columns=len(df.columns),
                is_public=is_public
            )
            
            db.session.add(dataset)
            db.session.commit()
            
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 100, 'message': 'Processing complete!'}, room=socket_id)
                emit('processing_complete', room=socket_id)
            
            return dataset
        
        except Exception as e:
            # Clean up the file if there was an error
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Emit error
            if socket_id:
                emit('processing_error', {'message': str(e)}, room=socket_id)
            
            raise
    
    def _clean_data(self, df):
        """Clean and preprocess the data."""
        # Make a copy to avoid modifying the original
        df_cleaned = df.copy()
        
        # Handle missing values
        for col in df_cleaned.columns:
            # For numeric columns, replace NaN with the median
            if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].median())
            # For categorical columns, replace NaN with the mode
            elif pd.api.types.is_categorical_dtype(df_cleaned[col]) or pd.api.types.is_object_dtype(df_cleaned[col]):
                df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].mode()[0] if not df_cleaned[col].mode().empty else 'Unknown')
        
        # Handle outliers in numeric columns
        for col in df_cleaned.select_dtypes(include=[np.number]).columns:
            # Calculate IQR
            Q1 = df_cleaned[col].quantile(0.25)
            Q3 = df_cleaned[col].quantile(0.75)
            IQR = Q3 - Q1
            
            # Define bounds
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Tag outliers (don't remove them)
            df_cleaned.loc[(df_cleaned[col] < lower_bound) | (df_cleaned[col] > upper_bound), col + '_outlier'] = True
            df_cleaned.loc[~((df_cleaned[col] < lower_bound) | (df_cleaned[col] > upper_bound)), col + '_outlier'] = False
        
        # Convert date columns to datetime
        for col in df_cleaned.columns:
            if pd.api.types.is_object_dtype(df_cleaned[col]):
                try:
                    # Try to detect common date formats
                    date_formats = [
                        '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
                        '%b %d, %Y', '%d %b %Y', '%B %d, %Y', '%d %B %Y',
                        '%m-%d-%Y', '%d-%m-%Y', '%Y.%m.%d', '%d.%m.%Y'
                    ]
                    
                    # Sample the first non-null value to check format
                    sample = df_cleaned[col].dropna().iloc[0] if not df_cleaned[col].dropna().empty else None
                    
                    if sample:
                        # Try each format until one works
                        format_found = None
                        for date_format in date_formats:
                            try:
                                pd.to_datetime(sample, format=date_format)
                                format_found = date_format
                                break
                            except:
                                continue
                        
                        # If a format was found, use it; otherwise fall back to the default parser
                        if format_found:
                            df_cleaned[col + '_date'] = pd.to_datetime(df_cleaned[col], format=format_found, errors='coerce')
                        else:
                            # Use pandas default parser when format is unknown
                            df_cleaned[col + '_date'] = pd.to_datetime(df_cleaned[col], errors='coerce')
                    else:
                        # No sample available, use the default parser
                        df_cleaned[col + '_date'] = pd.to_datetime(df_cleaned[col], errors='coerce')
                    
                    # If more than 50% of the values are valid dates, keep the column
                    if df_cleaned[col + '_date'].notna().mean() > 0.5:
                        df_cleaned[col + '_date'] = df_cleaned[col + '_date'].dt.strftime('%Y-%m-%d')
                    else:
                        df_cleaned = df_cleaned.drop(columns=[col + '_date'])
                except Exception as e:
                    # If conversion fails, ignore
                    pass
        
        return df_cleaned
    
    def get_preview(self, dataset_id, max_rows=10):
        """Get a preview of the dataset as HTML."""
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
        
        # Convert to HTML table
        return df.to_html(classes='table table-striped table-bordered table-hover', index=False)
    
    def delete_dataset(self, dataset_id):    
        # Retrieve the Dataset object or return 404 if not found
        dataset = Dataset.query.get_or_404(dataset_id)

        # 1) Attempt to remove the file from disk; log a warning if it does not exist or removal fails
        if os.path.exists(dataset.file_path):
            try:
                os.remove(dataset.file_path)
            except Exception as e:
                current_app.logger.warning(
                    f"Failed to remove dataset file at {dataset.file_path}: {e}"
                )
        else:
            current_app.logger.warning(
                f"Dataset file not found during deletion: {dataset.file_path}"
            )

        # 2) Cascade-delete all associated Visualisation records to satisfy NOT-NULL FK constraint
        for vis in list(dataset.visualisations):
            db.session.delete(vis)

        # 3) Delete the Dataset record itself from the database
        db.session.delete(dataset)
        db.session.commit()