import unittest
from unittest.mock import patch, MagicMock
import os
import sys
import anthropic
from flask import Flask

# Add the app directory to the path so we can import the app module
sys.path.append(os.path.abspath(os.path.join(os.path.dirname(__file__), '../..')))
from app.services.claude_client import ClaudeClient

class TestProxiesParameterFix(unittest.TestCase):
    """Tests specifically for the 'proxies' parameter fix in ClaudeClient."""
    
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
    def test_no_proxies_parameter_in_anthropic_class(self, mock_os, mock_anthropic):
        """Test that 'proxies' parameter is not passed to Anthropic class constructor."""
        # Configure mocks
        mock_anthropic_instance = MagicMock()
        mock_anthropic.Anthropic.return_value = mock_anthropic_instance
        mock_anthropic.__version__ = '0.7.0'
        
        # Setup environment variables mock
        mock_os.environ = MagicMock(spec=dict)
        mock_os.environ.get.return_value = None
        
        # Make hasattr return True for Anthropic
        def mock_hasattr(obj, attr):
            if attr == 'Anthropic':
                return True
            return False
        
        # Override the built-in hasattr function for our test
        with patch('app.services.claude_client.hasattr', mock_hasattr):
            # Test initialization
            self.client._initialize_client()
            
            # Verify Anthropic constructor was called without proxies parameter
            # This is the key test for the fix - we verify the function was called
            # with no arguments (not even kwargs that might include proxies)
            mock_anthropic.Anthropic.assert_called_once_with()
    
    @patch('app.services.claude_client.anthropic', spec=anthropic)
    def test_no_proxies_parameter_in_client_class(self, mock_anthropic):
        """Test that 'proxies' parameter is not passed to Client class constructor."""
        # Mock the Client class
        mock_client_instance = MagicMock()
        mock_anthropic.Client.return_value = mock_client_instance
        mock_anthropic.__version__ = '0.6.0'
        
        # Make hasattr return True for Client
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
            
            # Verify Client constructor was called with only api_key
            mock_anthropic.Client.assert_called_once_with(api_key='test_api_key')
            
            # Ensure no other parameters were passed
            args, kwargs = mock_anthropic.Client.call_args
            self.assertNotIn('proxies', kwargs)

if __name__ == '__main__':
    unittest.main()