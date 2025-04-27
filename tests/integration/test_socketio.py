import unittest
import json
from app import create_app, db, socketio
from app.models import User, Dataset
from flask_socketio import SocketIOTestClient

class SocketIOTestCase(unittest.TestCase):
    """Test case for the Socket.IO functionality."""
    
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
        
        # Create a Socket.IO test client
        self.socketio_client = SocketIOTestClient(self.app, socketio)
    
    def tearDown(self):
        """Clean up the test environment."""
        db.session.remove()
        db.drop_all()
        self.app_context.pop()
    
    def test_connect(self):
        """Test Socket.IO connection."""
        # Connect to Socket.IO
        self.socketio_client.connect()
        
        # Check that the client is connected
        self.assertTrue(self.socketio_client.is_connected())
        
        # Disconnect
        self.socketio_client.disconnect()
    
    def test_join_room(self):
        """Test joining a room."""
        # Connect to Socket.IO
        self.socketio_client.connect()
        
        # Join a room
        self.socketio_client.emit('join', {'user_id': self.user.id})
        
        # Check for a response (if any)
        # Note: In a real application, you might want to emit a confirmation
        # when a user joins a room, which you could check for here
        
        # Disconnect
        self.socketio_client.disconnect()
    
    def test_progress_update(self):
        """Test progress update events."""
        # Connect to Socket.IO
        self.socketio_client.connect()
        
        # Join a room
        self.socketio_client.emit('join', {'user_id': self.user.id})
        
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
        
        # Emit a progress update event
        with self.app.test_request_context():
            socketio.emit('progress_update', {
                'percent': 50,
                'message': 'Processing dataset...'
            }, room=self.user.id)
        
        # Check for the progress update event
        received = self.socketio_client.get_received()
        self.assertTrue(len(received) > 0)
        
        # Find the progress_update event
        progress_update_events = [
            event for event in received
            if event['name'] == 'progress_update'
        ]
        
        self.assertTrue(len(progress_update_events) > 0)
        event = progress_update_events[0]
        self.assertEqual(event['args'][0]['percent'], 50)
        self.assertEqual(event['args'][0]['message'], 'Processing dataset...')
        
        # Disconnect
        self.socketio_client.disconnect()
    
    def test_processing_complete(self):
        """Test processing complete events."""
        # Connect to Socket.IO
        self.socketio_client.connect()
        
        # Join a room
        self.socketio_client.emit('join', {'user_id': self.user.id})
        
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
        
        # Emit a processing complete event
        with self.app.test_request_context():
            socketio.emit('processing_complete', room=self.user.id)
        
        # Check for the processing complete event
        received = self.socketio_client.get_received()
        self.assertTrue(len(received) > 0)
        
        # Find the processing_complete event
        processing_complete_events = [
            event for event in received
            if event['name'] == 'processing_complete'
        ]
        
        self.assertTrue(len(processing_complete_events) > 0)
        
        # Disconnect
        self.socketio_client.disconnect()

if __name__ == '__main__':
    unittest.main()