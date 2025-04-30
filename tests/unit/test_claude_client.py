import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import anthropic
from flask import Flask

# Add the app directory to the path so we can import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.services.claude_client import ClaudeClient

class TestClaudeClient(unittest.TestCase):
    """Tests for the ClaudeClient service."""
    
    def setUp(self):
        """Set up test fixtures."""
        self.app = Flask(__name__)
        self.app.config['ANTHROPIC_API_KEY'] = 'test_api_key'
        self.app_context = self.app.app_context()
        self.app_context.push()
        self.client = ClaudeClient()
    
    def tearDown(self):
        """Tear down test fixtures."""
        self.app_context.pop()
    
    @patch('app.services.claude_client.anthropic', spec=anthropic)
    @patch('app.services.claude_client.os')
    def test_client_initialization_with_anthropic_class(self, mock_os, mock_anthropic):
        """Test client initialization with Anthropic class (v0.7.0+)."""
        # Configure mocks
        mock_anthropic_instance = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_anthropic_instance
        mock_anthropic.__version__ = '0.7.0'
        
        # Setup environment variables mock
        mock_os.environ = MagicMock(spec=dict)
        mock_os.environ.get.return_value = None
        
        # Make hasattr return True for Anthropic and False for Client
        def mock_hasattr(obj, attr):
            if attr == 'Anthropic':
                return True
            elif attr == 'Client':
                return False
            return False
        
        # Override the built-in hasattr function for our test
        with patch('app.services.claude_client.hasattr', mock_hasattr):
            # Test initialization
            self.client._initialize_client()
            
            # Verify Anthropic constructor was called with no arguments
            mock_anthropic.Anthropic.assert_called_once_with()
            
            # Verify environment variable was set temporarily
            mock_os.environ.__setitem__.assert_any_call('ANTHROPIC_API_KEY', 'test_api_key')
            
            # Verify environment variable was cleaned up
            mock_os.environ.pop.assert_called_once()
            
            # Verify client is set correctly
            self.assertEqual(self.client.client, mock_anthropic_instance)
    
    @patch('app.services.claude_client.anthropic', spec=anthropic)
    def test_client_initialization_with_client_class(self, mock_anthropic):
        """Test client initialization with Client class (pre-v0.7.0)."""
        # Mock the Client class
        mock_client_instance = MagicMock()
        mock_anthropic.Client.return_value = mock_client_instance
        mock_anthropic.__version__ = '0.6.0'
        
        # Make hasattr return False for Anthropic and True for Client
        def mock_hasattr(obj, attr):
            if attr == 'Anthropic':
                return False
            elif attr == 'Client':
                return True
            return False
        
        # Override the built-in hasattr function for our test
        with patch('app.services.claude_client.hasattr', mock_hasattr):
            # Test initialization
            self.client._initialize_client()
            
            # Verify Client constructor was called with api_key
            mock_anthropic.Client.assert_called_once_with(api_key='test_api_key')
            
            # Verify client is set correctly
            self.assertEqual(self.client.client, mock_client_instance)
    
    @patch('app.services.claude_client.anthropic', spec=anthropic)
    def test_client_initialization_error(self, mock_anthropic):
        """Test client initialization error when neither class is available."""
        # Make hasattr return False for both Anthropic and Client
        def mock_hasattr(obj, attr):
            return False
        
        # Override the built-in hasattr function for our test
        with patch('app.services.claude_client.hasattr', mock_hasattr):
            # Test initialization should raise TypeError
            with self.assertRaises(TypeError):
                self.client._initialize_client()

if __name__ == '__main__':
    unittest.main()