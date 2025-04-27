import unittest
from flask import url_for
from app import create_app, db
from app.models import User, Dataset, Visualisation, Share

class RoutesTestCase(unittest.TestCase):
    """Test case for the Flask routes."""
    
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
    
    def tearDown(self):
        """Clean up the test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def login(self):
        """Log in the test user."""
        return self.client.post('/auth/login', data={
            'email': 'test@example.com',
            'password': 'password',
            'remember_me': False
        }, follow_redirects=True)
    
    def test_home_page(self):
        """Test the home page."""
        response = self.client.get('/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Welcome to DynaDash', response.data)
    
    def test_login_page(self):
        """Test the login page."""
        response = self.client.get('/auth/login')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login to DynaDash', response.data)
    
    def test_register_page(self):
        """Test the register page."""
        response = self.client.get('/auth/register')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Create an Account', response.data)
    
    def test_login(self):
        """Test logging in."""
        response = self.login()
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Visualizations', response.data)
    
    def test_logout(self):
        """Test logging out."""
        # Log in
        self.login()
        
        # Log out
        response = self.client.get('/auth/logout', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'You have been logged out', response.data)
    
    def test_protected_page_redirect(self):
        """Test that protected pages redirect to login."""
        response = self.client.get('/visual/', follow_redirects=True)
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Login to DynaDash', response.data)
    
    def test_data_index(self):
        """Test the data index page."""
        # Log in
        self.login()
        
        # Access the data index page
        response = self.client.get('/data/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Datasets', response.data)
    
    def test_data_upload(self):
        """Test the data upload page."""
        # Log in
        self.login()
        
        # Access the data upload page
        response = self.client.get('/data/upload')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Upload Dataset', response.data)
    
    def test_visual_index(self):
        """Test the visual index page."""
        # Log in
        self.login()
        
        # Access the visual index page
        response = self.client.get('/visual/')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'My Visualizations', response.data)
    
    def test_dataset_view(self):
        """Test the dataset view page."""
        # Log in
        self.login()
        
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
        
        # Access the dataset view page
        response = self.client.get(f'/data/view/{dataset.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'test_dataset.csv', response.data)
    
    def test_dataset_share(self):
        """Test the dataset share page."""
        # Log in
        self.login()
        
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
        
        # Access the dataset share page
        response = self.client.get(f'/data/share/{dataset.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Share Dataset', response.data)
    
    def test_visualisation_generate(self):
        """Test the visualisation generate page."""
        # Log in
        self.login()
        
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
        
        # Access the visualisation generate page
        response = self.client.get(f'/visual/generate/{dataset.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Generate Visualization', response.data)
    
    def test_visualisation_view(self):
        """Test the visualisation view page."""
        # Log in
        self.login()
        
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
        
        # Create a test visualisation
        visualisation = Visualisation(
            dataset_id=dataset.id,
            title='Test Visualisation',
            description='A test visualisation',
            spec='<div>Test Visualisation</div>'
        )
        db.session.add(visualisation)
        db.session.commit()
        
        # Access the visualisation view page
        response = self.client.get(f'/visual/view/{visualisation.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Test Visualisation', response.data)
    
    def test_visualisation_share(self):
        """Test the visualisation share page."""
        # Log in
        self.login()
        
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
        
        # Create a test visualisation
        visualisation = Visualisation(
            dataset_id=dataset.id,
            title='Test Visualisation',
            description='A test visualisation',
            spec='<div>Test Visualisation</div>'
        )
        db.session.add(visualisation)
        db.session.commit()
        
        # Access the visualisation share page
        response = self.client.get(f'/visual/share/{visualisation.id}')
        self.assertEqual(response.status_code, 200)
        self.assertIn(b'Share Visualization', response.data)

if __name__ == '__main__':
    unittest.main()