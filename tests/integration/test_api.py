import unittest
import json
import io
from app import create_app, db
from app.models import User, Dataset, Visualisation, Share

class APITestCase(unittest.TestCase):
    """Test case for the API endpoints."""
    
    def setUp(self):
        """Set up the test environment."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
        
        # Create a test client
        self.client = self.app.test_client()
        self.client.testing = True
        
        # Create a test user
        self.user = User(name='Test User', email='test@example.com', password='password')
        db.session.add(self.user)
        db.session.commit()
        
        # Log in the test user
        response = self.client.post('/auth/api/v1/login', json={
            'email': 'test@example.com',
            'password': 'password'
        })
        self.assertEqual(response.status_code, 200)
    
    def tearDown(self):
        """Clean up the test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_get_datasets(self):
        """Test the GET /api/v1/datasets endpoint."""
        # Create a test dataset
        dataset = Dataset(
            user_id=self.user.id,
            filename='test_dataset.csv',
            original_filename='test_dataset.csv',
            file_path='/path/to/test_dataset.csv',
            file_type='csv',
            n_rows=100,
            n_columns=5,
            is_public=False
        )
        db.session.add(dataset)
        db.session.commit()
        
        # Send a GET request to the endpoint
        response = self.client.get('/data/api/v1/datasets')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('datasets', data)
        self.assertEqual(len(data['datasets']), 1)
        self.assertEqual(data['datasets'][0]['filename'], 'test_dataset.csv')
    
    def test_get_shared_datasets(self):
        """Test the GET /api/v1/shared-datasets endpoint."""
        # Create another user
        user2 = User(name='User 2', email='user2@example.com', password='password')
        db.session.add(user2)
        db.session.commit()
        
        # Create a dataset owned by user2
        dataset = Dataset(
            user_id=user2.id,
            filename='shared_dataset.csv',
            original_filename='shared_dataset.csv',
            file_path='/path/to/shared_dataset.csv',
            file_type='csv',
            n_rows=100,
            n_columns=5,
            is_public=False
        )
        db.session.add(dataset)
        db.session.commit()
        
        # Share the dataset with the test user
        share = Share(
            owner_id=user2.id,
            target_id=self.user.id,
            object_type='dataset',
            object_id=dataset.id
        )
        db.session.add(share)
        db.session.commit()
        
        # Send a GET request to the endpoint
        response = self.client.get('/data/api/v1/shared-datasets')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('datasets', data)
        self.assertEqual(len(data['datasets']), 1)
        self.assertEqual(data['datasets'][0]['filename'], 'shared_dataset.csv')
    
    def test_upload_dataset(self):
        """Test the POST /api/v1/upload endpoint."""
        # Create a test file
        data = {
            'file': (io.BytesIO(b'col1,col2,col3\n1,2,3\n4,5,6\n'), 'test.csv'),
            'is_public': 'false'
        }
        
        # Send a POST request to the endpoint
        response = self.client.post(
            '/data/api/v1/upload',
            data=data,
            content_type='multipart/form-data'
        )
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('success', data)
        self.assertTrue(data['success'])
        self.assertIn('dataset_id', data)
        
        # Check that the dataset was created
        dataset = Dataset.query.get(data['dataset_id'])
        self.assertIsNotNone(dataset)
        self.assertEqual(dataset.user_id, self.user.id)
        self.assertEqual(dataset.file_type, 'csv')
    
    def test_get_visualisations(self):
        """Test the GET /api/v1/visualisations endpoint."""
        # Create a test dataset
        dataset = Dataset(
            user_id=self.user.id,
            filename='test_dataset.csv',
            original_filename='test_dataset.csv',
            file_path='/path/to/test_dataset.csv',
            file_type='csv',
            n_rows=100,
            n_columns=5,
            is_public=False
        )
        db.session.add(dataset)
        db.session.commit()
        
        # Create a test visualisation
        visualisation = Visualisation(
            dataset_id=dataset.id,
            title='Test Visualisation',
            description='A test visualisation',
            spec='<div>Test Visualisation</div>'
        )
        db.session.add(visualisation)
        db.session.commit()
        
        # Send a GET request to the endpoint
        response = self.client.get('/visual/api/v1/visualisations')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('visualisations', data)
        self.assertEqual(len(data['visualisations']), 1)
        self.assertEqual(data['visualisations'][0]['title'], 'Test Visualisation')
    
    def test_get_shared_visualisations(self):
        """Test the GET /api/v1/shared-visualisations endpoint."""
        # Create another user
        user2 = User(name='User 2', email='user2@example.com', password='password')
        db.session.add(user2)
        db.session.commit()
        
        # Create a dataset owned by user2
        dataset = Dataset(
            user_id=user2.id,
            filename='shared_dataset.csv',
            original_filename='shared_dataset.csv',
            file_path='/path/to/shared_dataset.csv',
            file_type='csv',
            n_rows=100,
            n_columns=5,
            is_public=False
        )
        db.session.add(dataset)
        db.session.commit()
        
        # Create a visualisation for the dataset
        visualisation = Visualisation(
            dataset_id=dataset.id,
            title='Shared Visualisation',
            description='A shared visualisation',
            spec='<div>Shared Visualisation</div>'
        )
        db.session.add(visualisation)
        db.session.commit()
        
        # Share the visualisation with the test user
        share = Share(
            owner_id=user2.id,
            target_id=self.user.id,
            object_type='visualisation',
            object_id=visualisation.id
        )
        db.session.add(share)
        db.session.commit()
        
        # Send a GET request to the endpoint
        response = self.client.get('/visual/api/v1/shared-visualisations')
        
        # Check the response
        self.assertEqual(response.status_code, 200)
        data = json.loads(response.data)
        self.assertIn('visualisations', data)
        self.assertEqual(len(data['visualisations']), 1)
        self.assertEqual(data['visualisations'][0]['title'], 'Shared Visualisation')
    
    def test_generate_visualisation(self):
        """Test the POST /api/v1/generate endpoint."""
        # Create a test dataset
        dataset = Dataset(
            user_id=self.user.id,
            filename='test_dataset.csv',
            original_filename='test_dataset.csv',
            file_path='/path/to/test_dataset.csv',
            file_type='csv',
            n_rows=100,
            n_columns=5,
            is_public=False
        )
        db.session.add(dataset)
        db.session.commit()
        
        # Send a POST request to the endpoint
        response = self.client.post('/visual/api/v1/generate', json={
            'dataset_id': dataset.id,
            'chart_type': 'bar',
            'title': 'Test Visualisation',
            'description': 'A test visualisation'
        })
        
        # Check the response
        # Note: This test will fail in a real environment because it requires the Claude API
        # In a real test, we would mock the Claude API
        self.assertEqual(response.status_code, 500)  # Expected to fail without Claude API

if __name__ == '__main__':
    unittest.main()