import os
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

class Config:
    """Base configuration class."""
    # Flask settings
    SECRET_KEY = os.getenv('SECRET_KEY', 'dev_key_change_in_production')
    
    # SQLAlchemy settings
    SQLALCHEMY_DATABASE_URI = os.getenv('DYNA_SQLITE_PATH', 'sqlite:///dynadash.db')
    SQLALCHEMY_TRACK_MODIFICATIONS = False
    
    # File upload settings
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'uploads')
    MAX_CONTENT_LENGTH = 50 * 1024 * 1024  # 50MB max file size
    
    # Anthropic Claude API settings
    ANTHROPIC_API_KEY = os.getenv('ANTHROPIC_API_KEY')
    
    # Socket.IO settings
    SOCKETIO_ASYNC_MODE = 'threading'
    
    @staticmethod
    def init_app(app):
        """Initialize application with this configuration."""
        pass

class DevelopmentConfig(Config):
    """Development configuration."""
    DEBUG = True
    
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Log to console
        import logging
        handler = logging.StreamHandler()
        handler.setLevel(logging.INFO)
        app.logger.addHandler(handler)

class TestingConfig(Config):
    """Testing configuration."""
    TESTING = True
    DEBUG = True
    SQLALCHEMY_DATABASE_URI = 'sqlite:///:memory:'
    WTF_CSRF_ENABLED = False
    
    # Use a temporary folder for uploads during testing
    UPLOAD_FOLDER = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'tests', 'uploads')

class ProductionConfig(Config):
    """Production configuration."""
    DEBUG = False
    
    # Ensure production-grade secret key
    @classmethod
    def init_app(cls, app):
        Config.init_app(app)
        
        # Ensure proper secret key in production
        if app.config['SECRET_KEY'] == 'dev_key_change_in_production':
            raise ValueError("Production requires proper SECRET_KEY")
        
        # Ensure Anthropic API key is set
        if not app.config['ANTHROPIC_API_KEY']:
            raise ValueError("Production requires ANTHROPIC_API_KEY")
        
        # Log to file
        import logging
        from logging.handlers import RotatingFileHandler
        
        # Create logs directory if it doesn't exist
        logs_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)), 'logs')
        os.makedirs(logs_dir, exist_ok=True)
        
        # Set up file handler
        file_handler = RotatingFileHandler(
            os.path.join(logs_dir, 'dynadash.log'),
            maxBytes=10 * 1024 * 1024,  # 10MB
            backupCount=10
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        
        app.logger.setLevel(logging.INFO)
        app.logger.info('DynaDash startup')

# Configuration dictionary
config = {
    'development': DevelopmentConfig,
    'testing': TestingConfig,
    'production': ProductionConfig,
    'default': DevelopmentConfig
}