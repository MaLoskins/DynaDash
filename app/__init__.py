import os
from flask import Flask, redirect, url_for
from flask_login import LoginManager, current_user
from flask_socketio import SocketIO
from flask_migrate import Migrate
from flask_wtf.csrf import CSRFProtect

from .models import db, User
from config import config

# Initialize extensions
login_manager = LoginManager()
login_manager.login_view = 'auth.login'
login_manager.login_message = 'Please log in to access this page.'

socketio = SocketIO()
csrf = CSRFProtect()
migrate = Migrate()

@login_manager.user_loader
def load_user(user_id):
    """Load user by ID."""
    return User.query.get(int(user_id))

def create_app(config_name='default'):
    """Create and configure the Flask application."""
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
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
    
    @app.route('/')
    def index():
        if current_user.is_authenticated:
            return redirect(url_for('visual.index'))
        else:
            return redirect(url_for('visual.welcome'))

    return app