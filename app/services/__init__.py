# Import services for easier access
from .data_processor import DataProcessor
from .claude_client import ClaudeClient

# Instantiate services that need app context for configuration
claude_service = ClaudeClient()
# DataProcessor can be instantiated directly where needed if it doesn't require app-level config at init
# or you can instantiate it here too if you prefer:
# data_processor_service = DataProcessor()


__all__ = ['DataProcessor', 'claude_service'] # Make the instance available