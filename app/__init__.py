import os
import logging
from logging.handlers import RotatingFileHandler, SMTPHandler
from flask import Flask, redirect, url_for, request
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

from .models import db, User
from config import config

# Initialize extensions
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

socketio = SocketIO()
csrf = CSRFProtect()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address)
cache = Cache()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    # Add Rate Limiter configuration
    limiter.init_app(app)

    # Logging setup
    if not os.path.exists('logs'):
        os.makedirs('logs')
    file_handler = RotatingFileHandler('logs/api.log', maxBytes=10240, backupCount=3)
    file_handler.setFormatter(logging.Formatter('[%(asctime)s] %(levelname)s in %(module)s: %(message)s'))
    file_handler.setLevel(logging.INFO)
    app.logger.addHandler(file_handler)

    # Log each incoming request
    @app.before_request
    def log_request_info():
        app.logger.info(
            f'{request.method} {request.path} from {request.remote_addr} '
            f'user={getattr(current_user, "id", "anonymous")}'
        )
    
    # Initialize extensions with app
    db.init_app(app)
    login_manager.init_app(app)
    socketio.init_app(app, cors_allowed_origins='*')
    csrf.init_app(app)
    migrate.init_app(app, db)
    
    # Ensure upload folder exists
    os.makedirs(app.config['UPLOAD_FOLDER'], exist_ok=True)
    
    # Register blueprints
    from .blueprints.auth import auth as auth_blueprint
    from .blueprints.data import data as data_blueprint
    from .blueprints.visual import visual as visual_blueprint
    
    app.register_blueprint(auth_blueprint)
    app.register_blueprint(data_blueprint)
    app.register_blueprint(visual_blueprint)
    
    # Register error handlers
    from .errors import register_error_handlers
    register_error_handlers(app)
    
    # Register CLI commands
    from .cli import register_commands
    register_commands(app)
    
    # Import socket event handlers
    from . import socket_events

    # Add Caching configuration
    app.config['CACHE_TYPE'] = 'SimpleCache'  # In-memory cache
    app.config['CACHE_DEFAULT_TIMEOUT'] = 300  # 300 seconds = 5 minutes
    cache.init_app(app)
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('visual.index'))
        else:
            return redirect(url_for('visual.welcome'))

    return app