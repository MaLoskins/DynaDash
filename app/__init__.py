import os
import logging
from logging.handlers import RotatingFileHandler
from flask import Flask, redirect, url_for, request, current_app as flask_current_app_proxy
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect, generate_csrf
from flask_limiter import Limiter
from flask_limiter.util import get_remote_address
from flask_caching import Cache

from .models import db, User
from config import config
from .services import claude_service

# Initialize extensions
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

socketio = SocketIO()
csrf = CSRFProtect()
migrate = Migrate()
limiter = Limiter(key_func=get_remote_address, default_limits=["200 per day", "50 per hour"])
cache = Cache()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])

    db.init_app(app) 
    login_manager.init_app(app)
    socketio.init_app(app, async_mode=app.config.get('SOCKETIO_ASYNC_MODE', 'threading'), cors_allowed_origins=app.config.get('CORS_ALLOWED_ORIGINS', '*'))
    csrf.init_app(app)
    migrate.init_app(app, db)
    limiter.init_app(app)
    
    claude_service.init_app(app)

    app.logger.handlers.clear()
    app.logger.propagate = False

    if app.debug or app.testing:
        app.logger.setLevel(logging.DEBUG)
        app.logger.info(f"DynaDash starting in {config_name} mode (DEBUG={app.debug}, TESTING={app.testing})")
    else:
        logs_dir_config = app.config.get('LOGS_DIR')
        if logs_dir_config and os.path.isabs(logs_dir_config):
            logs_dir = logs_dir_config
        elif logs_dir_config: # Relative path from instance
             logs_dir = os.path.join(app.instance_path, logs_dir_config)
        else: # Default to 'logs' directory at project root (one level above app package)
            logs_dir = os.path.join(os.path.dirname(app.root_path), 'logs')


        if not os.path.exists(logs_dir):
            os.makedirs(logs_dir, exist_ok=True)
        
        log_file_path = os.path.join(logs_dir, app.config.get('LOG_FILE_NAME', 'dynadash_prod.log'))
        
        file_handler = RotatingFileHandler(
            log_file_path, 
            maxBytes=app.config.get('LOG_FILE_MAX_BYTES', 10*1024*1024),
            backupCount=app.config.get('LOG_FILE_BACKUP_COUNT', 5)
        )
        file_handler.setFormatter(logging.Formatter(
            '%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]'
        ))
        file_handler.setLevel(logging.INFO)
        app.logger.addHandler(file_handler)
        app.logger.setLevel(logging.INFO)
        app.logger.info(f"DynaDash starting in {config_name} mode.")

    @app.before_request
    def log_request_info():
        if not request.path.startswith('/static/'):
            app.logger.info( # Use app.logger here
                f'{request.method} {request.path} from {request.remote_addr} '
                f'user={getattr(current_user, "id", "anonymous")}'
            )
    
    upload_folder_path = app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.isabs(upload_folder_path):
        upload_folder_path = os.path.join(app.instance_path, upload_folder_path) 
    
    if not os.path.exists(os.path.dirname(upload_folder_path)):
         os.makedirs(os.path.dirname(upload_folder_path), exist_ok=True)
    os.makedirs(upload_folder_path, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder_path

    from .blueprints.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    # Data Blueprint Registration (handle potential absence)
    data_blueprint_registered = False
    try:
        from .blueprints.data import data as data_blueprint
        app.register_blueprint(data_blueprint)
        app.logger.info("Data blueprint registered successfully.")
        data_blueprint_registered = True
    except ImportError:
        app.logger.warning("Data blueprint (app.blueprints.data) not found or could not be imported. Related routes will not be available.")
    except Exception as e:
        app.logger.error(f"Error registering data blueprint: {e}", exc_info=True)

    from .blueprints.visual import visual as visual_blueprint
    app.register_blueprint(visual_blueprint)
    
    from .errors import register_error_handlers
    register_error_handlers(app)
    
    from .cli import register_commands
    register_commands(app)
    
    from . import socket_events

    app.config.setdefault('CACHE_TYPE', 'SimpleCache') 
    app.config.setdefault('CACHE_DEFAULT_TIMEOUT', 300)
    cache.init_app(app)
    
    @app.route('/')
    def index_route(): 
        if current_user.is_authenticated:
            return redirect(url_for('visual.index'))
        else:
            return redirect(url_for('visual.welcome'))
        
    @app.context_processor
    def utility_processor():
        def data_blueprint_exists_and_has_route(route_name):
            if not data_blueprint_registered:
                return False
            # Check if the specific route exists on the data blueprint
            # This requires the blueprint to be imported and checked,
            # or rely on url_for to raise an error if not found,
            # which we are trying to avoid in the template directly.
            # A simple check for registration is a good first step.
            # For a more precise check, you'd need to inspect app.url_map
            # or maintain a list of expected routes.
            # For now, just checking registration status.
            # To check specific endpoint: f"data.{route_name}" in app.view_functions
            return f"data.{route_name}" in app.view_functions

        return dict(
            csrf_token=generate_csrf,
            data_blueprint_exists_and_has_route=data_blueprint_exists_and_has_route,
            # Make flask_current_app_proxy available to templates as current_app
            current_app=flask_current_app_proxy
        )

    return app