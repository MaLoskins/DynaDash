import unittest
from app import create_app, db
from app.models import User, Dataset, Visualisation, Share
from config import config

class ModelsTestCase(unittest.TestCase):
    """Test case for the database models."""
    
    def setUp(self):
        """Set up the test environment."""
        self.app = create_app('testing')
        self.app_context = self.app.app_context()
        self.app_context.push()
        db.create_all()
    
    def tearDown(self):
        """Clean up the test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_user_model(self):
        """Test the User model."""
        # Create a user
        user = User(name='Test User', email='test@example.com', password='password')
        db.session.add(user)
        db.session.commit()
        
        # Retrieve the user
        retrieved_user = User.query.filter_by(email='test@example.com').first()
        
        # Check that the user was retrieved correctly
        self.assertIsNotNone(retrieved_user)
        self.assertEqual(retrieved_user.name, 'Test User')
        self.assertEqual(retrieved_user.email, 'test@example.com')
        
        # Check that the password is hashed
        self.assertNotEqual(retrieved_user.password_hash, 'password')
        self.assertTrue(retrieved_user.verify_password('password'))
        self.assertFalse(retrieved_user.verify_password('wrong_password'))
    
    def test_dataset_model(self):
        """Test the Dataset model."""
        # Create a user
        user = User(name='Test User', email='test@example.com', password='password')
        db.session.add(user)
        db.session.commit()
        
        # Create a dataset
        dataset = Dataset(
            user_id=user.id,
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
        
        # Retrieve the dataset
        retrieved_dataset = Dataset.query.filter_by(filename='test_dataset.csv').first()
        
        # Check that the dataset was retrieved correctly
        self.assertIsNotNone(retrieved_dataset)
        self.assertEqual(retrieved_dataset.user_id, user.id)
        self.assertEqual(retrieved_dataset.filename, 'test_dataset.csv')
        self.assertEqual(retrieved_dataset.file_type, 'csv')
        self.assertEqual(retrieved_dataset.n_rows, 100)
        self.assertEqual(retrieved_dataset.n_columns, 5)
        self.assertFalse(retrieved_dataset.is_public)
    
    def test_visualisation_model(self):
        """Test the Visualisation model."""
        # Create a user
        user = User(name='Test User', email='test@example.com', password='password')
        db.session.add(user)
        db.session.commit()
        
        # Create a dataset
        dataset = Dataset(
            user_id=user.id,
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
        
        # Create a visualisation
        visualisation = Visualisation(
            dataset_id=dataset.id,
            title='Test Visualisation',
            description='A test visualisation',
            spec='<div>Test Visualisation</div>'
        )
        db.session.add(visualisation)
        db.session.commit()
        
        # Retrieve the visualisation
        retrieved_visualisation = Visualisation.query.filter_by(title='Test Visualisation').first()
        
        # Check that the visualisation was retrieved correctly
        self.assertIsNotNone(retrieved_visualisation)
        self.assertEqual(retrieved_visualisation.dataset_id, dataset.id)
        self.assertEqual(retrieved_visualisation.title, 'Test Visualisation')
        self.assertEqual(retrieved_visualisation.description, 'A test visualisation')
        self.assertEqual(retrieved_visualisation.spec, '<div>Test Visualisation</div>')
    
    def test_share_model(self):
        """Test the Share model."""
        # Create two users
        user1 = User(name='User 1', email='user1@example.com', password='password')
        user2 = User(name='User 2', email='user2@example.com', password='password')
        db.session.add_all([user1, user2])
        db.session.commit()
        
        # Create a dataset
        dataset = Dataset(
            user_id=user1.id,
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
        
        # Create a share
        share = Share(
            owner_id=user1.id,
            target_id=user2.id,
            object_type='dataset',
            object_id=dataset.id
        )
        db.session.add(share)
        db.session.commit()
        
        # Retrieve the share
        retrieved_share = Share.query.filter_by(
            owner_id=user1.id,
            target_id=user2.id,
            object_type='dataset',
            object_id=dataset.id
        ).first()
        
        # Check that the share was retrieved correctly
        self.assertIsNotNone(retrieved_share)
        self.assertEqual(retrieved_share.owner_id, user1.id)
        self.assertEqual(retrieved_share.target_id, user2.id)
        self.assertEqual(retrieved_share.object_type, 'dataset')
        self.assertEqual(retrieved_share.object_id, dataset.id)

if __name__ == '__main__':
    unittest.main()