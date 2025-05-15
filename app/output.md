# CODEBASE

## Directory Tree:

### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app

```
/mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app
├── __init__.py
├── blueprints/
│   ├── .gitkeep
│   ├── __init__.py
│   ├── auth/
│   │   ├── .gitkeep
│   │   ├── __init__.py
│   │   ├── forms.py
│   │   └── routes.py
│   └── visual/
│       ├── .gitkeep
│       ├── __init__.py
│       ├── forms.py
│       └── routes.py
├── cli.py
├── errors.py
├── models/
│   ├── .gitkeep
│   └── __init__.py
├── services/
│   ├── .gitkeep
│   ├── __init__.py
│   ├── claude_client.py
│   └── data_processor.py
├── socket_events.py
├── static/
│   ├── .gitkeep
│   ├── css/
│   │   ├── .gitkeep
│   │   └── main.css
│   ├── images/
│   │   └── .gitkeep
│   └── js/
│       ├── .gitkeep
│       ├── common.js
│       ├── dashboard_renderer.js
│       ├── profile.js
│       ├── upload.js
│       ├── view.js
│       └── visual.js
└── templates/
    ├── .gitkeep
    ├── auth/
    │   ├── .gitkeep
    │   ├── change_password.html
    │   ├── login.html
    │   ├── profile.html
    │   └── register.html
    ├── errors/
    │   ├── 400.html
    │   ├── 401.html
    │   ├── 403.html
    │   ├── 404.html
    │   ├── 500.html
    │   └── base_error.html
    ├── shared/
    │   ├── .gitkeep
    │   ├── base.html
    │   ├── error.html
    │   └── index.html
    └── visual/
        ├── .gitkeep
        ├── generate.html
        ├── index.html
        ├── share.html
        ├── view.html
        └── welcome.html
```

## Code Files


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/__init__.py

```
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
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/blueprints/.gitkeep

```
# This file is intentionally left empty to ensure the blueprints directory is included in the Git repository.
# The blueprints directory is used to store Flask blueprints for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/blueprints/__init__.py

```
# This file is intentionally left empty to make the directory a Python package.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/blueprints/auth/.gitkeep

```
# This file is intentionally left empty to ensure the auth directory is included in the Git repository.
# The auth directory is used to store authentication-related Flask blueprints for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/blueprints/auth/__init__.py

```
from flask import Blueprint

auth = Blueprint('auth', __name__, url_prefix='/auth')

from . import routes
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/blueprints/auth/forms.py

```
from flask_wtf import FlaskForm
from wtforms import StringField, PasswordField, BooleanField, SubmitField
from wtforms.validators import DataRequired, Length, Email, EqualTo, ValidationError
from ...models import User
from werkzeug.security import check_password_hash
from flask_login import current_user

class LoginForm(FlaskForm):
    """Form for user login."""
    email = StringField('Email', validators=[
        DataRequired(),
        Email()
    ])
    password = PasswordField('Password', validators=[
        DataRequired()
    ])
    remember_me = BooleanField('Remember Me')
    submit = SubmitField('Log In')

class RegistrationForm(FlaskForm):
    """Form for user registration."""
    name = StringField('Name', validators=[
        DataRequired(),
        Length(min=2, max=64)
    ])
    email = StringField('Email', validators=[
        DataRequired(),
        Email(),
        Length(max=120)
    ])
    password = PasswordField('Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    confirm_password = PasswordField('Confirm Password', validators=[
        DataRequired(),
        EqualTo('password', message='Passwords must match.')
    ])
    submit = SubmitField('Register')
    
    def validate_email(self, email):
        """Validate that the email is not already registered."""
        user = User.query.filter_by(email=email.data).first()
        if user:
            raise ValidationError('Email already registered. Please use a different email or log in.')

class ChangePasswordForm(FlaskForm):
    """Form for changing password."""
    current_password = PasswordField('Current Password', validators=[
        DataRequired()
    ])
    new_password = PasswordField('New Password', validators=[
        DataRequired(),
        Length(min=8, message='Password must be at least 8 characters long.')
    ])
    confirm_new_password = PasswordField('Confirm New Password', validators=[
        DataRequired(),
        EqualTo('new_password', message='Passwords must match.')
    ])
    submit = SubmitField('Change Password')

    def validate_new_password(self, new_password_field):
        """Custom validator to check if the new password is the same as the old one."""

        if current_user and hasattr(current_user, 'password_hash') and current_user.password_hash:

            if check_password_hash(current_user.password_hash, new_password_field.data):
   
                raise ValidationError('New password cannot be the same as your current password. Please choose a different password.')
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/blueprints/auth/routes.py

```
from flask import render_template, redirect, url_for, flash, request, jsonify, g
from flask_login import login_user, logout_user, login_required, current_user
from . import auth
from .forms import LoginForm, RegistrationForm, ChangePasswordForm
from ...models import db, User


@auth.route('/login', methods=['GET', 'POST'])
def login():
    """Handle user login."""
    if current_user.is_authenticated:
        return redirect(url_for('visual.index'))
    
    form = LoginForm()
    if form.validate_on_submit():
        user = User.query.filter_by(email=form.email.data).first()
        if user is not None and user.verify_password(form.password.data):
            login_user(user, remember=form.remember_me.data)
            next_page = request.args.get('next')
            if next_page is None or not next_page.startswith('/'):
                next_page = url_for('visual.index')
            return redirect(next_page)
        flash('Invalid email or password.', 'danger')
    
    return render_template('auth/login.html', title='Login', form=form)

@auth.route('/logout')
@login_required
def logout():
    """Handle user logout."""
    logout_user()
    flash('You have been logged out.', 'success')
    return redirect(url_for('auth.login'))

@auth.route('/register', methods=['GET', 'POST'])
def register():
    """Handle user registration."""
    if current_user.is_authenticated:
        return redirect(url_for('visual.index'))
    
    form = RegistrationForm()
    if form.validate_on_submit():
        # Create new user
        user = User(
            name=form.name.data,
            email=form.email.data,
            password=form.password.data
        )
        db.session.add(user)
        db.session.commit()
        flash('Your account has been created! You can now log in.', 'success')
        return redirect(url_for('auth.login'))
    
    return render_template('auth/register.html', title='Register', form=form)

@auth.route('/profile', methods=['GET'])
@login_required
def profile():
    """Display user profile."""
    return render_template('auth/profile.html', title='Profile')

@auth.route('/change-password', methods=['GET', 'POST'])
@login_required
def change_password():
    """Handle password change."""
    form = ChangePasswordForm()
    if form.validate_on_submit():
        if current_user.verify_password(form.current_password.data):
            current_user.password = form.new_password.data
            db.session.commit()
            flash('Your password has been updated!', 'success')
            return redirect(url_for('auth.profile'))
        else:
            flash('Current password is incorrect.', 'danger')
    
    return render_template('auth/change_password.html', title='Change Password', form=form)

@auth.route('/delete-account', methods=['POST'])
@login_required
def delete_account():
    """Allow the current user to permanently delete their account."""
    user = current_user

    # Delete all datasets and visualisations associated with the user
    from ...models import Dataset, Visualisation, Share

    Share.query.filter((Share.owner_id == user.id) | (Share.target_id == user.id)).delete()
    datasets = Dataset.query.filter_by(user_id=user.id).all()
    for dataset in datasets:
        Visualisation.query.filter_by(dataset_id=dataset.id).delete()
        db.session.delete(dataset)

    db.session.delete(user)
    db.session.commit()

    logout_user()
    flash('Your account has been deleted.', 'info')
    return redirect(url_for('visual.welcome'))

# API Routes

@auth.route('/api/v1/login', methods=['POST'])
def api_login():
    """API endpoint for user login."""
    data = request.get_json()
    if not data:
        return jsonify(error='No data provided'), 400
    
    email = data.get('email')
    password = data.get('password')
    
    if not email or not password:
        return jsonify(error='Email and password are required'), 400
    
    user = User.query.filter_by(email=email).first()
    if user is not None and user.verify_password(password):
        login_user(user)
        return jsonify(success=True, user_id=user.id, name=user.name)
    
    return jsonify(error='Invalid email or password'), 401

@auth.route('/api/v1/logout', methods=['POST'])
@login_required
def api_logout():
    """API endpoint for user logout."""
    logout_user()
    return jsonify(success=True)

@auth.route('/api/v1/register', methods=['POST'])
def api_register():
    """API endpoint for user registration."""
    data = request.get_json()
    if not data:
        return jsonify(error='No data provided'), 400
    
    name = data.get('name')
    email = data.get('email')
    password = data.get('password')
    
    if not name or not email or not password:
        return jsonify(error='Name, email, and password are required'), 400
    
    # Check if email is already registered
    if User.query.filter_by(email=email).first():
        return jsonify(error='Email already registered'), 400
    
    # Create new user
    user = User(name=name, email=email, password=password)
    db.session.add(user)
    db.session.commit()
    
    return jsonify(success=True, user_id=user.id)

@auth.route('/api/v1/user', methods=['GET'])
@login_required
def api_get_user():
    """API endpoint to get current user information."""
    return jsonify(
        id=current_user.id,
        name=current_user.name,
        email=current_user.email
    )

@auth.route('/api/v1/users', methods=['GET'])
@login_required
def api_get_users():
    """API endpoint to get all users (for sharing)."""
    users = User.query.filter(User.id != current_user.id).all()
    return jsonify(users=[
        {
            'id': user.id,
            'name': user.name,
            'email': user.email
        }
        for user in users
    ])
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/blueprints/visual/.gitkeep

```
# This file is intentionally left empty to ensure the visual directory is included in the Git repository.
# The visual directory is used to store visualization-related Flask blueprints for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/blueprints/visual/__init__.py

```
from flask import Blueprint

visual = Blueprint('visual', __name__, url_prefix='/visual')

from . import routes
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/blueprints/visual/forms.py

```
from flask_wtf import FlaskForm
from wtforms import StringField, TextAreaField, SelectField, SubmitField
from wtforms.validators import DataRequired, Length

class GenerateVisualisationForm(FlaskForm):
    """Form for generating a visualization."""
    title = StringField('Visualization Title', validators=[
        DataRequired(),
        Length(min=3, max=100)
    ])
    description = TextAreaField('Description (Optional)', validators=[
        Length(max=500)
    ])
    # Chart type selection removed; Claude now selects visualization type autonomously.
    submit = SubmitField('Generate Visualization')

class ShareVisualisationForm(FlaskForm):
    """Form for sharing a visualization with another user."""
    user_id = SelectField('Share with User', validators=[DataRequired()], coerce=int)
    submit = SubmitField('Share')
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/blueprints/visual/routes.py

```
from flask import render_template, redirect, url_for, flash, request, jsonify, current_app
from flask_login import login_required, current_user
from markupsafe import Markup
from . import visual
from ...models import db, Dataset, Visualisation, Share, User # db import might be redundant if not used directly
from .forms import GenerateVisualisationForm, ShareVisualisationForm
# from ...services.claude_client import ClaudeClient # No longer importing the class directly
from ...services import claude_service # Import the initialized instance
from ... import cache, socketio 
import traceback
import re
import os 
import pandas as pd 
import json 
import anthropic # For specific API error handling


# claude_client = ClaudeClient() # REMOVE THIS LINE - use claude_service instance

# Helper function to clean/prepare HTML template from Claude (consolidated logic)
# This function can be moved to a utils file if it grows or is used elsewhere
def prepare_dashboard_template_html(html_content):
    """
    Clean and validate the dashboard HTML TEMPLATE to ensure it's suitable for iframe display
    and later data injection.
    """
    if not html_content:
        current_app.logger.warning("Empty HTML content provided to prepare_dashboard_template_html")
        return "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Error</title></head><body><h2>No dashboard content template available.</h2></body></html>"

    # Ensure the HTML starts with doctype
    if not html_content.strip().lower().startswith("<!doctype html"):
        html_content = "<!DOCTYPE html>\n" + html_content
    
    # Basic HTML structure checks
    if "<html" not in html_content.lower():
        html_content = html_content.replace("<!DOCTYPE html>", "<!DOCTYPE html>\n<html lang='en'>", 1)
        if "</html>" not in html_content.lower(): html_content += "\n</html>"
    
    head_start_idx = html_content.lower().find("<head>")
    head_end_idx = html_content.lower().find("</head>")

    if head_start_idx == -1: 
        html_tag_end = html_content.lower().find("<html>")
        insert_pos = html_tag_end + len("<html>") if html_tag_end != -1 else len("<!DOCTYPE html>")
        html_content = html_content[:insert_pos] + "\n<head><meta charset=\"UTF-8\"><title>Dashboard</title></head>\n" + html_content[insert_pos:]
        head_start_idx = html_content.lower().find("<head>") 
        head_end_idx = html_content.lower().find("</head>")

    if head_start_idx != -1 and "<meta charset" not in html_content[head_start_idx:head_end_idx if head_end_idx!=-1 else len(html_content)].lower():
        html_content = html_content[:head_start_idx+6] + "<meta charset=\"UTF-8\">\n" + html_content[head_start_idx+6:]
        head_end_idx = html_content.lower().find("</head>") 

    if "<body" not in html_content.lower():
        if head_end_idx != -1:
            html_content = html_content[:head_end_idx+7] + "\n<body>\n</body>" + html_content[head_end_idx+7:]
        elif "</html>" in html_content.lower():
            idx = html_content.lower().find("</html>")
            html_content = html_content[:idx] + "\n<body>\n</body>\n" + html_content[idx:]
        else:
            html_content += "\n<body>\n</body>"

    current_head_content = html_content[head_start_idx:head_end_idx if head_end_idx!=-1 else len(html_content)]

    if head_start_idx != -1 and '<meta name="viewport"' not in current_head_content.lower():
        viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0, maximum-scale=1.0, user-scalable=no">\n'
        html_content = html_content[:head_start_idx+6] + viewport_meta + html_content[head_start_idx+6:]
        head_end_idx = html_content.lower().find("</head>")

    if head_start_idx != -1 and '<meta http-equiv="Content-Security-Policy"' not in current_head_content:
        csp_tag = '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' \'unsafe-inline\' https://cdn.jsdelivr.net https://d3js.org; style-src \'self\' \'unsafe-inline\' https://cdn.jsdelivr.net; img-src \'self\' data: blob:; connect-src \'self\'; font-src \'self\' https://cdn.jsdelivr.net;">\n'
        html_content = html_content[:head_start_idx+6] + csp_tag + html_content[head_start_idx+6:]
        head_end_idx = html_content.lower().find("</head>")
    
    if head_end_idx != -1: 
        responsive_css_script = """
<style>
    html, body { width: 100% !important; height: 100% !important; margin: 0 !important; padding: 0 !important; overflow-x: hidden !important; box-sizing: border-box !important; }
    *, *:before, *:after { box-sizing: inherit !important; }
    #dashboard-content, #root, #app, main, .main, .dashboard, .dashboard-main,
    .container, .container-fluid, .row, .grid, div[class*="container"], section, article, .card, .panel, .box {
        width: 100% !important; max-width: 100% !important; margin-left: auto !important; margin-right: auto !important;
    }
    canvas, svg, .chart, div[class*="chart"] { width: 100% !important; max-width: 100% !important; height: auto !important; }
    img, table { max-width: 100% !important; height: auto !important; }
</style>
"""
        html_content = html_content[:head_end_idx] + responsive_css_script + html_content[head_end_idx:]

    if "console.error('Dashboard error:'" not in html_content:
        error_handling_script = """
<script>
    window.addEventListener('error', function(event) {
        console.error('Dashboard error:', event.message, 'at', event.filename, ':', event.lineno);
        var errorDisplay = document.getElementById('dynadashInternalErrorDisplay');
        if (!errorDisplay && document.body) {
            errorDisplay = document.createElement('div');
            errorDisplay.id = 'dynadashInternalErrorDisplay';
            errorDisplay.style.cssText = 'position:fixed;top:5px;left:5px;right:5px;padding:10px;background:rgba(220,50,50,0.9);color:white;border-radius:4px;z-index:20000;font-family:sans-serif;font-size:14px;';
            document.body.insertBefore(errorDisplay, document.body.firstChild);
        }
        if(errorDisplay) errorDisplay.textContent = 'Dashboard Error: ' + event.message + ' (in ' + (event.filename || 'inline script') + ':' + event.lineno + ')';
    });
    document.addEventListener('DOMContentLoaded', function() {
        if (typeof window.dynadashData === 'undefined' || window.dynadashData === null || (Array.isArray(window.dynadashData) && window.dynadashData.length === 0)) {
            console.warn('window.dynadashData is not defined or is empty. Dashboard might not render correctly.');
            var dataWarningDiv = document.getElementById('dynadashDataWarningDisplay');
            if(!dataWarningDiv && document.body) {
                dataWarningDiv = document.createElement('div');
                dataWarningDiv.id = 'dynadashDataWarningDisplay';
                dataWarningDiv.style.cssText = 'padding:10px;background:rgba(255,220,50,0.8);color:black;text-align:center;font-family:sans-serif;font-size:14px;';
                dataWarningDiv.textContent = 'Notice: Data for this dashboard (window.dynadashData) was not loaded or is empty. Visualizations may not appear as expected.';
                document.body.insertBefore(dataWarningDiv, document.body.firstChild);
            }
        }
        setTimeout(function() {
            if (typeof Chart !== 'undefined' && typeof window.dynadashData !== 'undefined') {
                var canvases = document.querySelectorAll('canvas');
                canvases.forEach(function(canvas) {
                    try {
                        var chartInstance = Chart.getChart(canvas); 
                        if (chartInstance) { chartInstance.update('none'); } 
                    } catch(e) { console.warn('Could not update chart on canvas ' + (canvas.id || '(no id)') + ':', e); }
                });
            }
        }, 1200);
    });
</script>
"""
        body_end_idx = html_content.lower().rfind('</body>')
        if body_end_idx != -1:
            html_content = html_content[:body_end_idx] + error_handling_script + html_content[body_end_idx:]
        else:
            html_content += error_handling_script

    return html_content


@visual.route('/welcome')
def welcome():
    return render_template('visual/welcome.html', title='Welcome')

@visual.route('/index')
@login_required
def index():
    """Display the visualizations gallery."""
    user_visualisations = Visualisation.query.join(Dataset).filter(
        Dataset.user_id == current_user.id
    ).order_by(Visualisation.created_at.desc()).all()
    
    shared_visualisations_query = db.session.query(Visualisation, User.name.label("owner_name")).\
        select_from(Share).\
        join(Visualisation, Share.object_id == Visualisation.id).\
        join(Dataset, Visualisation.dataset_id == Dataset.id).\
        join(User, Dataset.user_id == User.id).\
        filter(
            Share.target_id == current_user.id,
            Share.object_type == 'visualisation'
        ).order_by(Visualisation.created_at.desc())
    
    shared_visualisations_list = [] # Renamed to avoid conflict
    for vis, owner_name in shared_visualisations_query.all():
        shared_visualisations_list.append({
            'id': vis.id,
            'title': vis.title,
            'description': vis.description,
            'created_at': vis.created_at,
            'dataset_filename': vis.dataset.original_filename, 
            'owner_name': owner_name
        })

    return render_template(
        'visual/index.html',
        title='My Dashboards',
        user_visualisations=user_visualisations,
        shared_visualisations=shared_visualisations_list # Use the new list name
    )

@visual.route('/generate/<int:dataset_id>', methods=['GET', 'POST'])
@login_required
def generate(dataset_id):
    """Generate dashboard visualization TEMPLATE for a dataset."""
    dataset = Dataset.query.get_or_404(dataset_id)
    
    # Ensure 'data.index' resolves correctly, otherwise use a known fallback
    data_index_url = url_for('visual.index') # Default fallback
    try:
        data_index_url = url_for('data.index')
    except Exception: # pylint: disable=broad-except
        current_app.logger.warning("'data.index' endpoint not found, falling back to 'visual.index' for redirect.")


    if dataset.user_id != current_user.id: 
        flash('You must own the dataset to generate a new visualization from it.', 'danger')
        return redirect(data_index_url) 
    
    form = GenerateVisualisationForm()
    if form.validate_on_submit():
        room_id = f"user_{current_user.id}" # Define room_id outside try for except block
        try:
            socketio.emit('progress_update', {'percent': 0, 'message': 'Starting dashboard generation...'}, room=room_id)
            current_app.logger.info(f"Starting dashboard template generation for dataset ID: {dataset.id}, title: {form.title.data}")
            
            socketio.emit('progress_update', {'percent': 10, 'message': 'Analyzing dataset structure...'}, room=room_id)
            
            # Use the imported claude_service instance
            dashboard_html_template = claude_service.generate_dashboard(
                dataset.id, 
                form.title.data, 
                form.description.data
            )
            
            prepared_template = prepare_dashboard_template_html(dashboard_html_template) 
            
            socketio.emit('progress_update', {'percent': 90, 'message': 'Dashboard template generated, saving...'}, room=room_id)
            
            visualisation = Visualisation(
                dataset_id=dataset.id,
                title=form.title.data,
                description=form.description.data,
                spec=prepared_template 
            )
            db.session.add(visualisation)
            db.session.commit()
            
            socketio.emit('progress_update', {'percent': 100, 'message': 'Dashboard saved! Redirecting...'}, room=room_id)
            socketio.emit('processing_complete', {'redirect_url': url_for('visual.view', id=visualisation.id)}, room=room_id)
            
            current_app.logger.info(f"Dashboard template generation completed for dataset ID: {dataset.id}")
            flash('Dashboard generated successfully! You can now view it.', 'success')
            return redirect(url_for('visual.view', id=visualisation.id))
            
        except anthropic.APIError as api_err: 
            current_app.logger.error(f"Claude API Error during dashboard generation: {str(api_err)}", exc_info=True)
            socketio.emit('processing_error', {'message': f'Claude API Error: {str(api_err)}'}, room=room_id)
            flash(f'Error communicating with Claude API: {str(api_err)}', 'danger')
        except Exception as e:
            current_app.logger.error(f"Unexpected error in dashboard generation: {str(e)}", exc_info=True)
            socketio.emit('processing_error', {'message': f'Unexpected error: {str(e)}'}, room=room_id)
            flash(f'An unexpected error occurred: {str(e)}', 'danger')
    
    return render_template(
        'visual/generate.html',
        title='Generate Dashboard',
        dataset=dataset,
        form=form
    )

@visual.route('/view/<int:id>')
@login_required
def view(id):
    """View a visualization by injecting data into its template."""
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get_or_404(visualisation.dataset_id)
    
    can_view = False
    if dataset.user_id == current_user.id or dataset.is_public:
        can_view = True
    else:
        share_record = Share.query.filter_by( # Renamed to avoid conflict
            object_type='visualisation', object_id=id, target_id=current_user.id
        ).first()
        if share_record: # Check if a record was found
            can_view = True
    
    if not can_view:
        flash('You do not have permission to view this dashboard.', 'danger')
        return redirect(url_for('visual.index'))

    actual_dataset_json_for_js = "[]" 
    dashboard_template_html_content = "" # Renamed for clarity

    if visualisation.spec:
        try:
            file_path = dataset.file_path
            if not os.path.exists(file_path):
                current_app.logger.error(f"Dataset file {file_path} not found for visualization {id}.")
                flash('Dataset file is missing. Cannot display dashboard.', 'danger')
            else:
                if dataset.file_type.lower() == 'csv':
                    df = pd.read_csv(file_path)
                elif dataset.file_type.lower() == 'json':
                    df = pd.read_json(file_path)
                else:
                    current_app.logger.error(f"Unsupported dataset type {dataset.file_type} for viz {id}.")
                    flash(f"Unsupported dataset type: {dataset.file_type}", 'danger')
                    df = pd.DataFrame()

                actual_dataset_for_js = df.to_dict(orient='records')
                actual_dataset_json_for_js = json.dumps(actual_dataset_for_js)
            
            dashboard_template_html_content = Markup(visualisation.spec) # Spec is the template

        except Exception as data_err:
            current_app.logger.error(f"Error reading dataset content for visualization {id}: {str(data_err)}", exc_info=True)
            flash('Error loading data for the dashboard. Some elements may not display correctly.', 'warning')
            dashboard_template_html_content = Markup(visualisation.spec) # Still pass template even if data fails
            
    else:
        current_app.logger.warning(f"Empty visualization spec for ID: {id}")
        flash('This dashboard has no content template. It may have been incorrectly generated.', 'warning')
        dashboard_template_html_content = Markup('<html><body><div class="p-4 text-center text-gray-500">No dashboard template available.</div></body></html>')

    return render_template(
        'visual/view.html',
        title=visualisation.title,
        visualisation=visualisation,
        dashboard_template_html=dashboard_template_html_content,
        actual_dataset_json=actual_dataset_json_for_js, 
        dataset=dataset, 
        debug=current_app.debug 
    )

@visual.route('/share/<int:id>', methods=['GET', 'POST'])
@login_required
def share(id):
    """Share a visualization with other users."""
    visualisation = Visualisation.query.get_or_404(id)
    if visualisation.dataset.user_id != current_user.id:
        flash('You can only share dashboards that you own.', 'danger')
        return redirect(url_for('visual.index'))
    
    form = ShareVisualisationForm()
    users = User.query.filter(User.id != current_user.id).order_by(User.name).all()
    form.user_id.choices = [(user.id, f"{user.name} ({user.email})") for user in users]
    
    if form.validate_on_submit():
        target_user_id = form.user_id.data
        target_user = User.query.get(target_user_id)

        if not target_user:
            flash('Selected user not found.', 'danger')
        else:
            existing_share = Share.query.filter_by(
                owner_id=current_user.id,
                target_id=target_user_id,
                object_type='visualisation',
                object_id=id
            ).first()
            
            if existing_share:
                flash(f'This dashboard is already shared with {target_user.name}.', 'warning')
            else:
                new_share = Share( # Renamed to avoid conflict
                    owner_id=current_user.id,
                    target_id=target_user_id,
                    object_type='visualisation',
                    object_id=id
                )
                db.session.add(new_share)
                db.session.commit()
                flash(f'Dashboard shared successfully with {target_user.name}!', 'success')
        return redirect(url_for('visual.share', id=id))
    
    shared_with_users = db.session.query(User).join(Share, Share.target_id == User.id).filter(
        Share.owner_id == current_user.id,
        Share.object_type == 'visualisation',
        Share.object_id == id
    ).all()
    
    return render_template(
        'visual/share.html',
        title=f'Share: {visualisation.title}',
        visualisation=visualisation,
        dataset=visualisation.dataset, 
        form=form,
        shared_with_users=shared_with_users # Renamed from shared_with
    )

@visual.route('/unshare/<int:id>/<int:user_id>', methods=['POST'])
@login_required
def unshare(id, user_id):
    visualisation = Visualisation.query.get_or_404(id)
    if visualisation.dataset.user_id != current_user.id: 
        flash('You can only manage sharing for dashboards that you own.', 'danger')
        return redirect(url_for('visual.index'))
    
    share_to_delete = Share.query.filter_by(
        owner_id=current_user.id,
        target_id=user_id,
        object_type='visualisation',
        object_id=id
    ).first()
    
    if share_to_delete:
        user_removed = User.query.get(user_id)
        db.session.delete(share_to_delete)
        db.session.commit()
        flash(f'Sharing access removed successfully for {user_removed.name if user_removed else "user"}.', 'success')
    else:
        flash('Share record not found or you are not the owner.', 'warning')
    
    return redirect(url_for('visual.share', id=id))

@visual.route('/delete/<int:id>', methods=['POST'])
@login_required
def delete(id):
    visualisation = Visualisation.query.get_or_404(id)
    if visualisation.dataset.user_id != current_user.id: 
        flash('You can only delete dashboards that you own.', 'danger')
        return redirect(url_for('visual.index'))
    
    Share.query.filter_by(object_type='visualisation', object_id=id).delete(synchronize_session='fetch')
    db.session.delete(visualisation)
    db.session.commit()
    
    flash('Dashboard deleted successfully!', 'success')
    return redirect(url_for('visual.index'))

# API Routes

@visual.route('/api/v1/visualisations', methods=['GET'])
@login_required
@cache.cached(timeout=60) 
def api_get_visualisations():
    visualisations = Visualisation.query.join(Dataset).filter(
        Dataset.user_id == current_user.id
    ).order_by(Visualisation.created_at.desc()).all()
    
    result = [{
        'id': vis.id, 'title': vis.title, 'description': vis.description,
        'dataset_name': vis.dataset.original_filename, 
        'created_at': vis.created_at.isoformat()
    } for vis in visualisations]
    return jsonify(visualisations=result)

@visual.route('/api/v1/shared-visualisations', methods=['GET'])
@login_required
@cache.cached(timeout=60)
def api_get_shared_visualisations():
    shared_visualisations_data = db.session.query( # Renamed
            Visualisation, User.name.label("owner_name")
        ).\
        select_from(Share).\
        join(Visualisation, Share.object_id == Visualisation.id).\
        join(Dataset, Visualisation.dataset_id == Dataset.id).\
        join(User, Dataset.user_id == User.id).\
        filter(
            Share.target_id == current_user.id,
            Share.object_type == 'visualisation'
        ).order_by(Visualisation.created_at.desc()).all()
    
    result = [{
        'id': vis.id, 'title': vis.title, 'description': vis.description,
        'dataset_name': vis.dataset.original_filename,
        'created_at': vis.created_at.isoformat(),
        'owner_name': owner_name
    } for vis, owner_name in shared_visualisations_data] # Use renamed variable
    return jsonify(visualisations=result)


@visual.route('/api/v1/visualisations/<int:id>', methods=['GET'])
@login_required
@cache.cached(timeout=60) 
def api_get_visualisation(id):
    visualisation = Visualisation.query.get_or_404(id)
    dataset = Dataset.query.get_or_404(visualisation.dataset_id)
    
    can_view = False
    if dataset.user_id == current_user.id or dataset.is_public:
        can_view = True
    else:
        share_record_api = Share.query.filter_by(object_type='visualisation', object_id=id, target_id=current_user.id).first() # Renamed
        if share_record_api: can_view = True # Use renamed variable
    
    if not can_view:
        return jsonify(error='Permission denied'), 403

    actual_data_for_js = []
    try:
        file_path = dataset.file_path
        if os.path.exists(file_path):
            if dataset.file_type.lower() == 'csv':
                df = pd.read_csv(file_path)
            elif dataset.file_type.lower() == 'json':
                df = pd.read_json(file_path)
            else: df = pd.DataFrame()
            actual_data_for_js = df.to_dict(orient='records')
        else:
             current_app.logger.warning(f"API: Dataset file {file_path} not found for viz {id}")
    except Exception as e:
        current_app.logger.error(f"API: Error loading data for viz {id}: {e}", exc_info=True)

    return jsonify(
        id=visualisation.id,
        title=visualisation.title,
        description=visualisation.description,
        dashboard_template_spec=visualisation.spec, 
        actual_dataset=actual_data_for_js, 
        dataset_id=visualisation.dataset_id,
        dataset_filename=dataset.original_filename,
        created_at=visualisation.created_at.isoformat()
    )
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/cli.py

```
import click
from flask.cli import with_appcontext
from .models import db, User, Dataset, Visualisation, Share
import os
import random
from datetime import datetime, timedelta
from werkzeug.security import generate_password_hash

def register_commands(app):
    """Register CLI commands with the application."""
    
    @app.cli.command('init-db')
    @with_appcontext
    def init_db_command():
        """Initialize the database."""
        db.create_all()
        click.echo('Initialized the database.')
    
    @app.cli.command('drop-db')
    @with_appcontext
    def drop_db_command():
        """Drop all tables in the database."""
        if click.confirm('Are you sure you want to drop all tables?'):
            db.drop_all()
            click.echo('Dropped all tables.')
    
    @app.cli.command('seed-db')
    @with_appcontext
    def seed_db_command():
        """Seed the database with sample data."""
        # Create users
        users = [
            User(name='Admin User', email='admin@example.com', password='password'),
            User(name='Test User', email='test@example.com', password='password'),
            User(name='Demo User', email='demo@example.com', password='password')
        ]
        db.session.add_all(users)
        db.session.commit()
        
        # Create datasets
        datasets = []
        for i, user in enumerate(users):
            for j in range(3):  # 3 datasets per user
                dataset = Dataset(
                    user_id=user.id,
                    filename=f'dataset_{i}_{j}.csv',
                    original_filename=f'Sample Dataset {j+1}.csv',
                    file_path=f'/path/to/dataset_{i}_{j}.csv',
                    file_type='csv',
                    n_rows=random.randint(100, 1000),
                    n_columns=random.randint(5, 20),
                    is_public=(j == 0),  # First dataset is public
                    uploaded_at=datetime.utcnow() - timedelta(days=random.randint(1, 30))
                )
                datasets.append(dataset)
        
        db.session.add_all(datasets)
        db.session.commit()
        
        # Create visualisations
        visualisations = []
        for dataset in datasets:
            for j in range(2):  # 2 visualisations per dataset
                visualisation = Visualisation(
                    dataset_id=dataset.id,
                    title=f'Visualisation {j+1} for {dataset.original_filename}',
                    description=f'Sample visualisation {j+1} for {dataset.original_filename}',
                    spec=f'<div>Sample Visualisation {j+1} for {dataset.original_filename}</div>',
                    created_at=datetime.utcnow() - timedelta(days=random.randint(1, 15))
                )
                visualisations.append(visualisation)
        
        db.session.add_all(visualisations)
        db.session.commit()
        
        # Create shares
        shares = []
        for i, user in enumerate(users):
            for j, other_user in enumerate(users):
                if i != j:  # Don't share with self
                    # Share a dataset
                    user_datasets = Dataset.query.filter_by(user_id=user.id).all()
                    if user_datasets:
                        dataset = user_datasets[0]
                        share = Share(
                            owner_id=user.id,
                            target_id=other_user.id,
                            object_type='dataset',
                            object_id=dataset.id,
                            granted_at=datetime.utcnow() - timedelta(days=random.randint(1, 10))
                        )
                        shares.append(share)
                    
                    # Share a visualisation
                    user_visualisations = Visualisation.query.join(Dataset).filter(Dataset.user_id == user.id).all()
                    if user_visualisations:
                        visualisation = user_visualisations[0]
                        share = Share(
                            owner_id=user.id,
                            target_id=other_user.id,
                            object_type='visualisation',
                            object_id=visualisation.id,
                            granted_at=datetime.utcnow() - timedelta(days=random.randint(1, 10))
                        )
                        shares.append(share)
        
        db.session.add_all(shares)
        db.session.commit()
        
        click.echo(f'Seeded the database with {len(users)} users, {len(datasets)} datasets, {len(visualisations)} visualisations, and {len(shares)} shares.')
    
    @app.cli.command('create-user')
    @click.argument('name')
    @click.argument('email')
    @click.argument('password')
    @with_appcontext
    def create_user_command(name, email, password):
        """Create a new user."""
        user = User(name=name, email=email, password=password)
        db.session.add(user)
        db.session.commit()
        click.echo(f'Created user {name} with email {email}.')
    
    @app.cli.command('list-users')
    @with_appcontext
    def list_users_command():
        """List all users."""
        users = User.query.all()
        if not users:
            click.echo('No users found.')
            return
        
        click.echo('Users:')
        for user in users:
            click.echo(f'  {user.id}: {user.name} ({user.email})')
    
    @app.cli.command('backup-db')
    @click.argument('output_file', type=click.Path())
    @with_appcontext
    def backup_db_command(output_file):
        """Backup the database to a file."""
        import sqlite3
        import shutil
        
        # Get the database file path from the app config
        db_path = app.config['SQLALCHEMY_DATABASE_URI'].replace('sqlite:///', '')
        
        # Create the output directory if it doesn't exist
        output_dir = os.path.dirname(output_file)
        if output_dir and not os.path.exists(output_dir):
            os.makedirs(output_dir)
        
        # Copy the database file
        shutil.copy2(db_path, output_file)
        
        click.echo(f'Backed up database to {output_file}.')
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/errors.py

```
from flask import render_template, jsonify, request

def register_error_handlers(app):
    """Register error handlers for the application."""
    
    @app.errorhandler(400)
    def bad_request(e):
        """Handle 400 Bad Request errors."""
        if request.path.startswith('/api/'):
            return jsonify(error='Bad Request', message=str(e)), 400
        return render_template('errors/400.html', error=e), 400
    
    @app.errorhandler(401)
    def unauthorized(e):
        """Handle 401 Unauthorized errors."""
        if request.path.startswith('/api/'):
            return jsonify(error='Unauthorized', message=str(e)), 401
        return render_template('errors/401.html', error=e), 401
    
    @app.errorhandler(403)
    def forbidden(e):
        """Handle 403 Forbidden errors."""
        if request.path.startswith('/api/'):
            return jsonify(error='Forbidden', message=str(e)), 403
        return render_template('errors/403.html', error=e), 403
    
    @app.errorhandler(404)
    def page_not_found(e):
        """Handle 404 Not Found errors."""
        if request.path.startswith('/api/'):
            return jsonify(error='Not Found', message=str(e)), 404
        return render_template('errors/404.html', error=e), 404
    
    @app.errorhandler(405)
    def method_not_allowed(e):
        """Handle 405 Method Not Allowed errors."""
        if request.path.startswith('/api/'):
            return jsonify(error='Method Not Allowed', message=str(e)), 405
        return render_template('errors/405.html', error=e), 405
    
    @app.errorhandler(429)
    def too_many_requests(e):
        """Handle 429 Too Many Requests errors."""
        if request.path.startswith('/api/'):
            return jsonify(error='Too Many Requests', message=str(e)), 429
        return render_template('errors/429.html', error=e), 429
    
    @app.errorhandler(500)
    def internal_server_error(e):
        """Handle 500 Internal Server Error errors."""
        app.logger.error(f'Server Error: {e}')
        if request.path.startswith('/api/'):
            return jsonify(error='Internal Server Error', message=str(e)), 500
        return render_template('errors/500.html', error=e), 500
    
    @app.errorhandler(Exception)
    def unhandled_exception(e):
        """Handle unhandled exceptions."""
        app.logger.error(f'Unhandled Exception: {e}')
        if request.path.startswith('/api/'):
            return jsonify(error='Internal Server Error', message=str(e)), 500
        return render_template('errors/500.html', error=e), 500
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/models/.gitkeep

```
# This file is intentionally left empty to ensure the models directory is included in the Git repository.
# The models directory is used to store SQLAlchemy models for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/models/__init__.py

```
from datetime import datetime
from flask_sqlalchemy import SQLAlchemy
from flask_login import UserMixin
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy import event
from sqlalchemy.engine import Engine

# Enable SQLite foreign key support
@event.listens_for(Engine, "connect")
def enable_sqlite_foreign_keys(dbapi_connection, connection_record):
    if dbapi_connection.__class__.__module__.startswith('sqlite3'):
        cursor = dbapi_connection.cursor()
        cursor.execute("PRAGMA foreign_keys=ON")
        cursor.close()

# Initialize SQLAlchemy
db = SQLAlchemy()

class User(UserMixin, db.Model):
    """User model for authentication and user management."""
    __tablename__ = 'user'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(64), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    datasets = db.relationship('Dataset', backref='owner', lazy='dynamic', cascade='all, delete-orphan')
    owned_shares = db.relationship('Share', foreign_keys='Share.owner_id', backref='owner', lazy='dynamic')
    received_shares = db.relationship('Share', foreign_keys='Share.target_id', backref='target', lazy='dynamic')
    
    @property
    def password(self):
        """Prevent password from being accessed."""
        raise AttributeError('password is not a readable attribute')
    
    @password.setter
    def password(self, password):
        """Set password to a hashed password."""
        self.password_hash = generate_password_hash(password)
    
    def verify_password(self, password):
        """Check if password matches the hashed password."""
        return check_password_hash(self.password_hash, password)
    
    def __repr__(self):
        return f'<User {self.name}>'

class Dataset(db.Model):
    """Dataset model for storing uploaded datasets."""
    __tablename__ = 'dataset'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id', ondelete='CASCADE'), nullable=False)
    filename = db.Column(db.String(128), nullable=False)
    original_filename = db.Column(db.String(128), nullable=False)
    file_path = db.Column(db.String(256), nullable=False)
    file_type = db.Column(db.String(10), nullable=False)  # csv, json, etc.
    n_rows = db.Column(db.Integer, nullable=False)
    n_columns = db.Column(db.Integer, nullable=False)
    is_public = db.Column(db.Boolean, default=False)
    uploaded_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    visualisations = db.relationship('Visualisation', backref='dataset', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Dataset {self.filename}>'

class Visualisation(db.Model):
    """Visualisation model for storing generated visualisations."""
    __tablename__ = 'visualisation'
    
    id = db.Column(db.Integer, primary_key=True)
    dataset_id = db.Column(db.Integer, db.ForeignKey('dataset.id'), nullable=False)
    title = db.Column(db.String(128), nullable=False)
    description = db.Column(db.Text, nullable=True)
    spec = db.Column(db.Text, nullable=False)  # HTML/SVG/js snippet
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Visualisation {self.title}>'

class Share(db.Model):
    """Share model for managing access to datasets and visualisations."""
    __tablename__ = 'share'
    
    id = db.Column(db.Integer, primary_key=True)
    owner_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    target_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    object_type = db.Column(db.String(20), nullable=False)  # 'dataset' or 'visualisation'
    object_id = db.Column(db.Integer, nullable=False)
    granted_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<Share {self.object_type} {self.object_id} from {self.owner_id} to {self.target_id}>'
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/services/.gitkeep

```
# This file is intentionally left empty to ensure the services directory is included in the Git repository.
# The services directory is used to store service classes for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/services/__init__.py

```
# Import services for easier access
from .data_processor import DataProcessor
from .claude_client import ClaudeClient

# Instantiate services that need app context for configuration
claude_service = ClaudeClient()
# DataProcessor can be instantiated directly where needed if it doesn't require app-level config at init
# or you can instantiate it here too if you prefer:
# data_processor_service = DataProcessor()


__all__ = ['DataProcessor', 'claude_service'] # Make the instance available
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/services/claude_client.py

```
import os
import json
import time
import anthropic
from flask import current_app
import pandas as pd
from ..models import Dataset

class ClaudeClient:
    """Service for interacting with the Anthropic Claude API."""
    
    def __init__(self):
        """Initialize the Claude client with placeholders."""
        self.client = None
        # Reverted to your original model name as a default.
        # This should ideally be configured via ANTHROPIC_MODEL_NAME in .env
        self.model_name = "claude-3-7-sonnet-20250219" 
        self.api_key = None
        self.max_retries = 3
        self.retry_delay = 5 
        self.max_tokens_dashboard = 15000
        self.temperature_dashboard = 0.7
        self.max_tokens_analysis = 4000
        self.temperature_analysis = 0.5

    def init_app(self, app):
        """Initialize with application-specific configuration."""
        self.model_name = app.config.get("ANTHROPIC_MODEL_NAME", self.model_name)
        self.api_key = app.config.get('ANTHROPIC_API_KEY')
        self.max_retries = app.config.get("ANTHROPIC_MAX_RETRIES", self.max_retries)
        self.retry_delay = app.config.get("ANTHROPIC_RETRY_DELAY", self.retry_delay)
        self.max_tokens_dashboard = app.config.get("ANTHROPIC_MAX_TOKENS_DASHBOARD", self.max_tokens_dashboard)
        self.temperature_dashboard = app.config.get("ANTHROPIC_TEMPERATURE_DASHBOARD", self.temperature_dashboard)
        self.max_tokens_analysis = app.config.get("ANTHROPIC_MAX_TOKENS_ANALYSIS", self.max_tokens_analysis)
        self.temperature_analysis = app.config.get("ANTHROPIC_TEMPERATURE_ANALYSIS", self.temperature_analysis)

        if not self.api_key:
            app.logger.warning("Anthropic API key is not set in config. ClaudeClient will not function if API calls are made.")

    def _initialize_client(self):
        if not self.client:
            if not self.api_key:
                current_app.logger.error("Anthropic API key is missing. Cannot initialize client.")
                raise ValueError("Anthropic API key is not set. ClaudeClient cannot be initialized.")
            
            try:
                current_app.logger.info(f"Initializing Anthropic client with model: {self.model_name}, SDK version: {anthropic.__version__}")
                self.client = anthropic.Anthropic(api_key=self.api_key)
            except Exception as e:
                current_app.logger.error(f"Error initializing Anthropic client: {str(e)}", exc_info=True)
                raise
    
    def _get_dataset_metadata(self, dataset_id):
        dataset = Dataset.query.get_or_404(dataset_id)
        file_path = dataset.file_path

        if not os.path.exists(file_path):
            current_app.logger.error(f"Dataset file not found for metadata: {file_path}")
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        column_info = {}
        df_preview = None 
        full_df_for_stats = None

        try:
            if dataset.file_type.lower() == 'csv':
                df_preview = pd.read_csv(file_path, nrows=5) 
                full_df_for_stats = pd.read_csv(file_path)
            elif dataset.file_type.lower() == 'json':
                full_df_for_stats = pd.read_json(file_path) 
                df_preview = full_df_for_stats.head(5)
            else:
                current_app.logger.error(f"Unsupported file type for metadata: {dataset.file_type}")
                raise ValueError(f"Unsupported file type: {dataset.file_type}")
                
            for col_name_original in full_df_for_stats.columns:
                col_name = str(col_name_original)
                col_series = full_df_for_stats[col_name_original]
                col_type_str = str(col_series.dtype)
                stats = {"type": col_type_str, "name": col_name}

                if pd.api.types.is_numeric_dtype(col_series):
                    stats.update({
                        "min": float(col_series.min()) if pd.notna(col_series.min()) else None,
                        "max": float(col_series.max()) if pd.notna(col_series.max()) else None,
                        "mean": float(col_series.mean()) if pd.notna(col_series.mean()) else None,
                        "median": float(col_series.median()) if pd.notna(col_series.median()) else None,
                        "std": float(col_series.std()) if pd.notna(col_series.std()) else None
                    })
                elif pd.api.types.is_datetime64_any_dtype(col_series):
                    stats["type"] = "datetime"
                    stats.update({
                        "min": col_series.min().isoformat() if pd.notna(col_series.min()) else None,
                        "max": col_series.max().isoformat() if pd.notna(col_series.max()) else None
                    })
                elif pd.api.types.is_categorical_dtype(col_series) or pd.api.types.is_object_dtype(col_series) or pd.api.types.is_string_dtype(col_series):
                    unique_values_count = col_series.nunique()
                    stats["unique_values"] = int(unique_values_count)
                    if unique_values_count > 0 and unique_values_count < 10 : # Check if series is not all NaN for value_counts
                         stats["top_values"] = col_series.value_counts().head(5).to_dict()
                    elif unique_values_count > 0:
                        stats["example_values"] = col_series.dropna().unique()[:3].tolist()
                    else: # All NaN case
                        stats["example_values"] = []


                column_info[col_name] = stats
                
        except Exception as e:
            current_app.logger.warning(f"Could not generate detailed column statistics for dataset {dataset_id}: {str(e)}", exc_info=True)
            if df_preview is not None:
                for col_name_original in df_preview.columns:
                    col_name = str(col_name_original)
                    column_info[col_name] = {"type": str(df_preview[col_name_original].dtype), "name": col_name}
            else:
                 column_info = {"error": "Could not load dataframe to extract column info."}

        return {
            "original_filename": dataset.original_filename,
            "file_type": dataset.file_type,
            "n_rows": dataset.n_rows,
            "n_columns": dataset.n_columns,
            "column_info": column_info
        }

    def _create_dashboard_prompt(self, dataset_metadata, title, description=""):
        column_info_str = json.dumps(dataset_metadata["column_info"], indent=2)
        
        prompt = f"""
        You are an expert data visualization web developer. Your task is to create a complete, interactive, self-contained HTML file (with embedded CSS and JavaScript) that serves as a template for a dashboard. This template will later be populated with actual data.

        # Dashboard Information
        Title: {title}
        Description: {description} (Use this to guide the theme and focus of the dashboard)

        # Dataset Structure (Metadata only)
        Filename: {dataset_metadata['original_filename']}
        Type: {dataset_metadata['file_type']}
        Approximate Rows: {dataset_metadata['n_rows']}
        Number of Columns: {dataset_metadata['n_columns']}
        
        # Column Information (Schema and basic statistics):
        {column_info_str}
        
        # CRITICAL DATA INJECTION INSTRUCTION:
        The actual dataset will be injected into the dashboard via a global JavaScript variable: `window.dynadashData`.
        This `window.dynadashData` will be an array of JavaScript objects, where each object represents a row from the dataset.
        For example, if the dataset has columns "Name" (string) and "Age" (number), `window.dynadashData` would look like:
        `[
          {{ "Name": "Alice", "Age": 30, ... }},
          {{ "Name": "Bob", "Age": 24, ... }},
          ...
        ]`
        Your generated JavaScript code MUST:
        1. Access the data exclusively from `window.dynadashData`.
        2. Perform any necessary data transformations (e.g., string to number, date parsing if strings) on `window.dynadashData` before using it in charts.
        3. Do NOT embed any static example data directly into the script for the main visualizations. Placeholder data for UI layout during development is fine, but it should be replaced by `window.dynadashData`.
        4. Initialize all charts and interactive elements using the data from `window.dynadashData`.

        # Requirements for the Dashboard Template:
        1.  **Self-Contained HTML:** Produce a single HTML file with all CSS (in `<style>` tags) and JavaScript (in `<script>` tags) embedded.
        2.  **Multiple Visualizations:** Include at least 3-5 diverse and complementary charts (e.g., bar, line, scatter, pie, heatmap) suitable for the provided column types and dataset description.
        3.  **Interactivity:** Implement interactive elements (e.g., filters based on categorical columns, date range selectors if applicable, tooltips on charts). These interactive elements should dynamically update the visualizations based on `window.dynadashData`.
        4.  **Layout & Styling:**
            *   Professionally designed, responsive, and visually appealing.
            *   Clear sections, headers, and potentially a summary/KPI section.
            *   Use a modern, clean aesthetic.
        5.  **Chart Libraries:** Use Chart.js (preferred for simplicity and wide compatibility) or D3.js for visualizations. Ensure the necessary library is linked via CDN if not fully embedded.
        6.  **Chart Best Practices:** Ensure charts have titles, axis labels, and legends where appropriate.
        7.  **Robust Initialization:** All JavaScript code for chart creation (e.g., `new Chart(ctx, config)`) must be complete and self-initializing on DOM load, using `window.dynadashData`.
        8.  **Error Handling (Basic):** The JavaScript should be robust enough not to break completely if `window.dynadashData` is empty or has unexpected minor variations (though assume the schema provided is generally correct).
        9.  **No External File Dependencies:** All assets like CSS or JS code snippets must be embedded. CDN links for major libraries (Chart.js, D3.js) are acceptable.

        # Response Format:
        Return ONLY the complete HTML code for the dashboard template, starting with `<!DOCTYPE html>`. Do not include any explanations, comments, or markdown formatting outside the HTML itself.
        The HTML should be ready to have the `window.dynadashData` variable populated and then viewed in a browser.
        """
        return prompt.strip()
    
    def generate_dashboard(self, dataset_id, title, description="", use_thinking=False):
        self._initialize_client()
        
        dataset_metadata = self._get_dataset_metadata(dataset_id)
        prompt = self._create_dashboard_prompt(dataset_metadata, title, description)
        
        current_app.logger.info(f"Requesting dashboard generation from Claude for dataset_id: {dataset_id}, title: '{title}'")

        for attempt in range(self.max_retries):
            try:
                params = {
                    "model": self.model_name,
                    "max_tokens": self.max_tokens_dashboard,
                    "temperature": self.temperature_dashboard,
                    "system": "You are a data visualization expert that creates beautiful, interactive dashboard HTML templates using HTML, CSS, and JavaScript. The data will be injected via a `window.dynadashData` variable. You only respond with complete HTML code, with no explanations or Markdown outside the HTML itself.",
                    "messages": [{"role": "user", "content": prompt}]
                }
                
                if use_thinking:
                     current_app.logger.info("Note: 'use_thinking' parameter usage is illustrative.")

                response = self.client.messages.create(**params)
                
                dashboard_html_template = None
                if response.content and isinstance(response.content, list):
                    for block in response.content:
                        if block.type == 'text':
                            dashboard_html_template = block.text
                            break
                
                if not dashboard_html_template:
                    current_app.logger.error("No text content found in Claude's response.")
                    raise ValueError("No text content found in the response from Claude.")
                
                if dashboard_html_template.strip().startswith("```html"):
                    dashboard_html_template = dashboard_html_template.split("```html", 1)[-1]
                    if dashboard_html_template.strip().endswith("```"):
                        dashboard_html_template = dashboard_html_template.rsplit("```", 1)[0]
                elif dashboard_html_template.strip().startswith("```"):
                     dashboard_html_template = dashboard_html_template.strip()[3:-3] if dashboard_html_template.strip().endswith("```") else dashboard_html_template.strip()[3:]

                dashboard_html_template = dashboard_html_template.strip()
                
                sanitized_template = self._sanitize_dashboard_html(dashboard_html_template)
                
                current_app.logger.debug(f"Generated dashboard HTML template (first 500 chars): {sanitized_template[:500]}...")
                current_app.logger.info(f"Successfully generated dashboard template from Claude for dataset_id: {dataset_id}.")
                return sanitized_template
                    
            except anthropic.APIConnectionError as e:
                current_app.logger.error(f"Claude API connection error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1: raise
                time.sleep(self.retry_delay * (attempt + 1))
            except anthropic.RateLimitError as e:
                current_app.logger.error(f"Claude API rate limit error (attempt {attempt + 1}/{self.max_retries}): {e}")
                if attempt == self.max_retries - 1: raise
                time.sleep(self.retry_delay * (attempt + 1) * 2) 
            except anthropic.APIStatusError as e: # Specific check for NotFoundError which indicates model name issue
                if isinstance(e, anthropic.NotFoundError):
                    current_app.logger.error(f"Claude API NotFoundError (attempt {attempt + 1}/{self.max_retries}): Model '{self.model_name}' not found or access denied. {e.response}")
                else:
                    current_app.logger.error(f"Claude API status error {e.status_code} (attempt {attempt + 1}/{self.max_retries}): {e.response}")
                if attempt == self.max_retries - 1: raise
                time.sleep(self.retry_delay * (attempt + 1))
            except Exception as e:
                current_app.logger.error(f"Claude API request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}", exc_info=True)
                if attempt == self.max_retries - 1: raise
                time.sleep(self.retry_delay)
        
        current_app.logger.error(f"Failed to generate dashboard from Claude after {self.max_retries} attempts for dataset_id: {dataset_id}.")
        raise Exception(f"Failed to generate dashboard from Claude after {self.max_retries} attempts.")

    def _sanitize_dashboard_html(self, html_content):
        if not html_content:
            current_app.logger.warning("Empty HTML content provided to _sanitize_dashboard_html.")
            return "<!DOCTYPE html><html><head><meta charset='UTF-8'><title>Error</title></head><body><h2>No dashboard content generated.</h2></body></html>"

        if not html_content.strip().lower().startswith("<!doctype html"):
            html_content = "<!DOCTYPE html>\n" + html_content
        
        if "<html" not in html_content.lower():
            html_content = html_content.replace("<!DOCTYPE html>", "<!DOCTYPE html>\n<html lang='en'>", 1)
            if "</html>" not in html_content.lower(): html_content += "\n</html>"
        
        head_start_idx = html_content.lower().find("<head>")
        head_end_idx = html_content.lower().find("</head>")

        if head_start_idx == -1: 
            html_tag_end = html_content.lower().find("<html>")
            insert_pos = html_tag_end + len("<html>") if html_tag_end != -1 else len("<!DOCTYPE html>")
            html_content = html_content[:insert_pos] + "\n<head><meta charset=\"UTF-8\"><title>Dashboard</title></head>\n" + html_content[insert_pos:]
            head_start_idx = html_content.lower().find("<head>") 
            head_end_idx = html_content.lower().find("</head>")


        if head_start_idx != -1 and "<meta charset" not in html_content[head_start_idx:head_end_idx if head_end_idx!=-1 else len(html_content)].lower():
            html_content = html_content[:head_start_idx+6] + "<meta charset=\"UTF-8\">\n" + html_content[head_start_idx+6:]
            head_end_idx = html_content.lower().find("</head>") 

        if "<body" not in html_content.lower():
            if head_end_idx != -1:
                html_content = html_content[:head_end_idx+7] + "\n<body>\n</body>" + html_content[head_end_idx+7:]
            elif "</html>" in html_content.lower():
                idx = html_content.lower().find("</html>")
                html_content = html_content[:idx] + "\n<body>\n</body>\n" + html_content[idx:]
            else:
                html_content += "\n<body>\n</body>"
        
        current_head_content = html_content[head_start_idx:head_end_idx if head_end_idx!=-1 else len(html_content)]

        if head_start_idx != -1 and '<meta name="viewport"' not in current_head_content.lower():
            viewport_meta = '<meta name="viewport" content="width=device-width, initial-scale=1.0">\n'
            html_content = html_content[:head_start_idx+6] + viewport_meta + html_content[head_start_idx+6:]
            head_end_idx = html_content.lower().find("</head>")

        if head_start_idx != -1 and '<meta http-equiv="Content-Security-Policy"' not in current_head_content:
            # Adjusted CSP for broader CDN compatibility if needed, but keep it reasonably tight
            csp_tag = '<meta http-equiv="Content-Security-Policy" content="default-src \'self\'; script-src \'self\' \'unsafe-inline\' https://*.jsdelivr.net https://*.d3js.org https://cdnjs.cloudflare.com; style-src \'self\' \'unsafe-inline\' https://*.jsdelivr.net https://cdnjs.cloudflare.com; img-src \'self\' data: blob:; connect-src \'self\'; font-src \'self\' https://*.jsdelivr.net https://cdnjs.cloudflare.com;">\n'
            html_content = html_content[:head_start_idx+6] + csp_tag + html_content[head_start_idx+6:]
            head_end_idx = html_content.lower().find("</head>")
        
        libraries_to_check = [
            {"reference": "Chart", "cdn": "https://cdn.jsdelivr.net/npm/chart.js", "check_tag": "chart.js"},
            {"reference": "d3", "cdn": "https://d3js.org/d3.v7.min.js", "check_tag": "d3.v7.min.js"},
        ]
        
        if head_end_idx != -1: # Ensure head_end_idx is valid before using
            insertion_point = head_end_idx
            for lib in libraries_to_check:
                # Check if library is referenced (e.g. "new Chart" or "d3.select") AND script tag is missing
                if lib["reference"] in html_content and lib["check_tag"] not in html_content:
                    script_tag = f'<script src="{lib["cdn"]}"></script>\n'
                    html_content = html_content[:insertion_point] + script_tag + html_content[insertion_point:]
                    insertion_point += len(script_tag) 
        
        if "console.error('Dashboard error:'" not in html_content:
            error_handling_script = """
            <script>
            window.addEventListener('error', function(event) {
                console.error('Dashboard error:', event.message, 'at', event.filename, ':', event.lineno);
                var errorDisplay = document.getElementById('dynadashInternalErrorDisplay');
                if (!errorDisplay && document.body) {
                    errorDisplay = document.createElement('div');
                    errorDisplay.id = 'dynadashInternalErrorDisplay';
                    errorDisplay.style.cssText = 'position:fixed;top:5px;left:5px;right:5px;padding:10px;background:rgba(220,50,50,0.9);color:white;border-radius:4px;z-index:20000;font-family:sans-serif;font-size:14px;';
                    document.body.insertBefore(errorDisplay, document.body.firstChild);
                }
                if(errorDisplay) errorDisplay.textContent = 'Dashboard Error: ' + event.message + ' (in ' + (event.filename || 'inline script') + ':' + event.lineno + ')';
            });
            document.addEventListener('DOMContentLoaded', function() {
                if (typeof window.dynadashData === 'undefined' || window.dynadashData === null || (Array.isArray(window.dynadashData) && window.dynadashData.length === 0)) {
                    console.warn('window.dynadashData is not defined or is empty. Dashboard might not render correctly.');
                    var dataWarningDiv = document.getElementById('dynadashDataWarningDisplay');
                    if(!dataWarningDiv && document.body) {
                        dataWarningDiv = document.createElement('div');
                        dataWarningDiv.id = 'dynadashDataWarningDisplay';
                        dataWarningDiv.style.cssText = 'padding:10px;background:rgba(255,220,50,0.8);color:black;text-align:center;font-family:sans-serif;font-size:14px;';
                        dataWarningDiv.textContent = 'Notice: Data for this dashboard (window.dynadashData) was not loaded or is empty. Visualizations may not appear as expected.';
                        document.body.insertBefore(dataWarningDiv, document.body.firstChild);
                    }
                }
                setTimeout(function() {
                    if (typeof Chart !== 'undefined' && typeof window.dynadashData !== 'undefined') {
                        var canvases = document.querySelectorAll('canvas');
                        canvases.forEach(function(canvas) {
                            try {
                                var chartInstance = Chart.getChart(canvas); 
                                if (chartInstance) { chartInstance.update('none'); } 
                            } catch(e) { console.warn('Could not update chart on canvas ' + (canvas.id || '(no id)') + ':', e); }
                        });
                    }
                }, 1200);
            });
            </script>
            """
            body_end_idx = html_content.lower().rfind('</body>')
            if body_end_idx != -1:
                 html_content = html_content[:body_end_idx] + error_handling_script + html_content[body_end_idx:]
            else:
                 html_content += error_handling_script
        
        return html_content

    def analyze_dataset(self, dataset_id, use_thinking=True):
        self._initialize_client()
        dataset_metadata_and_content = self._read_dataset_file(dataset_id)
        
        prompt = f"""
        You are a data analysis expert. Analyze the following dataset and provide insights.
        
        Dataset Information:
        - Filename: {dataset_metadata_and_content['original_filename']}
        - Type: {dataset_metadata_and_content['file_type']}
        - Rows: {dataset_metadata_and_content['n_rows']}
        - Columns: {dataset_metadata_and_content['n_columns']}
        - Column Details: {json.dumps(dataset_metadata_and_content['column_info'])}
        
        Dataset Content (first 50 rows or 2000 characters):
        ```{dataset_metadata_and_content['file_type']}
        { (dataset_metadata_and_content['content'][:2000] + '...' if len(dataset_metadata_and_content['content']) > 2000 else dataset_metadata_and_content['content']) }
        ```
        
        Please provide:
        1. A concise summary of the dataset's nature and potential use.
        2. Key statistical insights for important columns.
        3. Interesting patterns, correlations, or anomalies you observe or hypothesize.
        4. Potential data quality issues.
        5. Recommendations for 3-5 specific visualizations.
        
        Format your response STRICTLY as JSON:
        {{
            "summary": "string",
            "key_statistics_insights": [{{ "column_name": "string", "insight": "string" }}],
            "patterns_correlations": [{{ "observation": "string", "implication_or_hypothesis": "string" }}],
            "data_quality_issues": [{{ "issue_type": "string", "description": "string", "affected_columns": ["string"] }}],
            "visualization_recommendations": [{{ "chart_type": "string", "description": "string", "relevant_columns": ["string"] }}]
        }}
        """
        
        current_app.logger.info(f"Requesting dataset analysis from Claude for dataset_id: {dataset_id}")

        for attempt in range(self.max_retries):
            try:
                params = {
                    "model": self.model_name,
                    "max_tokens": self.max_tokens_analysis,
                    "temperature": self.temperature_analysis,
                    "system": "You are a data analysis expert. Respond strictly with JSON.",
                    "messages": [{"role": "user", "content": prompt}]
                }

                response = self.client.messages.create(**params)
                
                analysis_text = None
                if response.content and isinstance(response.content, list):
                     for block in response.content:
                        if block.type == 'text': analysis_text = block.text; break
                
                if not analysis_text:
                    current_app.logger.error("No text content found in Claude's analysis response.")
                    raise ValueError("No text content found in the analysis response from Claude.")

                if analysis_text.strip().startswith("```json"):
                    analysis_text = analysis_text.split("```json",1)[-1]
                    if analysis_text.strip().endswith("```"): analysis_text = analysis_text.rsplit("```",1)[0]
                elif analysis_text.strip().startswith("```"):
                    analysis_text = analysis_text.strip()[3:-3] if analysis_text.strip().endswith("```") else analysis_text.strip()[3:]
                
                analysis_text = analysis_text.strip()
                analysis = json.loads(analysis_text)
                current_app.logger.info(f"Successfully received dataset analysis from Claude for dataset_id: {dataset_id}.")
                return analysis
            
            except json.JSONDecodeError as e:
                current_app.logger.error(f"Failed to parse JSON from Claude's analysis response (attempt {attempt + 1}/{self.max_retries}): {e}. Response: {analysis_text[:500]}", exc_info=True)
                if attempt == self.max_retries - 1: raise ValueError(f"Invalid JSON response from Claude after retries: {e}")
                time.sleep(self.retry_delay)
            except anthropic.APIError as e: 
                current_app.logger.error(f"Claude API Error for analysis (attempt {attempt + 1}/{self.max_retries}): {type(e).__name__} - {e}")
                if attempt == self.max_retries - 1: raise
                delay_multiplier = 2 if isinstance(e, anthropic.RateLimitError) else 1
                time.sleep(self.retry_delay * (attempt + 1) * delay_multiplier)
            except Exception as e:
                current_app.logger.error(f"Claude analysis request failed (attempt {attempt + 1}/{self.max_retries}): {str(e)}", exc_info=True)
                if attempt == self.max_retries - 1: raise
                time.sleep(self.retry_delay)
        
        current_app.logger.error(f"Failed to get dataset analysis from Claude after {self.max_retries} attempts for dataset_id: {dataset_id}.")
        raise Exception(f"Failed to get dataset analysis from Claude after {self.max_retries} attempts.")

    def _read_dataset_file(self, dataset_id):
        dataset = Dataset.query.get_or_404(dataset_id)
        file_path = dataset.file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        with open(file_path, 'r', encoding='utf-8') as f:
            file_content = f.read()
        
        metadata = self._get_dataset_metadata(dataset_id)
        
        return {
            "content": file_content,
            "file_type": dataset.file_type,
            "original_filename": dataset.original_filename,
            "n_rows": dataset.n_rows,
            "n_columns": dataset.n_columns,
            "column_info": metadata['column_info']
        }
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/services/data_processor.py

```
import os
import pandas as pd
import numpy as np
import json
from flask import current_app
from flask_socketio import emit
from ..models import db, Dataset
import uuid
from werkzeug.utils import secure_filename

class DataProcessor:
    """Service for processing and cleaning uploaded datasets."""
    
    def __init__(self):
        """Initialize the data processor."""
        self.supported_file_types = ['csv', 'json']
    
    def process(self, file, user_id, is_public=False, socket_id=None):
        """
        Process an uploaded file and save it to the database.
        
        Args:
            file: The uploaded file object
            user_id: The ID of the user who uploaded the file
            is_public: Whether the dataset should be public
            socket_id: The Socket.IO session ID for progress updates
        
        Returns:
            The created Dataset object
        """
        # Validate file type
        filename = secure_filename(file.filename)
        file_ext = filename.rsplit('.', 1)[1].lower() if '.' in filename else ''
        
        if file_ext not in self.supported_file_types:
            raise ValueError(f"Unsupported file type: {file_ext}. Supported types: {', '.join(self.supported_file_types)}")
        
        # Generate a unique filename
        unique_filename = f"{uuid.uuid4().hex}.{file_ext}"
        file_path = os.path.join(current_app.config['UPLOAD_FOLDER'], unique_filename)
        
        # Save the file
        file.save(file_path)
        
        # Process the file based on its type
        if file_ext == 'csv':
            return self._process_csv(file_path, filename, user_id, is_public, socket_id)
        elif file_ext == 'json':
            return self._process_json(file_path, filename, user_id, is_public, socket_id)
    
    def _process_csv(self, file_path, original_filename, user_id, is_public, socket_id):
        """Process a CSV file."""
        try:
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 10, 'message': 'Reading CSV file...'}, room=socket_id)
            
            # Read the CSV file
            df = pd.read_csv(file_path)
            
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 30, 'message': 'Cleaning data...'}, room=socket_id)
            
            # Clean the data
            df = self._clean_data(df)
            
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 60, 'message': 'Saving cleaned data...'}, room=socket_id)
            
            # Save the cleaned data back to the file
            df.to_csv(file_path, index=False)
            
            # Create a dataset record
            dataset = Dataset(
                user_id=user_id,
                filename=os.path.basename(file_path),
                original_filename=original_filename,
                file_path=file_path,
                file_type='csv',
                n_rows=len(df),
                n_columns=len(df.columns),
                is_public=is_public
            )
            
            db.session.add(dataset)
            db.session.commit()
            
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 100, 'message': 'Processing complete!'}, room=socket_id)
                emit('processing_complete', room=socket_id)
            
            return dataset
        
        except Exception as e:
            # Clean up the file if there was an error
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Emit error
            if socket_id:
                emit('processing_error', {'message': str(e)}, room=socket_id)
            
            raise
    
    def _process_json(self, file_path, original_filename, user_id, is_public, socket_id):
        """Process a JSON file."""
        try:
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 10, 'message': 'Reading JSON file...'}, room=socket_id)
            
            # Read the JSON file
            with open(file_path, 'r') as f:
                data = json.load(f)
            
            # Convert to DataFrame
            if isinstance(data, list):
                df = pd.DataFrame(data)
            elif isinstance(data, dict):
                # Handle nested JSON structures
                if any(isinstance(v, (list, dict)) for v in data.values()):
                    # Flatten the structure
                    flattened = []
                    for key, value in data.items():
                        if isinstance(value, list):
                            for item in value:
                                if isinstance(item, dict):
                                    item['_key'] = key
                                    flattened.append(item)
                        elif isinstance(value, dict):
                            value['_key'] = key
                            flattened.append(value)
                    df = pd.DataFrame(flattened)
                else:
                    # Simple key-value pairs
                    df = pd.DataFrame([data])
            else:
                raise ValueError("Invalid JSON structure. Expected a list or dictionary.")
            
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 30, 'message': 'Cleaning data...'}, room=socket_id)
            
            # Clean the data
            df = self._clean_data(df)
            
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 60, 'message': 'Saving cleaned data...'}, room=socket_id)
            
            # Save the cleaned data back to the file
            df.to_json(file_path, orient='records')
            
            # Create a dataset record
            dataset = Dataset(
                user_id=user_id,
                filename=os.path.basename(file_path),
                original_filename=original_filename,
                file_path=file_path,
                file_type='json',
                n_rows=len(df),
                n_columns=len(df.columns),
                is_public=is_public
            )
            
            db.session.add(dataset)
            db.session.commit()
            
            # Emit progress update
            if socket_id:
                emit('progress_update', {'percent': 100, 'message': 'Processing complete!'}, room=socket_id)
                emit('processing_complete', room=socket_id)
            
            return dataset
        
        except Exception as e:
            # Clean up the file if there was an error
            if os.path.exists(file_path):
                os.remove(file_path)
            
            # Emit error
            if socket_id:
                emit('processing_error', {'message': str(e)}, room=socket_id)
            
            raise
    
    def _clean_data(self, df):
        """Clean and preprocess the data."""
        # Make a copy to avoid modifying the original
        df_cleaned = df.copy()
        
        # Handle missing values
        for col in df_cleaned.columns:
            # For numeric columns, replace NaN with the median
            if pd.api.types.is_numeric_dtype(df_cleaned[col]):
                df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].median())
            # For categorical columns, replace NaN with the mode
            elif pd.api.types.is_categorical_dtype(df_cleaned[col]) or pd.api.types.is_object_dtype(df_cleaned[col]):
                df_cleaned[col] = df_cleaned[col].fillna(df_cleaned[col].mode()[0] if not df_cleaned[col].mode().empty else 'Unknown')
        
        # Handle outliers in numeric columns
        for col in df_cleaned.select_dtypes(include=[np.number]).columns:
            # Calculate IQR
            Q1 = df_cleaned[col].quantile(0.25)
            Q3 = df_cleaned[col].quantile(0.75)
            IQR = Q3 - Q1
            
            # Define bounds
            lower_bound = Q1 - 1.5 * IQR
            upper_bound = Q3 + 1.5 * IQR
            
            # Tag outliers (don't remove them)
            df_cleaned.loc[(df_cleaned[col] < lower_bound) | (df_cleaned[col] > upper_bound), col + '_outlier'] = True
            df_cleaned.loc[~((df_cleaned[col] < lower_bound) | (df_cleaned[col] > upper_bound)), col + '_outlier'] = False
        
        # Convert date columns to datetime
        for col in df_cleaned.columns:
            if pd.api.types.is_object_dtype(df_cleaned[col]):
                try:
                    # Try to detect common date formats
                    date_formats = [
                        '%Y-%m-%d', '%m/%d/%Y', '%d/%m/%Y', '%Y/%m/%d',
                        '%b %d, %Y', '%d %b %Y', '%B %d, %Y', '%d %B %Y',
                        '%m-%d-%Y', '%d-%m-%Y', '%Y.%m.%d', '%d.%m.%Y'
                    ]
                    
                    # Sample the first non-null value to check format
                    sample = df_cleaned[col].dropna().iloc[0] if not df_cleaned[col].dropna().empty else None
                    
                    if sample:
                        # Try each format until one works
                        format_found = None
                        for date_format in date_formats:
                            try:
                                pd.to_datetime(sample, format=date_format)
                                format_found = date_format
                                break
                            except:
                                continue
                        
                        # If a format was found, use it; otherwise fall back to the default parser
                        if format_found:
                            df_cleaned[col + '_date'] = pd.to_datetime(df_cleaned[col], format=format_found, errors='coerce')
                        else:
                            # Use pandas default parser when format is unknown
                            df_cleaned[col + '_date'] = pd.to_datetime(df_cleaned[col], errors='coerce')
                    else:
                        # No sample available, use the default parser
                        df_cleaned[col + '_date'] = pd.to_datetime(df_cleaned[col], errors='coerce')
                    
                    # If more than 50% of the values are valid dates, keep the column
                    if df_cleaned[col + '_date'].notna().mean() > 0.5:
                        df_cleaned[col + '_date'] = df_cleaned[col + '_date'].dt.strftime('%Y-%m-%d')
                    else:
                        df_cleaned = df_cleaned.drop(columns=[col + '_date'])
                except Exception as e:
                    # If conversion fails, ignore
                    pass
        
        return df_cleaned
    
    def get_preview(self, dataset_id, max_rows=10):
        """Get a preview of the dataset as HTML."""
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Read the dataset file
        file_path = dataset.file_path
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"Dataset file not found: {file_path}")
        
        # Read the dataset based on file type
        if dataset.file_type.lower() == 'csv':
            df = pd.read_csv(file_path, nrows=max_rows)
        elif dataset.file_type.lower() == 'json':
            df = pd.read_json(file_path)
            if len(df) > max_rows:
                df = df.head(max_rows)
        else:
            raise ValueError(f"Unsupported file type: {dataset.file_type}")
        
        # Convert to HTML table
        return df.to_html(classes='table table-striped table-bordered table-hover', index=False)
    
    def delete_dataset(self, dataset_id):
        """Delete a dataset and its file."""
        dataset = Dataset.query.get_or_404(dataset_id)
        
        # Delete the file
        if os.path.exists(dataset.file_path):
            os.remove(dataset.file_path)
        
        # Delete the dataset record
        db.session.delete(dataset)
        db.session.commit()
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/socket_events.py

```
from flask_socketio import emit, join_room, leave_room
from flask_login import current_user
from flask import request
from . import socketio

@socketio.on('connect')
def handle_connect():
    """Handle client connection."""
    if current_user.is_authenticated:
        # Log connection
        print(f"Client connected: {request.sid}")

@socketio.on('disconnect')
def handle_disconnect():
    """Handle client disconnection."""
    print(f"Client disconnected: {request.sid}")

@socketio.on('join')
def handle_join(data):
    """Handle join room event."""
    if current_user.is_authenticated:
        user_id = data.get('user_id')
        
        # Validate that the user_id matches the current user
        if user_id and str(user_id) == str(current_user.id):
            room = f"user_{user_id}"
            join_room(room)
            print(f"User {user_id} joined room: {room}")
        else:
            # Security check failed
            print(f"Join room security check failed for user {current_user.id}")
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/.gitkeep

```
# This file is intentionally left empty to ensure the static directory is included in the Git repository.
# The static directory is used to store static assets like CSS, JavaScript, and images.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/css/.gitkeep

```
# This file is intentionally left empty to ensure the css directory is included in the Git repository.
# The css directory is used to store CSS files for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/css/main.css

```
<REDACTED FOR BREVITY>
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/images/.gitkeep

```
# This file is intentionally left empty to ensure the images directory is included in the Git repository.
# The images directory is used to store image files for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/.gitkeep

```
# This file is intentionally left empty to ensure the js directory is included in the Git repository.
# The js directory is used to store JavaScript files for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/common.js

```
// Wrap in DOMContentLoaded to ensure elements are available
document.addEventListener('DOMContentLoaded', function() {
    // Toggle user menu
    const userMenuButton = document.getElementById('user-menu-button');
    const userMenu = document.getElementById('user-menu');
    if (userMenuButton && userMenu) {
        userMenuButton.addEventListener('click', function() {
            userMenu.classList.toggle('hidden');
        });
    }

    // Close user menu when clicking outside
    document.addEventListener('click', function(event) {
        if (userMenuButton && userMenu && !userMenu.classList.contains('hidden') &&
            !userMenu.contains(event.target) &&
            userMenuButton && !userMenuButton.contains(event.target)) { // check userMenuButton exists
            userMenu.classList.add('hidden');
        }
    });

    // Toggle mobile menu
    const mobileMenuButton = document.getElementById('mobile-menu-button');
    const mobileMenu = document.getElementById('mobile-menu');
    if (mobileMenuButton && mobileMenu) {
        mobileMenuButton.addEventListener('click', function() {
            mobileMenu.classList.toggle('hidden');
        });
    }
    

    // Close flash messages on click
    document.querySelectorAll('.close-flash').forEach(function(button) {
        button.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });

    // Auto-close flash messages after 5 seconds
    const flashMessages = document.querySelectorAll('.flash-message');
    if (flashMessages.length > 0) {
        setTimeout(function() {
            flashMessages.forEach(function(message) {
                message.style.transition = 'opacity 0.5s ease';
                message.style.opacity = '0';
                setTimeout(() => { message.style.display = 'none'; }, 500);
            });
        }, 5000);
    }

    // Socket.IO connection (only when authenticated and user ID is available)
    // window.dynadash_current_user_id is set in base.html
    if (typeof window.dynadash_current_user_id !== 'undefined' && window.dynadash_current_user_id !== null) {
        try {
            const socket = io(); 
            socket.on('connect', function() {
                console.log('Socket.IO connected, SID:', socket.id);
                socket.emit('join', { user_id: window.dynadash_current_user_id });
            });
            socket.on('disconnect', function(reason) {
                console.log('Socket.IO disconnected:', reason);
            });
            socket.on('connect_error', (err) => {
                console.error('Socket.IO connection error:', err.message, err.data);
            });
            
            // Generic progress handlers previously in visual_generate.js are moved here
            // as they are more general. Specific pages might override or add more details.
            socket.on('progress_update', function(data) {
                console.log('Progress update:', data);
                const progressBar = document.getElementById('progress-bar'); 
                const progressLabel = document.getElementById('progress-label');
                if (progressBar) progressBar.style.width = data.percent + '%';
                if (progressLabel) progressLabel.textContent = data.message;
                
                // If a more specific handler exists (e.g., on generate page), it can update step indicators
                if (typeof window.updateStepIndicator === 'function') {
                    window.updateStepIndicator(data.percent);
                }
            });

            socket.on('processing_complete', function(data) {
                console.log('Processing complete:', data);
                const progressBar = document.getElementById('progress-bar');
                const progressLabel = document.getElementById('progress-label');
                if (progressBar) progressBar.style.width = '100%';
                if (progressLabel) progressLabel.textContent = 'Processing complete! Redirecting...';
                
                if (typeof window.updateStepIndicator === 'function') {
                    window.updateStepIndicator(100);
                }

                if (data && data.redirect_url) {
                    window.location.href = data.redirect_url;
                } else {
                     const processingModal = document.getElementById('processing-modal');
                     if(processingModal) setTimeout(() => { processingModal.classList.add('hidden'); }, 1500);
                }
            });

            socket.on('processing_error', function(data) {
                console.error('Processing error from server:', data);
                const progressLabel = document.getElementById('progress-label');
                const errorMessageModal = document.getElementById('error-message-modal'); // Assuming this ID exists on modal
                
                if(progressLabel) progressLabel.textContent = 'Error occurred.';
                if(errorMessageModal) {
                    errorMessageModal.textContent = 'Error: ' + data.message;
                    errorMessageModal.classList.remove('hidden');
                } else {
                    alert('Error during processing: ' + data.message); 
                }
                // Don't automatically hide processing modal on error, let user see message.
            });

        } catch (e) {
            console.error("Failed to initialize Socket.IO. Is the library loaded?", e);
        }
    }
});
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/dashboard_renderer.js

```
document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ dashboard_renderer.js loaded");

    const dashboardFrame = document.getElementById('dashboard-frame');
    const fullscreenFrame = document.getElementById('fullscreen-frame');
    const loadingIndicator = document.getElementById('dashboard-loading');
    const dashboardError = document.getElementById('dashboard-error');

    // Data and template are now expected to be on the window object
    // They are injected by app/templates/visual/view.html's head_scripts block
    const dashboardTemplateHtml = window.dynadashDashboardTemplateHtml; 
    const actualDatasetData = window.dynadashDatasetJson; 

    function buildFullHtml(template, data) {
        if (typeof template !== 'string' || !template) {
            console.error("Dashboard template is missing or not a string.");
            return "<html><body>Error: Dashboard template missing.</body></html>";
        }
        // Ensure data is an array, default to empty if undefined/null
        const dataToInject = (typeof data !== 'undefined' && data !== null) ? data : [];
        const dataScript = `<script>window.dynadashData = ${JSON.stringify(dataToInject)};<\/script>`;
        
        let finalHtml = template;
        const headEndTag = '</head>';
        const bodyStartTag = '<body>';
        const headEndIndex = template.toLowerCase().lastIndexOf(headEndTag); // Use lastIndexOf for head
        const bodyStartIndex = template.toLowerCase().indexOf(bodyStartTag);

        if (headEndIndex !== -1) {
            finalHtml = template.slice(0, headEndIndex) + dataScript + "\n" + template.slice(headEndIndex);
        } else if (bodyStartIndex !== -1) {
            finalHtml = template.slice(0, bodyStartIndex + bodyStartTag.length) + "\n" + dataScript + template.slice(bodyStartIndex + bodyStartTag.length);
        } else {
            finalHtml = dataScript + template; 
        }
        return finalHtml;
    }

    function loadDashboard() {
        if (!dashboardFrame || !loadingIndicator || !dashboardError) { // fullscreenFrame is optional for this function
            console.error("One or more essential dashboard display elements are missing from the DOM.");
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            if (dashboardError) {
                 dashboardError.style.display = 'block';
                 dashboardError.querySelector('p').textContent = "Essential dashboard elements missing from page.";
            }
            return;
        }
        
        if (typeof dashboardTemplateHtml === 'undefined' || dashboardTemplateHtml === null || dashboardTemplateHtml.trim() === "") {
            console.error("Dashboard template HTML is not available (window.dynadashDashboardTemplateHtml is empty or undefined).");
            showDashboardError("Dashboard template is missing or could not be loaded.");
            return;
        }

        loadingIndicator.style.display = 'flex';
        dashboardError.style.display = 'none';
        dashboardFrame.style.display = 'none';
        if(fullscreenFrame) fullscreenFrame.setAttribute('srcdoc', '');


        try {
            const fullHtmlContent = buildFullHtml(dashboardTemplateHtml, actualDatasetData);
            
            // Function to handle iframe load/error
            const handleIframeLoad = (frameElement, isPrimary) => {
                console.log(`Iframe ${frameElement.id} loaded.`);
                if(isPrimary) {
                    loadingIndicator.style.display = 'none';
                    dashboardFrame.style.display = 'block';
                }
            };

            const handleIframeError = (frameElement, isPrimary, errorMsg) => {
                console.error(`Error loading ${frameElement.id} iframe content:`, errorMsg);
                if(isPrimary) {
                    showDashboardError(`Failed to load dashboard content in iframe (${frameElement.id}).`);
                }
            };
            
            dashboardFrame.onload = () => handleIframeLoad(dashboardFrame, true);
            dashboardFrame.onerror = (e) => handleIframeError(dashboardFrame, true, e.type);
            dashboardFrame.setAttribute('srcdoc', fullHtmlContent);

            if (fullscreenFrame) { 
                fullscreenFrame.onload = () => handleIframeLoad(fullscreenFrame, false);
                fullscreenFrame.onerror = (e) => handleIframeError(fullscreenFrame, false, e.type);
                fullscreenFrame.setAttribute('srcdoc', fullHtmlContent);
            }

            // Fallback timer
            setTimeout(() => {
                const isDashboardFrameVisible = dashboardFrame.style.display === 'block';
                if (!isDashboardFrameVisible && loadingIndicator.style.display !== 'none') {
                    console.warn("Dashboard iframe onload event might not have fired as expected after timeout.");
                    let frameDoc = dashboardFrame.contentDocument || dashboardFrame.contentWindow?.document;
                    if (frameDoc && frameDoc.body && frameDoc.body.children.length > 0 && frameDoc.readyState === 'complete') {
                        loadingIndicator.style.display = 'none';
                        dashboardFrame.style.display = 'block';
                    } else {
                        showDashboardError("Dashboard did not load correctly or is empty after timeout.");
                    }
                }
            }, 8000);

        } catch (err) {
            console.error("Error setting up dashboard srcdoc:", err);
            showDashboardError("A JavaScript error occurred while preparing the dashboard: " + err.message);
        }
    }

    function showDashboardError(message = "An unknown error occurred while loading the dashboard.") {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (dashboardError) {
            dashboardError.style.display = 'block';
            const p = dashboardError.querySelector('p');
            if(p) p.textContent = message;
        }
        if (dashboardFrame) dashboardFrame.style.display = 'none';
    }

    const fullscreenBtn = document.getElementById('fullscreen-btn');
    const exitFullscreenBtn = document.getElementById('exit-fullscreen-btn');
    const fullscreenContainer = document.getElementById('fullscreen-container');

    if (fullscreenBtn && exitFullscreenBtn && fullscreenContainer && fullscreenFrame) {
        fullscreenBtn.addEventListener('click', () => {
            fullscreenContainer.style.display = 'block';
            document.body.style.overflow = 'hidden';
        });

        exitFullscreenBtn.addEventListener('click', () => {
            fullscreenContainer.style.display = 'none';
            document.body.style.overflow = 'auto';
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === "Escape" && fullscreenContainer.style.display === 'block') {
                exitFullscreenBtn.click();
            }
        });
    }
    
    document.getElementById('reload-dashboard-btn')?.addEventListener('click', loadDashboard); 
    document.getElementById('refresh-btn-dashboard')?.addEventListener('click', loadDashboard); 

    const downloadBtn = document.getElementById('download-btn-dashboard');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', () => {
            if (typeof dashboardTemplateHtml === 'undefined' || dashboardTemplateHtml === null) {
                alert("No dashboard template available to download.");
                return;
            }
            const fullHtmlToDownload = buildFullHtml(dashboardTemplateHtml, actualDatasetData || []);
            const link = document.createElement('a');
            const blob = new Blob([fullHtmlToDownload], { type: 'text/html;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            link.href = url;
            link.download = 'dynadash_dashboard.html';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        });
    }

    // Initial load
    if (document.readyState === 'complete' || (document.readyState !== 'loading' && !document.documentElement.doScroll)) {
      loadDashboard();
    } else {
      document.addEventListener('DOMContentLoaded', loadDashboard);
    }
});
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/profile.js

```
// This file contains JavaScript code for the profile page.
// It handles the confirmation modal for deleting an account.

document.addEventListener('DOMContentLoaded', function() {
  // show the modal instead of browser confirm()
  window.confirmAndSubmit = function() {
    document.getElementById('delete-account-modal')
            .classList.remove('hidden');
  };

  // cancel hides the modal
  document.getElementById('cancel-delete-account')
          .addEventListener('click', function() {
    document.getElementById('delete-account-modal')
            .classList.add('hidden');
  });

  // confirm submits the hidden form
  document.getElementById('confirm-delete-account')
          .addEventListener('click', function() {
    document.getElementById('delete-account-form')
            .submit();
  });
});

```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/upload.js

```
$(document).ready(function() {
  // Handle file selection
  const dropZone = $('#drop-zone');
  const fileInput = $('#file');
  const fileInfo = $('#file-info');
  const fileName = $('#file-name');
  const removeFile = $('#remove-file');
  const previewBtn = $('#preview-btn');
  const previewContainer = $('#preview-container');
  const previewContent = $('#preview-content');
  const processingModal = $('#processing-modal');
  const progressBar = $('#progress-bar');
  const progressLabel = $('#progress-label');

  fileInput.on('change', function() {
    if (fileInput[0].files.length > 0) {
      const file = fileInput[0].files[0];
      fileName.text(file.name);
      fileInfo.removeClass('hidden');
      previewBtn.removeClass('hidden');
    } else {
      fileInfo.addClass('hidden');
      previewBtn.addClass('hidden');
      previewContainer.addClass('hidden');
    }
  });

  // Handle drag & drop
  dropZone.on('dragover', function(e) {
    e.preventDefault();
    dropZone.addClass('border-blue-500');
  });

  dropZone.on('dragleave', function() {
    dropZone.removeClass('border-blue-500');
  });

  dropZone.on('drop', function(e) {
    e.preventDefault();
    dropZone.removeClass('border-blue-500');
    const files = e.originalEvent.dataTransfer.files;
    if (files.length > 0) {
      fileInput[0].files = files;
      fileName.text(files[0].name);
      fileInfo.removeClass('hidden');
      previewBtn.removeClass('hidden');
    }
  });

  // Remove selected file
  removeFile.on('click', function() {
    fileInput.val('');
    fileInfo.addClass('hidden');
    previewBtn.addClass('hidden');
    previewContainer.addClass('hidden');
  });

  // Preview selected file
  previewBtn.on('click', function() {
    if (fileInput[0].files.length > 0) {
      const file = fileInput[0].files[0];
      const reader = new FileReader();
      reader.onload = function(e) {
        let content = e.target.result;
        let html = '';

        if (file.name.endsWith('.csv')) {
          // Parse CSV
          const rows = content.split('\n');
          html = '<table class="min-w-full divide-y divide-gray-200">';
          rows.slice(0, 10).forEach((row, rowIndex) => {
            const cells = row.split(',');
            html += '<tr>';
            cells.forEach((cell, cellIndex) => {
              if (rowIndex === 0) {
                html += `<th class="px-3 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">${cell}</th>`;
              } else {
                html += `<td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">${cell}</td>`;
              }
            });
            html += '</tr>';
          });
          html += '</table>';
        } else if (file.name.endsWith('.json')) {
          // Parse JSON
          try {
            const data = JSON.parse(content);
            html = '<pre class="text-sm text-gray-700">' + JSON.stringify(data, null, 2) + '</pre>';
          } catch (err) {
            html = '<div class="text-red-500">Invalid JSON file</div>';
          }
        }

        previewContent.html(html);
        previewContainer.removeClass('hidden');
      };
      reader.readAsText(file);
    }
  });

  // Handle form submission and show processing modal
  $('#upload-form').on('submit', function() {
    processingModal.removeClass('hidden');
    const socket = io();
    socket.on('progress_update', function(data) {
      progressBar.css('width', data.percent + '%');
      progressLabel.text(data.message);
    });
    socket.on('processing_complete', function() {
      progressBar.css('width', '100%');
      progressLabel.text('Processing complete!');
      // Server-side will redirect automatically
    });
    socket.on('processing_error', function(data) {
      processingModal.addClass('hidden');
      alert('Error: ' + data.message);
    });
  });
});

```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/view.js

```
$(document).ready(function() {
    // Delete confirmation modal
    const deleteModal = $('#delete-modal');

    $('#delete-btn').on('click', function() {
        deleteModal.removeClass('hidden');
    });

    $('#cancel-delete').on('click', function() {
        deleteModal.addClass('hidden');
    });

    // Close modal when clicking outside the modal element
    $(window).on('click', function(event) {
        if (event.target === deleteModal[0]) {
            deleteModal.addClass('hidden');
        }
    });

    // Download dataset
    $('#download-btn').on('click', function() {
        const downloadUrl = $(this).data('download-url');
        window.location.href = downloadUrl;
    });
});
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/visual.js

```
document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ visual.js loaded");

  // ---------- Share Page: confirm deletion ----------
  const unshareForms = document.querySelectorAll('form[action*="/unshare/"]');
  unshareForms.forEach(form => {
    form.addEventListener('submit', function (e) {
      const confirmed = confirm("Are you sure you want to remove this user's access?");
      if (!confirmed) {
        e.preventDefault();
      }
    });
  });

  // ---------- View Page: fullscreen mode ----------
  const fullscreenBtn = document.getElementById("fullscreen-btn");
  const exitFullscreenBtn = document.getElementById("exit-fullscreen-btn");
  const fullscreenContainer = document.getElementById("fullscreen-container");

  if (fullscreenBtn && exitFullscreenBtn && fullscreenContainer) {
    fullscreenBtn.addEventListener("click", () => {
      fullscreenContainer.style.display = "block";
      document.body.style.overflow = "hidden";
    });

    exitFullscreenBtn.addEventListener("click", () => {
      fullscreenContainer.style.display = "none";
      document.body.style.overflow = "auto";
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        fullscreenContainer.style.display = "none";
        document.body.style.overflow = "auto";
      }
    });
  }

  // ---------- View Page: delete confirmation ----------
  const deleteBtn = document.querySelector('form[action*="/delete/"] button[type="submit"]');
  if (deleteBtn) {
    deleteBtn.addEventListener("click", function (e) {
      const confirmed = confirm("Are you sure you want to delete this dashboard?");
      if (!confirmed) e.preventDefault();
    });
  }

  // ---------- Shared Pages: auto-hide flash messages ----------
  const flash = document.querySelector(".alert");
  if (flash) {
    setTimeout(() => {
      flash.style.display = "none";
    }, 3000);
  }
});
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/.gitkeep

```
# This file is intentionally left empty to ensure the templates directory is included in the Git repository.
# The templates directory is used to store Jinja2 templates for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/auth/.gitkeep

```
# This file is intentionally left empty to ensure the auth directory is included in the Git repository.
# The auth directory is used to store authentication-related templates for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/auth/change_password.html

```
{% extends "shared/base.html" %}

{% block title %}Change Password - DynaDash{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-md mx-auto px-4 sm:px-6 lg:px-8">
        <div class="shadow overflow-hidden sm:rounded-lg">
            <div class="px-4 py-5 sm:px-6">
                <h3 class="text-lg leading-6 font-medium">
                    Change Password
                </h3>
                <p class="mt-1 max-w-2xl text-sm text-text-secondary">
                    Update your account password.
                </p>
            </div>
            <div class="border-t border-border-color px-4 py-5 sm:px-6">
                <form action="{{ url_for('auth.change_password') }}" method="POST">
                    {{ form.hidden_tag() }}
                    
                    <div class="mb-4">
                        <label for="current_password" class="block text-sm font-medium">
                            {{ form.current_password.label }}
                        </label>
                        <div class="mt-1">
                            {{ form.current_password(class="shadow-sm focus:ring-magenta-primary focus:border-magenta-primary block w-full sm:text-sm rounded-md") }}
                            {% if form.current_password.errors %}
                                <div class="text-red-500 text-xs mt-1">
                                    {% for error in form.current_password.errors %}
                                        <span>{{ error }}</span>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        </div>
                    </div>
                    
                    <div class="mb-4">
                        <label for="new_password" class="block text-sm font-medium">
                            {{ form.new_password.label }}
                        </label>
                        <div class="mt-1">
                            {{ form.new_password(class="shadow-sm focus:ring-magenta-primary focus:border-magenta-primary block w-full sm:text-sm rounded-md") }}
                            {% if form.new_password.errors %}
                                <div class="text-red-500 text-xs mt-1">
                                    {% for error in form.new_password.errors %}
                                        <span>{{ error }}</span>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        </div>
                    </div>
                    
                    <div class="mb-6">
                        <label for="confirm_new_password" class="block text-sm font-medium">
                            {{ form.confirm_new_password.label }}
                        </label>
                        <div class="mt-1">
                            {{ form.confirm_new_password(class="shadow-sm focus:ring-magenta-primary focus:border-magenta-primary block w-full sm:text-sm rounded-md") }}
                            {% if form.confirm_new_password.errors %}
                                <div class="text-red-500 text-xs mt-1">
                                    {% for error in form.confirm_new_password.errors %}
                                        <span>{{ error }}</span>
                                    {% endfor %}
                                </div>
                            {% endif %}
                        </div>
                    </div>
                    
                    <div class="flex justify-end">
                        <a href="{{ url_for('auth.profile') }}" class="py-2 px-4 border border-border-color rounded-md shadow-sm text-sm font-medium hover:bg-highlight focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-magenta-primary mr-2">
                            Cancel
                        </a>
                        {{ form.submit(class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-magenta-primary") }}
                    </div>
                </form>
            </div>
        </div>
    </div>
</div>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/auth/login.html

```
{% extends "shared/base.html" %}

{% block title %}Login - DynaDash{% endblock %}

{% block content %}
<div class="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-card-bg p-8 rounded-lg shadow-md border border-border-color">
        <div>
            <h2 class="mt-6 text-center text-3xl font-extrabold">
                Login to DynaDash
            </h2>
            <p class="mt-2 text-center text-sm">
                Or
                <a href="{{ url_for('auth.register') }}" class="font-medium hover:text-magenta-secondary">
                    create a new account
                </a>
            </p>
        </div>
        <form class="mt-8 space-y-6" action="{{ url_for('auth.login') }}" method="POST">
            {{ form.hidden_tag() }}
            <div class="rounded-md shadow-sm -space-y-px">
                <div>
                    <label for="email" class="sr-only">Email address</label>
                    {{ form.email(class="appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-t-md focus:outline-none focus:z-10 sm:text-sm", placeholder="Email address") }}
                    {% if form.email.errors %}
                        <div class="text-red-500 text-xs mt-1">
                            {% for error in form.email.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
                <div>
                    <label for="password" class="sr-only">Password</label>
                    {{ form.password(class="appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-b-md focus:outline-none focus:z-10 sm:text-sm", placeholder="Password") }}
                    {% if form.password.errors %}
                        <div class="text-red-500 text-xs mt-1">
                            {% for error in form.password.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
            </div>

            <div class="flex items-center justify-between">
                <div class="flex items-center">
                    {{ form.remember_me(class="h-4 w-4 focus:ring-magenta-primary border rounded") }}
                    <label for="remember_me" class="ml-2 block text-sm">
                        Remember me
                    </label>
                </div>
            </div>

            <div>
                {{ form.submit(class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2") }}
            </div>
        </form>
    </div>
</div>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/auth/profile.html

```
{% extends "shared/base.html" %}

{% block title %}Profile - DynaDash{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="shadow overflow-hidden sm:rounded-lg">
            <div class="px-4 py-5 sm:px-6 flex justify-between items-center">
                <div>
                    <h3 class="text-lg leading-6 font-medium">
                        User Profile
                    </h3>
                    <p class="mt-1 max-w-2xl text-sm">
                        Your personal information and account details.
                    </p>
                </div>
                <a href="{{ url_for('auth.change_password') }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm">
                    Change Password
                </a>
            </div>
            <div class="border-t border-border-color">
                <dl>
                    <div class="px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6">
                        <dt class="text-sm font-medium text-text-secondary">
                            Full name
                        </dt>
                        <dd class="mt-1 text-sm sm:mt-0 sm:col-span-2">
                            {{ current_user.name }}
                        </dd>
                    </div>
                    <div class="px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 border-t border-border-color">
                        <dt class="text-sm font-medium text-text-secondary">
                            Email address
                        </dt>
                        <dd class="mt-1 text-sm sm:mt-0 sm:col-span-2">
                            {{ current_user.email }}
                        </dd>
                    </div>
                    <div class="px-4 py-5 sm:grid sm:grid-cols-3 sm:gap-4 sm:px-6 border-t border-border-color">
                        <dt class="text-sm font-medium text-text-secondary">
                            Account created
                        </dt>
                        <dd class="mt-1 text-sm sm:mt-0 sm:col-span-2">
                            {{ current_user.created_at.strftime('%B %d, %Y') }}
                        </dd>
                    </div>
                </dl>
            </div>
        </div>
        
        <div class="mt-8 grid grid-cols-1 gap-6 sm:grid-cols-2">
            <div class="shadow overflow-hidden sm:rounded-lg">
                <div class="px-4 py-5 sm:px-6">
                    <h3 class="text-lg leading-6 font-medium">
                        My Datasets
                    </h3>
                    <p class="mt-1 max-w-2xl text-sm text-text-secondary">
                        Summary of your uploaded datasets.
                    </p>
                </div>
                <div class="border-t border-border-color px-4 py-5 sm:px-6">
                    <div class="text-center">
                        <a href="{{ url_for('data.index') }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-magenta-primary">
                            View All Datasets
                        </a>
                    </div>
                </div>
            </div>
            
            <div class="shadow overflow-hidden sm:rounded-lg">
                <div class="px-4 py-5 sm:px-6">
                    <h3 class="text-lg leading-6 font-medium">
                        My Visualizations
                    </h3>
                    <p class="mt-1 max-w-2xl text-sm text-text-secondary">
                        Summary of your generated visualizations.
                    </p>
                </div>
                <div class="border-t border-border-color px-4 py-5 sm:px-6">
                    <div class="text-center">
                        <a href="{{ url_for('visual.index') }}" class="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-magenta-primary">
                            View All Visualizations
                        </a>
                    </div>
                </div>
            </div>
            
            <a href="#" onclick="confirmAndSubmit()" 
               class="justify-self-start inline-flex items-center px-2 py-2 border border-transparent text-sm font-medium rounded-md shadow-sm">
                Delete Account
            </a>

            <!-- hidden form (with CSRF) -->
            <form id="delete-account-form"
                action="{{ url_for('auth.delete_account') }}"
                method="POST"
                style="display: none;">
                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
            </form>

        </div>
    </div>
</div>

<!-- Account Delete Confirmation Modal -->
<div id="delete-account-modal"
     class="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center hidden z-50">
  <div class="bg-white rounded-lg shadow-lg p-6 max-w-md w-full">
    <h3 class="text-xl font-bold text-gray-800 mb-4">Confirm Deletion</h3>
    <p class="text-gray-600 mb-6">
      Are you sure you want to delete your account? All related data will be erased. This cannot be undone.
    </p>
    <div class="flex justify-end space-x-4">
      <button id="cancel-delete-account"
              class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded transition">
        Cancel
      </button>
      <button id="confirm-delete-account"
              class="bg-pink-600 hover:bg-red-700 text-white font-bold py-2 px-4 rounded transition">
        Delete
      </button>
    </div>
  </div>
</div>

<script  src="{{ url_for('static', filename='js/profile.js') }}" defer></script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/auth/register.html

```
{% extends "shared/base.html" %}

{% block title %}Register - DynaDash{% endblock %}

{% block content %}
<div class="min-h-screen flex items-center justify-center py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 bg-card-bg p-8 rounded-lg shadow-md border border-border-color">
        <div>
            <h2 class="mt-6 text-center text-3xl font-extrabold">
                Create an Account
            </h2>
            <p class="mt-2 text-center text-sm">
                Or
                <a href="{{ url_for('auth.login') }}" class="font-medium hover:text-magenta-secondary">
                    sign in to your existing account
                </a>
            </p>
        </div>
        <form class="mt-8 space-y-6" action="{{ url_for('auth.register') }}" method="POST">
            {{ form.hidden_tag() }}
            <div class="rounded-md shadow-sm -space-y-px">
                <div>
                    <label for="name" class="sr-only">Name</label>
                    {{ form.name(class="appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-t-md focus:outline-none focus:z-10 sm:text-sm", placeholder="User name") }}
                    {% if form.name.errors %}
                        <div class="text-red-500 text-xs mt-1">
                            {% for error in form.name.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
                <div>
                    <label for="email" class="sr-only">Email address</label>
                    {{ form.email(class="appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-md focus:outline-none focus:z-10 sm:text-sm", placeholder="Email address") }}
                    {% if form.email.errors %}
                        <div class="text-red-500 text-xs mt-1">
                            {% for error in form.email.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
                <div>
                    <label for="password" class="sr-only">Password</label>
                    {{ form.password(class="appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-md focus:outline-none focus:z-10 sm:text-sm", placeholder="Password") }}
                    {% if form.password.errors %}
                        <div class="text-red-500 text-xs mt-1">
                            {% for error in form.password.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
                <div>
                    <label for="confirm_password" class="sr-only">Confirm Password</label>
                    {{ form.confirm_password(class="appearance-none rounded-none relative block w-full px-3 py-2 border placeholder-gray-500 rounded-md focus:outline-none focus:z-10 sm:text-sm", placeholder="Confirm Password") }}
                    {% if form.confirm_password.errors %}
                        <div class="text-red-500 text-xs mt-1">
                            {% for error in form.confirm_password.errors %}
                                <span>{{ error }}</span>
                            {% endfor %}
                        </div>
                    {% endif %}
                </div>
            </div>

            <div>
                {{ form.submit(class="group relative w-full flex justify-center py-2 px-4 border border-transparent text-sm font-medium rounded-md focus:outline-none focus:ring-2 focus:ring-offset-2") }}
            </div>
        </form>
    </div>
</div>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/400.html

```
{% extends "errors/base_error.html" %}

{% set code = 400 %}
{% set title = "Bad Request" %}
{% set message = "The server could not understand your request. Please check your input and try again." %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/401.html

```
{% extends "errors/base_error.html" %}

{% set code = 401 %}
{% set title = "Unauthorized" %}
{% set message = "You need to be authenticated to access this resource. Please log in and try again." %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/403.html

```
{% extends "errors/base_error.html" %}

{% set code = 403 %}
{% set title = "Forbidden" %}
{% set message = "You don't have permission to access this resource. Please check your credentials or contact the administrator." %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/404.html

```
{% extends "errors/base_error.html" %}

{% set code = 404 %}
{% set title = "Page Not Found" %}
{% set message = "The page you are looking for does not exist. It might have been moved or deleted." %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/500.html

```
{% extends "errors/base_error.html" %}

{% set code = 500 %}
{% set title = "Internal Server Error" %}
{% set message = "Something went wrong on our end. Please try again later or contact support if the problem persists." %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/errors/base_error.html

```
{% extends "shared/base.html" %}

{% block title %}{{ code }} {{ title }} - DynaDash{% endblock %}

{% block content %}
<div class="min-h-screen flex items-center justify-center bg-gray-100 py-12 px-4 sm:px-6 lg:px-8">
    <div class="max-w-md w-full space-y-8 text-center">
        <div>
            <h1 class="text-9xl font-extrabold text-blue-600">{{ code }}</h1>
            <h2 class="mt-6 text-center text-3xl font-extrabold text-gray-900">
                {{ title }}
            </h2>
            <p class="mt-2 text-center text-sm text-gray-600">
                {{ message }}
            </p>
        </div>
        <div>
            <a href="{{ url_for('visual.index') if current_user.is_authenticated else url_for('auth.login') }}" class="inline-flex items-center px-4 py-2 border border-transparent text-base font-medium rounded-md shadow-sm text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500">
                Go to Home
            </a>
        </div>
    </div>
</div>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/shared/.gitkeep

```
# This file is intentionally left empty to ensure the shared directory is included in the Git repository.
# The shared directory is used to store shared templates that are used across multiple parts of the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/shared/base.html

```
<!DOCTYPE html>
<html lang="en">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>{% block title %}DynaDash{% endblock %}</title>
    
    <script src="https://cdn.tailwindcss.com"></script>
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/2.3.0/purify.min.js"></script>
    <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">

    {% block head_scripts %}
    {% if current_user.is_authenticated %}
    <script>
        window.dynadash_current_user_id = {{ current_user.id | tojson }};
    </script>
    {% else %}
    <script>
        window.dynadash_current_user_id = null;
    </script>
    {% endif %}
    {% endblock %}
    
    {% block styles %}{% endblock %}
</head>
<body class="min-h-screen flex flex-col">
    <nav class="fixed top-0 left-0 w-full text-white shadow-md z-50 h-16">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex justify-between h-16">
                <div class="flex">
                    <div class="flex-shrink-0 flex items-center">
                        <a href="{{ url_for('visual.index') if current_user.is_authenticated else url_for('visual.welcome') }}" class="font-bold text-xl">
                            DynaDash
                        </a>
                    </div>
                {% if current_user.is_authenticated %}
                   <div class="hidden sm:ml-6 sm:flex sm:space-x-8">
                    <a href="{{ url_for('visual.index') }}"
                       class="inline-flex items-center px-1 pt-1 text-sm font-medium {% if request.endpoint and request.endpoint.startswith('visual') %}border-b-2 border-magenta-primary{% else %}border-b-2 border-transparent{% endif %}">
                          Visualizations
                    </a>
                    {# Use the new context function to check if data blueprint routes exist #}
                    {% if data_blueprint_exists_and_has_route('index') %}
                    <a href="{{ url_for('data.index') }}"
                      class="inline-flex items-center px-1 pt-1 text-sm font-medium {% if request.endpoint and request.endpoint.startswith('data') and request.endpoint != 'data.upload' %}border-b-2 border-magenta-primary{% else %}border-b-2 border-transparent{% endif %}">
                        Datasets 
                    </a>
                    {% endif %}
                    {% if data_blueprint_exists_and_has_route('upload') %}
                    <a href="{{ url_for('data.upload') }}"
                        class="inline-flex items-center px-1 pt-1 text-sm font-medium {% if request.endpoint and request.endpoint == 'data.upload' %}border-b-2 border-magenta-primary{% else %}border-b-2 border-transparent{% endif %}">
                         Upload   
                    </a>
                    {% endif %}
                   </div>
                {% endif %}
                </div>
                <div class="hidden sm:ml-6 sm:flex sm:items-center">
                    {% if current_user.is_authenticated %}
                    <div class="ml-3 relative">
                        <div class="flex items-center">
                            <span class="mr-2 text-text-color">{{ current_user.name }}</span>
                            <div class="relative">
                                <button type="button" id="user-menu-button" class="flex text-sm rounded-full focus:outline-none">
                                    <span class="sr-only">Open user menu</span>
                                    <div class="h-8 w-8 rounded-full flex items-center justify-center">
                                        {{ current_user.name[0] }}
                                    </div>
                                </button>
                            </div>
                            <div id="user-menu" class="hidden absolute right-0 top-full mt-2 w-48 rounded-md shadow-xl z-50 py-1 focus:outline-none" role="menu" aria-orientation="vertical" aria-labelledby="user-menu-button" tabindex="-1">
                                <a href="{{ url_for('auth.profile') }}" class="block px-4 py-2 text-sm" role="menuitem">Your Profile</a>
                                <a href="{{ url_for('auth.change_password') }}" class="block px-4 py-2 text-sm" role="menuitem">Change Password</a>
                                <a href="{{ url_for('auth.logout') }}" class="block px-4 py-2 text-sm" role="menuitem">Sign out</a>
                            </div>
                        </div>
                    </div>
                    {% else %}
                    <div class="flex space-x-4">
                        <a href="{{ url_for('auth.login') }}" class="px-3 py-2 rounded-md text-sm font-medium">Login</a>
                        <a href="{{ url_for('auth.register') }}" class="bg-magenta-primary px-3 py-2 rounded-md text-sm font-medium">Register</a>
                    </div>
                    {% endif %}
                </div>
                <div class="-mr-2 flex items-center sm:hidden">
                    <button type="button" id="mobile-menu-button" class="inline-flex items-center justify-center p-2 rounded-md focus:outline-none">
                        <span class="sr-only">Open main menu</span>
                        <svg class="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>

        <div id="mobile-menu" class="hidden sm:hidden">
            <div class="pt-2 pb-3 space-y-1 px-2">
                {% if current_user.is_authenticated %}
                <a href="{{ url_for('visual.index') }}" class="{% if request.endpoint and request.endpoint == 'visual.index' %}bg-highlight{% else %}{% endif %} block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Visualizations
                </a>
                {% if data_blueprint_exists_and_has_route('index') %}
                <a href="{{ url_for('data.index') }}" class="{% if request.endpoint and request.endpoint.startswith('data') and request.endpoint != 'data.upload' %}bg-highlight{% else %}{% endif %} block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Datasets
                </a>
                {% endif %}
                {% if data_blueprint_exists_and_has_route('upload') %}
                <a href="{{ url_for('data.upload') }}" class="{% if request.endpoint and request.endpoint == 'data.upload' %}bg-highlight{% else %}{% endif %} block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Upload
                </a>
                {% endif %}
                {% else %}
                <a href="{{ url_for('auth.login') }}" class="block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Login
                </a>
                <a href="{{ url_for('auth.register') }}" class="block pl-3 pr-4 py-2 text-base font-medium rounded-md">
                    Register
                </a>
                {% endif %}
            </div>
            {% if current_user.is_authenticated %}
            <div class="pt-4 pb-3 border-t">
                <div class="flex items-center px-4">
                    <div class="flex-shrink-0">
                        <div class="h-10 w-10 rounded-full flex items-center justify-center">
                            {{ current_user.name[0] }}
                        </div>
                    </div>
                    <div class="ml-3">
                        <div class="text-base font-medium text-text-color">{{ current_user.name }}</div>
                        <div class="text-sm font-medium text-text-secondary">{{ current_user.email }}</div>
                    </div>
                </div>
                <div class="mt-3 space-y-1 px-2">
                    <a href="{{ url_for('auth.profile') }}" class="block px-4 py-2 text-base font-medium rounded-md">
                        Your Profile
                    </a>
                    <a href="{{ url_for('auth.change_password') }}" class="block px-4 py-2 text-base font-medium rounded-md">
                        Change Password
                    </a>
                    <a href="{{ url_for('auth.logout') }}" class="block px-4 py-2 text-base font-medium rounded-md">
                        Sign out
                    </a>
                </div>
            </div>
            {% endif %}
        </div>
    </nav>

    <div class="flash-messages">
        {% with messages = get_flashed_messages(with_categories=true) %}
            {% if messages %}
                {% for category, message in messages %}
                    <div class="flash-message flash-{{ category }}">
                        <span>{{ message }}</span>
                        <button type="button" class="close-flash ml-2">×</button>
                    </div>
                {% endfor %}
            {% endif %}
        {% endwith %}
    </div>

    <main class="flex-grow pt-16">
        {% block content %}{% endblock %}
    </main>

    <footer class="py-4 mt-8">
        <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
            <div class="flex flex-col sm:flex-row justify-between items-center text-center sm:text-left">
                <div class="text-sm mb-2 sm:mb-0">
                    © {% block current_year %}2025{% endblock %} DynaDash. All rights reserved.
                </div>
                <div class="text-sm">
                    Created by Matthew Haskins, Leo Chen, Jonas Liu, Ziyue Xu
                </div>
            </div>
        </div>
    </footer>
    
    <script src="{{ url_for('static', filename='js/common.js') }}" defer></script>

    {% block scripts %}{% endblock %}
</body>
</html>

```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/shared/error.html

```
{% extends "shared/base.html" %}

{% block title %}Error {{ error_code }} - DynaDash{% endblock %}

{% block content %}
<div class="flex flex-col items-center justify-center py-16 px-4">
    <div class="text-6xl font-bold mb-4 text-danger">{{ error_code }}</div>
    <h1 class="text-3xl font-bold mb-6 text-center">{{ error_message }}</h1>
    
    <p class="mb-8 text-center max-w-lg">
        {% if error_code == 404 %}
        The page you are looking for might have been removed, had its name changed, or is temporarily unavailable.
        {% elif error_code == 403 %}
        You don't have permission to access this resource.
        {% elif error_code == 500 %}
        Something went wrong on our end. Please try again later.
        {% else %}
        An error occurred while processing your request.
        {% endif %}
    </p>
    
    <div class="flex flex-col sm:flex-row space-y-4 sm:space-y-0 sm:space-x-4 w-full sm:w-auto">
        <a href="{{ url_for('visual.index') if current_user.is_authenticated else url_for('visual.welcome') }}" class="btn w-full sm:w-auto">
            Go to Home
        </a>
        <button onclick="window.history.back()" class="btn btn-secondary w-full sm:w-auto">
            Go Back
        </button>
    </div>
</div>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/shared/index.html

```
{% extends "shared/base.html" %}

{% block title %}DynaDash - Dynamic Data Analytics{% endblock %}

{% block head_scripts %}
    {{ super() }}
    <!-- Font Awesome for icons (moved from bottom to ensure it's loaded before body) -->
    <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous" defer></script>
{% endblock %}


{% block content %}
<div class="flex flex-col items-center justify-center py-12 px-4">
    <h1 class="text-5xl font-bold mb-6 text-center">Welcome to DynaDash</h1>
    <p class="text-xl lead mb-8 text-center max-w-3xl">
        A web-based data-analytics platform that lets you upload datasets, 
        receive automated visualizations powered by Claude AI, and share insights with your team.
    </p>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 w-full max-w-6xl mb-12">
        <!-- Feature 1 -->
        <div class="bg-white p-6 rounded-lg">
            <div class="text-magenta-primary text-4xl mb-4">
                <i class="fas fa-upload"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">Upload Datasets</h3>
            <p>
                Securely upload your CSV or JSON datasets and preview them instantly.
            </p>
        </div>
        
        <!-- Feature 2 -->
        <div class="bg-white p-6 rounded-lg">
            <div class="text-magenta-primary text-4xl mb-4">
                <i class="fas fa-chart-bar"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">AI-Powered Visualizations</h3>
            <p>
                Get automated exploratory analyses & visualizations generated by Claude AI.
            </p>
        </div>
        
        <!-- Feature 3 -->
        <div class="bg-white p-6 rounded-lg">
            <div class="text-magenta-primary text-4xl mb-4">
                <i class="fas fa-cubes"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">Manage Your Gallery</h3>
            <p>
                Curate, annotate & manage visualizations in your personal gallery.
            </p>
        </div>
        
        <!-- Feature 4 -->
        <div class="bg-white p-6 rounded-lg">
            <div class="text-magenta-primary text-4xl mb-4">
                <i class="fas fa-share-alt"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">Share Insights</h3>
            <p>
                Selectively share chosen datasets or charts with nominated peers.
            </p>
        </div>
    </div>
    
    {% if not current_user.is_authenticated %}
    <div class="flex flex-col md:flex-row gap-6">
        <a href="{{ url_for('auth.register') }}" class="btn">
            Register Now
        </a>
        <a href="{{ url_for('auth.login') }}" class="btn btn-secondary">
            Login
        </a>
    </div>
    {% else %}
    <div class="flex flex-col md:flex-row gap-6">
        <a href="{{ url_for('data.upload') }}" class="btn">
            Upload Dataset
        </a>
        <a href="{{ url_for('visual.index') }}" class="btn btn-secondary">
            View Visualizations
        </a>
    </div>
    {% endif %}
</div>

<!-- How It Works Section -->
<div class="bg-gray-50 py-16"> {# This bg-gray-50 will be themed by main.css #}
    <div class="container mx-auto px-4">
        <h2 class="text-3xl font-bold text-center mb-12">How It Works</h2>
        
        <div class="flex flex-col md:flex-row justify-between items-center mb-16">
            <div class="md:w-1/2 mb-8 md:mb-0 md:pr-8">
                <h3 class="text-2xl font-semibold mb-4">1. Upload Your Data</h3>
                <p class="mb-4">
                    Upload your CSV or JSON datasets securely to the platform. 
                    Our system validates your data and provides an instant preview.
                </p>
                <ul class="list-disc list-inside">
                    <li>Support for CSV and JSON formats</li>
                    <li>Secure file handling</li>
                    <li>Instant data preview</li>
                </ul>
            </div>
            <div class="md:w-1/2">
                <div class="bg-white p-4 rounded-lg"> {# Card style from main.css #}
                    <div class="bg-surface-1 h-64 rounded flex items-center justify-center"> {# Utility class for themed background #}
                        <span class="text-text-secondary">Upload Interface Mockup</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="flex flex-col md:flex-row justify-between items-center mb-16">
            <div class="md:w-1/2 md:order-2 mb-8 md:mb-0 md:pl-8">
                <h3 class="text-2xl font-semibold mb-4">2. Generate Visualizations</h3>
                <p class="mb-4">
                    Our AI-powered system analyzes your data and generates meaningful visualizations 
                    automatically using Anthropic's Claude API.
                </p>
                <ul class="list-disc list-inside">
                    <li>AI-powered data analysis</li>
                    <li>Multiple chart types</li>
                    <li>Real-time progress tracking</li>
                </ul>
            </div>
            <div class="md:w-1/2 md:order-1">
                <div class="bg-white p-4 rounded-lg"> {# Card style from main.css #}
                    <div class="bg-surface-1 h-64 rounded flex items-center justify-center"> {# Utility class for themed background #}
                        <span class="text-text-secondary">Visualization Process Mockup</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="flex flex-col md:flex-row justify-between items-center">
            <div class="md:w-1/2 mb-8 md:mb-0 md:pr-8">
                <h3 class="text-2xl font-semibold mb-4">3. Share and Collaborate</h3>
                <p class="mb-4">
                    Curate your visualizations in a personal gallery and selectively share them 
                    with team members for collaboration.
                </p>
                <ul class="list-disc list-inside">
                    <li>Fine-grained access control</li>
                    <li>Personal visualization gallery</li>
                    <li>Team collaboration features</li>
                </ul>
            </div>
            <div class="md:w-1/2">
                <div class="bg-white p-4 rounded-lg"> {# Card style from main.css #}
                    <div class="bg-surface-1 h-64 rounded flex items-center justify-center"> {# Utility class for themed background #}
                        <span class="text-text-secondary">Sharing Interface Mockup</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
{{ super() }}
{# Font Awesome script already moved to head_scripts for better practice #}
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/.gitkeep

```
# This file is intentionally left empty to ensure the visual directory is included in the Git repository.
# The visual directory is used to store visualization-related templates for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/generate.html

```
{% extends "shared/base.html" %}

{% block title %}Generate Dashboard - DynaDash{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-bold text-text-color">Generate Dashboard</h1>
            {# Ensure data.view exists or provide a fallback. text-blue-600 is themed to magenta by main.css #}
            <a href="{{ url_for('data.view', id=dataset.id) if 'data.view' in current_app.view_functions else url_for('visual.index') }}" class="text-blue-600 hover:text-blue-800">
                <i class="fas fa-arrow-left mr-1"></i> Back to Dataset
            </a>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Dataset Info Card -->
            <div class="md:col-span-1">
                {# .bg-white is themed to var(--card-bg) by main.css #}
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    {# .border-gray-200 is themed to var(--border-color) by main.css #}
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-text-color">Dataset Details</h2>
                    </div>
                    <div class="p-4">
                        {# Changed text-gray-200 to text-text-color for better theme alignment #}
                        <h3 class="font-medium text-text-color mb-1">{{ dataset.original_filename }}</h3>
                        {# .text-gray-500 is themed to var(--text-secondary) by main.css #}
                        <p class="text-sm text-gray-500 mb-4">
                            {{ dataset.file_type.upper() }} • {{ dataset.n_rows }} rows • {{ dataset.n_columns }} columns
                        </p>
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Uploaded:</span> {{ dataset.uploaded_at.strftime('%b %d, %Y') }}
                        </p>
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Visibility:</span> 
                            {# text-green-600 for public status is fine, uses --accent-green via Tailwind #}
                            <span class="{{ 'text-green-600' if dataset.is_public else 'text-text-color' }}">
                                {{ 'Public' if dataset.is_public else 'Private' }}
                            </span>
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Dashboard Form Card -->
            <div class="md:col-span-2">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-text-color">Dashboard Options</h2>
                    </div>
                    <div class="p-4">
                        <form method="POST" action="{{ url_for('visual.generate', dataset_id=dataset.id) }}" id="dashboard-form">
                            {{ form.hidden_tag() }}
                            
                            <div class="mb-4">
                                {# Rely on main.css for label styling; remove Tailwind classes #}
                                {{ form.title.label }}
                                <div class="mt-1">
                                    {# Rely on main.css for input styling; remove most Tailwind classes. Keep w-full if needed. #}
                                    {{ form.title(class="w-full", placeholder="Enter a title for your dashboard") }}
                                    {% if form.title.errors %}
                                        {# .text-red-500 is themed to var(--danger-light). Add invalid-feedback for potential icon/enhanced styling. #}
                                        <div class="invalid-feedback text-xs mt-1">
                                            {% for error in form.title.errors %}
                                                <span>{{ error }}</span>
                                            {% endfor %}
                                        </div>
                                    {% endif %}
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                {{ form.description.label }}
                                <div class="mt-1">
                                    {{ form.description(class="w-full", rows=3, placeholder="Describe what insights you're looking for or what aspects of the data you want to highlight...") }}
                                    {% if form.description.errors %}
                                        <div class="invalid-feedback text-xs mt-1">
                                            {% for error in form.description.errors %}
                                                <span>{{ error }}</span>
                                            {% endfor %}
                                        </div>
                                    {% endif %}
                                </div>
                                <p class="text-xs text-gray-500 mt-1">
                                    Adding a descriptive explanation of your data and what insights you're looking for will help generate more relevant visualizations.
                                </p>
                            </div>
                            
                            <div class="mb-6">
                                {# Use .alert .alert-info for the note box #}
                                <div class="alert alert-info">
                                    <span class="text-sm"> {# main.css alert styles will handle text color #}
                                        <strong>Note:</strong> Claude will analyze your dataset and automatically create a fully interactive dashboard with multiple visualizations. This process may take up to 60-90 seconds for larger datasets.
                                    </span>
                                </div>
                            </div>
                            
                            <div class="flex justify-end">
                                {# Use .btn class for the submit button #}
                                {{ form.submit(class="btn", value="Generate Dashboard", id="submit-button") }}
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Processing Modal -->
        <div id="processing-modal" class="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center hidden z-50">
            {# Modal content uses CSS variables from main.css, which is good #}
            <div class="bg-card-bg rounded-lg shadow-lg p-6 max-w-md w-full border border-border-color">
                <h3 class="text-xl font-bold text-text-color mb-4">Generating Dashboard</h3>
                <div class="mb-4">
                    {# progress-container and #progress-bar are styled by main.css #}
                    <div class="progress-container">
                        <div id="progress-bar" style="width: 0%"></div>
                    </div>
                    <p id="progress-label" class="text-sm text-text-secondary mt-2">Initializing...</p>
                </div>
                <div class="text-text-secondary text-sm">
                    <p class="mb-2">Claude is analyzing your data and creating a custom dashboard. This may take 60-90 seconds to complete.</p>
                    {# steps-container and step-indicator are styled by main.css #}
                    <div id="steps-container" class="border border-border-color rounded p-2 mt-3">
                        <p class="text-xs text-text-tertiary mb-1">Current progress:</p>
                        <ul class="text-xs space-y-1">
                            <li id="step-1" class="flex items-center">
                                <span class="step-indicator" id="step-1-indicator"></span> 
                                <span>Preparing dataset and analyzing structure</span>
                            </li>
                            <li id="step-2" class="flex items-center text-text-tertiary">
                                <span class="step-indicator" id="step-2-indicator"></span> 
                                <span>Identifying key data relationships</span>
                            </li>
                            <li id="step-3" class="flex items-center text-text-tertiary">
                                <span class="step-indicator" id="step-3-indicator"></span> 
                                <span>Generating dashboard layout</span>
                            </li>
                            <li id="step-4" class="flex items-center text-text-tertiary">
                                <span class="step-indicator" id="step-4-indicator"></span> 
                                <span>Creating visualizations</span>
                            </li>
                            <li id="step-5" class="flex items-center text-text-tertiary">
                                <span class="step-indicator" id="step-5-indicator"></span> 
                                <span>Finalizing and saving dashboard</span>
                            </li>
                        </ul>
                    </div>
                </div>
                {# Use .alert .alert-danger for modal error message #}
                <div id="error-message-modal" class="mt-4 alert alert-danger error-message hidden">
                    An error occurred. Please try again or contact support if the problem persists.
                </div>
            </div>
        </div>

    </div>
</div>
{% endblock %}

{% block scripts %}
{# visual_generate.js is NOT for this page, it's for view.html #}
{# Add specific JS for this page if needed, e.g. for handling form submission with SocketIO progress #}
<script>
document.addEventListener("DOMContentLoaded", function () {
    const dashboardForm = document.getElementById('dashboard-form');
    const processingModal = document.getElementById('processing-modal');
    const progressBar = document.getElementById('progress-bar');
    const progressLabel = document.getElementById('progress-label');
    const errorMessageModal = document.getElementById('error-message-modal');
    
    const steps = {
        1: { percent: 10, message: "Preparing dataset and analyzing structure", indicator: "step-1-indicator", text_el_id: "step-1" },
        2: { percent: 30, message: "Identifying key data relationships", indicator: "step-2-indicator", text_el_id: "step-2" },
        3: { percent: 50, message: "Generating dashboard layout", indicator: "step-3-indicator", text_el_id: "step-3" },
        4: { percent: 70, message: "Creating visualizations", indicator: "step-4-indicator", text_el_id: "step-4" },
        5: { percent: 90, message: "Finalizing and saving dashboard", indicator: "step-5-indicator", text_el_id: "step-5" }
    };

    function updateStepIndicator(currentPercent) {
        for (const stepNum in steps) {
            const step = steps[stepNum];
            const indicatorEl = document.getElementById(step.indicator);
            const textEl = document.getElementById(step.text_el_id);
            if (indicatorEl && textEl) {
                // Add 'step-active' for the current step based on percentage range
                let isActive = false;
                if (stepNum < Object.keys(steps).length) {
                     const nextStepPercent = steps[parseInt(stepNum) + 1] ? steps[parseInt(stepNum) + 1].percent : 100;
                     isActive = currentPercent >= step.percent && currentPercent < nextStepPercent;
                } else { // Last step
                     isActive = currentPercent >= step.percent;
                }

                if (currentPercent >= step.percent) {
                    indicatorEl.classList.remove('bg-gray-300'); // remove explicit tailwind class if present
                    indicatorEl.classList.add('step-completed');
                    textEl.classList.remove('text-text-tertiary');
                    textEl.classList.add('text-text-color'); // Or specific class for completed text
                    if (isActive) {
                        indicatorEl.classList.add('step-active');
                        textEl.classList.add('active'); // Assuming .active is styled in CSS
                    } else {
                         indicatorEl.classList.remove('step-active');
                         textEl.classList.remove('active');
                    }
                } else {
                     indicatorEl.classList.remove('step-completed', 'step-active');
                     // indicatorEl.classList.add('bg-gray-300'); // Not needed if default is styled by main.css
                     textEl.classList.remove('text-text-color', 'active');
                     textEl.classList.add('text-text-tertiary');
                }
            }
        }
    }


    if (dashboardForm && processingModal && progressBar && progressLabel) {
        dashboardForm.addEventListener('submit', function(event) {
            processingModal.classList.remove('hidden');
            progressBar.style.width = '0%';
            progressLabel.textContent = 'Initializing...';
            if(errorMessageModal) {
                 errorMessageModal.classList.add('hidden');
                 // Clear previous text if any, main.css might use :before for icon
                 errorMessageModal.textContent = 'An error occurred. Please try again or contact support if the problem persists.';
            }
            updateStepIndicator(0); 
        });
    }
});
</script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/index.html

```
{% extends "shared/base.html" %}

{% block title %}My Visualizations - DynaDash{% endblock %}

{% block content %}
{# This page is currently minimal. If content is added, ensure it uses themed styles. #}
{# For example, a list of visualizations would use themed cards. #}
<div class="py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center mb-6">
            <h1 class="text-3xl font-bold text-text-color">My Dashboards</h1>
            {# Example button to create new dashboard, linking to upload or a generation page #}
            <a href="{{ url_for('data.upload') }}" class="btn">
                <i class="fas fa-plus mr-2"></i> Create New Dashboard
            </a>
        </div>

        {% if visualisations and visualisations.items %}
            <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6">
                {% for vis in visualisations.items %}
                    <div class="bg-card-bg shadow-md rounded-lg overflow-hidden border border-border-color flex flex-col">
                        <div class="p-4 border-b border-border-color">
                            <h2 class="text-lg font-semibold text-text-color truncate" title="{{ vis.title }}">{{ vis.title }}</h2>
                        </div>
                        <div class="p-4 flex-grow">
                            {% if vis.description %}
                                <p class="text-sm text-text-secondary mb-3 h-16 overflow-hidden text-ellipsis">{{ vis.description }}</p>
                            {% else %}
                                <p class="text-sm text-text-tertiary mb-3 h-16 italic">No description provided.</p>
                            {% endif %}
                            <p class="text-xs text-text-tertiary">
                                Dataset: <span class="font-medium text-text-secondary">{{ vis.dataset.original_filename }}</span>
                            </p>
                            <p class="text-xs text-text-tertiary">
                                Created: <span class="font-medium text-text-secondary">{{ vis.created_at.strftime('%b %d, %Y %H:%M') }}</span>
                            </p>
                        </div>
                        <div class="p-4 bg-surface-1 border-t border-border-color flex justify-end space-x-2">
                            <a href="{{ url_for('visual.view', id=vis.id) }}" class="btn btn-secondary btn-sm">
                                <i class="fas fa-eye mr-1"></i> View
                            </a>
                             {% if vis.dataset.user_id == current_user.id %}
                            <a href="{{ url_for('visual.share', id=vis.id) }}" class="btn btn-accent-green btn-sm">
                                <i class="fas fa-share-alt mr-1"></i> Share
                            </a>
                            <form action="{{ url_for('visual.delete', id=vis.id) }}" method="POST" class="inline m-0" onsubmit="return confirm('Are you sure you want to delete this dashboard?');">
                                <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                                <button type="submit" class="btn btn-danger btn-sm">
                                    <i class="fas fa-trash-alt mr-1"></i> Delete
                                </button>
                            </form>
                            {% endif %}
                        </div>
                    </div>
                {% endfor %}
            </div>
            
            {# Pagination #}
            {% if visualisations.has_prev or visualisations.has_next %}
            <div class="mt-8 flex justify-center">
                <nav aria-label="Pagination">
                    <ul class="inline-flex items-center -space-x-px shadow-sm">
                        {% if visualisations.has_prev %}
                        <li>
                            <a href="{{ url_for('visual.index', page=visualisations.prev_num) }}" class="btn btn-secondary btn-sm rounded-r-none">
                                <i class="fas fa-chevron-left mr-1"></i> Previous
                            </a>
                        </li>
                        {% endif %}
                        {% for page_num in visualisations.iter_pages(left_edge=1, right_edge=1, left_current=1, right_current=2) %}
                            {% if page_num %}
                                {% if visualisations.page == page_num %}
                                <li>
                                    <a href="#" class="btn btn-sm rounded-none" aria-current="page">{{ page_num }}</a>
                                </li>
                                {% else %}
                                <li>
                                    <a href="{{ url_for('visual.index', page=page_num) }}" class="btn btn-secondary btn-sm rounded-none">{{ page_num }}</a>
                                </li>
                                {% endif %}
                            {% else %}
                                <li><span class="btn btn-secondary btn-sm rounded-none disabled">...</span></li>
                            {% endif %}
                        {% endfor %}
                        {% if visualisations.has_next %}
                        <li>
                            <a href="{{ url_for('visual.index', page=visualisations.next_num) }}" class="btn btn-secondary btn-sm rounded-l-none">
                                Next <i class="fas fa-chevron-right ml-1"></i>
                            </a>
                        </li>
                        {% endif %}
                    </ul>
                </nav>
            </div>
            {% endif %}

        {% else %}
            <div class="bg-card-bg border border-border-color rounded-lg p-12 text-center">
                <div class="text-text-tertiary text-5xl mb-4">
                    <i class="fas fa-chart-bar"></i>
                </div>
                <h2 class="text-2xl font-semibold text-text-color mb-3">No Dashboards Yet</h2>
                <p class="text-text-secondary mb-6">
                    It looks like you haven't created or been shared any dashboards.
                </p>
                <a href="{{ url_for('data.upload') }}" class="btn">
                    <i class="fas fa-plus mr-2"></i> Create Your First Dashboard
                </a>
            </div>
        {% endif %}
    </div>
</div>
<script src="{{ url_for('static', filename='js/visual.js') }}"></script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/share.html

```
{% extends "shared/base.html" %}

{% block title %}Share Visualization - DynaDash{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-4xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex items-center justify-between mb-6">
            <h1 class="text-3xl font-bold text-text-color">Share Visualization</h1>
            {# text-blue-600 is themed to magenta by main.css #}
            <a href="{{ url_for('visual.view', id=visualisation.id) }}" class="text-blue-600 hover:text-blue-800">
                <i class="fas fa-arrow-left mr-1"></i> Back to Visualization
            </a>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Visualization Info Card -->
            <div class="md:col-span-1">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-text-color">Visualization Details</h2>
                    </div>
                    <div class="p-4">
                        {# Changed text-gray-200 to text-text-color #}
                        <h3 class="font-medium text-text-color mb-1">{{ visualisation.title }}</h3>
                        {% if visualisation.description %}
                            <p class="text-sm text-gray-500 mb-4">{{ visualisation.description }}</p>
                        {% endif %}
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Created:</span> {{ visualisation.created_at.strftime('%b %d, %Y') }}
                        </p>
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Dataset:</span> {{ dataset.original_filename }}
                        </p>
                        
                        <div class="mt-4 p-2 bg-surface-1 rounded"> {# Changed bg-gray-50 to bg-surface-1 #}
                            <div class="text-xs text-gray-500 mb-1">Preview:</div>
                            {# Changed bg-gray-100 to bg-surface-2 #}
                            <div class="h-32 flex items-center justify-center bg-surface-2 rounded">
                                <span class="text-text-tertiary text-sm">Visualization Preview</span> {# text-gray-400 themed to text-secondary, text-tertiary might be better #}
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Share Form Card -->
            <div class="md:col-span-2">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-text-color">Share with Users</h2>
                    </div>
                    <div class="p-4">
                        <form method="POST" action="{{ url_for('visual.share', id=visualisation.id) }}">
                            {{ form.hidden_tag() }}
                            
                            <div class="mb-6">
                                {# Rely on main.css for label styling #}
                                {{ form.user_id.label }}
                                <div class="mt-1">
                                    {# Rely on main.css for select styling #}
                                    {{ form.user_id(class="w-full") }}
                                    {% if form.user_id.errors %}
                                        <div class="invalid-feedback text-xs mt-1">
                                            {% for error in form.user_id.errors %}
                                                <span>{{ error }}</span>
                                            {% endfor %}
                                        </div>
                                    {% endif %}
                                </div>
                            </div>
                            
                            <div class="flex justify-end">
                                {# Use .btn class for submit #}
                                {{ form.submit(class="btn") }}
                            </div>
                        </form>
                        
                        <div class="mt-8">
                            <h3 class="text-lg font-medium text-text-color mb-4">Currently Shared With</h3>
                            
                            {% if shared_with %}
                                {# Table styling will be largely handled by main.css `table` selector #}
                                <div class="overflow-x-auto"> {# Wrapper for responsiveness #}
                                    <table class="min-w-full">
                                        <thead> {# Removed bg-gray-50, main.css table th has bg #}
                                            <tr>
                                                {# text-gray-500 themed to text-secondary #}
                                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    User
                                                </th>
                                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Actions
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody> {# Removed bg-white and divide-y, main.css table handles this #}
                                            {% for user_share in shared_with %} {# Assuming shared_with is a list of User objects or similar #}
                                                <tr>
                                                    <td class="px-6 py-4 whitespace-nowrap">
                                                        <div class="flex items-center">
                                                            {# Changed bg-gray-200 to bg-surface-3 for avatar placeholder #}
                                                            <div class="flex-shrink-0 h-10 w-10 bg-surface-3 rounded-full flex items-center justify-center">
                                                                <span class="text-text-color">{{ user_share.name[0] }}</span>
                                                            </div>
                                                            <div class="ml-4">
                                                                {# text-gray-900 themed to text-text-color #}
                                                                <div class="text-sm font-medium text-gray-900">
                                                                    {{ user_share.name }}
                                                                </div>
                                                                <div class="text-sm text-gray-500">
                                                                    {{ user_share.email }}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                        {# text-red-600 themed to var(--danger). text-danger provided by main.css for links. #}
                                                        <form action="{{ url_for('visual.unshare', id=visualisation.id, user_id=user_share.id) }}" method="POST" class="inline">
                                                            <button type="submit" class="text-danger hover:text-danger-dark">
                                                                Remove
                                                            </button>
                                                        </form>
                                                    </td>
                                                </tr>
                                            {% endfor %}
                                        </tbody>
                                    </table>
                                </div>
                            {% else %}
                                {# Changed bg-gray-50 to bg-surface-1 #}
                                <div class="bg-surface-1 rounded-lg p-6 text-center">
                                    <div class="text-text-tertiary text-4xl mb-3"> {# text-gray-400 themed to text-secondary, text-tertiary for icon #}
                                        <i class="fas fa-users-slash"></i>
                                    </div>
                                    {# text-gray-600 themed to text-secondary #}
                                    <p class="text-gray-600">
                                        This visualization is not shared with anyone yet.
                                    </p>
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                {# Use .alert .alert-info for the sharing information box #}
                <div class="mt-6 alert alert-info">
                    <h3 class="text-lg font-semibold mb-2">Sharing Information</h3> {# Alert styles will color this #}
                    <ul class="list-disc list-inside space-y-1"> {# Alert styles will color this #}
                        <li>Shared users can view but not modify your visualization</li>
                        <li>You can revoke access at any time</li>
                        <li>Users will be notified when you share a visualization with them</li>
                        <li>The dataset used to create this visualization will also be accessible to shared users</li>
                    </ul>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
{# FontAwesome is usually included in base.html, but if not, keep it. #}
{# <script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script> #}
<script src="{{ url_for('static', filename='js/visual.js') }}"></script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/view.html

```
{% extends "shared/base.html" %}

{% block title %}{{ visualisation.title }} - DynaDash{% endblock %}

{% block head_scripts %} {# Changed from 'head' to 'head_scripts' to match base.html #}
    {{ super() }}
    <style>
        .dashboard-frame { width: 100%; height: 800px; min-height: 800px; border: none; background-color: var(--card-bg); } /* Changed background to var(--card-bg) */
        .dashboard-frame canvas { max-width: 100%; }
        .dashboard-container { height: auto; min-height: 800px; position: relative; width: 100%; }
        .fullscreen-toggle { position: absolute; top: 10px; right: 10px; z-index: 100; padding: 5px 10px; background-color: rgba(0,0,0,0.5); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
        .fullscreen-container { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 9999; background-color: var(--card-bg); display: none; } /* Changed background */
        .fullscreen-container .dashboard-frame { height: 100%; width: 100%; }
        .fullscreen-container .fullscreen-toggle { top: 20px; right: 20px; }
        .dashboard-error { padding: 20px; text-align: center; background-color: rgba(var(--danger-rgb), 0.1); border: 1px solid var(--danger); border-radius: var(--radius-md); margin: 20px 0; } /* Themed error box */
        .dashboard-error h3 { color: var(--danger); margin-bottom: 10px; }
        .dashboard-error p { color: var(--text-secondary); margin-bottom: 15px; } /* Themed paragraph */
        .dashboard-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; }
        .spinner { border: 4px solid var(--surface-3); width: 40px; height: 40px; border-radius: 50%; border-left-color: var(--magenta-primary); animation: spin 1s ease infinite; margin-bottom: 15px; } /* Themed spinner */
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .lg\:col-span-3 { width: 100%; }
    </style>
    <script>
        window.dynadashDatasetJson = {{ actual_dataset_json|safe }};
        window.dynadashDashboardTemplateHtml = {{ dashboard_template_html|tojson|safe }};
    </script>
{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex flex-wrap justify-between items-center mb-6 gap-4"> {# Added flex-wrap and gap for responsiveness #}
            <div>
                <h1 class="text-3xl font-bold text-text-color">{{ visualisation.title }}</h1>
                {% if visualisation.description %}
                    <p class="text-text-secondary mt-1">{{ visualisation.description }}</p>
                {% endif %}
            </div>
            <div class="flex space-x-3 flex-wrap gap-2"> {# Added flex-wrap and gap for responsiveness #}
                <a href="{{ url_for('visual.index') }}" class="btn btn-secondary">
                    <i class="fas fa-arrow-left mr-1"></i> Back to Dashboards
                </a>
                
                {% if dataset.user_id == current_user.id %}
                    {# Assuming btn-success is green as per main.css themeing strategy #}
                    <a href="{{ url_for('visual.share', id=visualisation.id) }}" class="btn btn-success">
                        <i class="fas fa-share-alt mr-1"></i> Share
                    </a>
                    
                    <form action="{{ url_for('visual.delete', id=visualisation.id) }}" method="POST" class="inline m-0">
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        {# Assuming btn-danger is red #}
                        <button type="submit" class="btn btn-danger" 
                                onclick="return confirm('Are you sure you want to delete this dashboard? This action cannot be undone.');">
                            <i class="fas fa-trash-alt mr-1"></i> Delete
                        </button>
                    </form>
                {% endif %}
            </div>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div class="lg:col-span-1">
                {# Card uses direct CSS variables from main.css, which is good #}
                <div class="bg-card-bg shadow-md rounded-lg overflow-hidden mb-6 border border-border-color">
                    <div class="p-4 border-b border-border-color">
                        <h2 class="text-lg font-semibold text-text-color">Dashboard Details</h2>
                    </div>
                    <div class="p-4">
                        <ul class="space-y-3">
                            <li class="flex justify-between">
                                <span class="text-text-secondary">Created:</span>
                                <span class="font-medium text-text-color-muted">{{ visualisation.created_at.strftime('%b %d, %Y') }}</span>
                            </li>
                            <li class="flex justify-between">
                                <span class="text-text-secondary">Dataset:</span>
                                {# text-magenta-primary is good use of CSS var #}
                                <a href="{{ url_for('data.view', id=dataset.id) if 'data.view' in current_app.view_functions else '#' }}" class="font-medium text-magenta-primary hover:text-magenta-light">
                                    {{ dataset.original_filename }}
                                </a>
                            </li>
                            <li class="flex justify-between">
                                <span class="text-text-secondary">Owner:</span>
                                <span class="font-medium text-text-color-muted">{{ dataset.owner.name }}</span>
                            </li>
                        </ul>
                    </div>
                </div>
                
                <div class="bg-card-bg shadow-md rounded-lg overflow-hidden border border-border-color">
                    <div class="p-4 border-b border-border-color">
                        <h2 class="text-lg font-semibold text-text-color">Actions</h2>
                    </div>
                    <div class="p-4 space-y-3">
                        {% if dataset.user_id == current_user.id %}
                            <a href="{{ url_for('visual.share', id=visualisation.id) }}" class="btn btn-success w-full text-center">
                                <i class="fas fa-share-alt mr-1"></i> Share Dashboard
                            </a>
                        {% endif %}
                        
                        {# Assuming btn-accent-blue, btn-accent-purple, btn-accent-cyan are defined or bg-accent-* classes work correctly with .btn #}
                        <a href="{{ url_for('data.view', id=dataset.id) if 'data.view' in current_app.view_functions else '#' }}" class="btn btn-accent-blue w-full text-center">
                            <i class="fas fa-database mr-1"></i> View Dataset
                        </a>
                        
                        <button id="fullscreen-btn" class="btn btn-accent-purple w-full text-center">
                            <i class="fas fa-expand mr-1"></i> Fullscreen Mode
                        </button>
                        
                        {# bg-gray-500 button changed to btn-secondary #}
                        <button id="download-btn-dashboard" class="btn btn-secondary w-full text-center">
                            <i class="fas fa-download mr-1"></i> Download HTML
                        </button>
                        
                        <button id="refresh-btn-dashboard" class="btn btn-accent-cyan w-full text-center">
                            <i class="fas fa-sync-alt mr-1"></i> Refresh Dashboard
                        </button>
                    </div>
                </div>
            </div>
            
            <div class="lg:col-span-3">
                <div class="bg-card-bg shadow-md rounded-lg overflow-hidden w-full border border-border-color">
                    <div class="p-4 border-b border-border-color">
                        <h2 class="text-lg font-semibold text-text-color">Dashboard</h2>
                    </div>
                    <div class="dashboard-container">
                        <div id="dashboard-loading" class="dashboard-loading">
                            <div class="spinner"></div>
                            <p class="text-text-secondary">Loading dashboard...</p>
                        </div>
                        
                        <div id="dashboard-error" class="dashboard-error" style="display: none;">
                            <h3><i class="fas fa-exclamation-circle"></i> Dashboard Display Issue</h3>
                            <p>There was a problem displaying the dashboard. This may be due to browser security restrictions or a temporary issue.</p> {# Removed text-text-secondary as dashboard-error p handles color #}
                            <div>
                                <button id="reload-dashboard-btn" class="btn btn-accent-blue">
                                    <i class="fas fa-sync-alt mr-1"></i> Try Again
                                </button>
                                <a href="{{ url_for('visual.view', id=visualisation.id) }}" class="btn btn-secondary ml-2">
                                    <i class="fas fa-arrow-right mr-1"></i> Reload Page
                                </a>
                            </div>
                        </div>
                        
                        <iframe id="dashboard-frame" class="dashboard-frame" style="display: none;" 
                                sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads"></iframe>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>

<div id="fullscreen-container" class="fullscreen-container">
    <button id="exit-fullscreen-btn" class="fullscreen-toggle">
        <i class="fas fa-compress"></i> Exit Fullscreen
    </button>
    <iframe id="fullscreen-frame" class="dashboard-frame" 
            sandbox="allow-scripts allow-same-origin allow-popups allow-forms allow-downloads"></iframe>
</div>
{% endblock %}

{% block scripts %}
    <script src="{{ url_for('static', filename='js/dashboard_renderer.js') }}" defer></script>
    <script src="{{ url_for('static', filename='js/visual.js') }}" defer></script> 
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/welcome.html

```
{% extends "shared/base.html" %}

{% block content %}
<div class="flex flex-col items-center justify-center min-h-screen text-center px-4 space-y-8 pt-12">
    {# text-blue-600 is themed to magenta by main.css, including text-shadow effects #}
    <h1 class="text-5xl font-extrabold text-blue-600">Say Hello to DynaDash!</h1>
    
    {# text-gray-700 is themed to text-secondary #}
    <p class="text-lg text-gray-700 max-w-3xl">
        Ever wished your data could tell its own story? With DynaDash, upload your private datasets and watch as Claude magically crafts eye-catching charts and insights. Curate your favourites, share them with friends, and explore data like never before—all in a flash!
    </p>

    <div class="grid grid-cols-1 md:grid-cols-2 gap-6 max-w-4xl w-full mx-auto">
    {% for feature in [
      { 'icon': '🔐', 'title': 'Secure Login',       'desc': 'Sign in to keep your data safe and personal.' },
      { 'icon': '📁', 'title': 'Easy Uploads',        'desc': 'Drag, drop or select CSV/JSON files in a snap.' },
      { 'icon': '🤖', 'title': 'Automated Charts',    'desc': 'Let Claude whip up visuals while you grab a coffee.' },
      { 'icon': '🔄', 'title': 'Live Updates',        'desc': 'Track processing in real time with Socket.IO.' },
      { 'icon': '🤝', 'title': 'Share & Collaborate', 'desc': 'Pick datasets or charts and share with your crew.' },
      { 'icon': '📱', 'title': 'Fully Responsive',    'desc': 'Looks great on any device, thanks to Tailwind CSS.' }
    ] %}
        {# .bg-white is themed to var(--card-bg) #}
        {# Replaced Tailwind ring and drop-shadow with main.css themed shadow-glow on hover #}
        <div class="relative group
                    bg-white rounded-2xl 
                    transform hover:-translate-y-1
                    transition-transform duration-300 
                    ring-0 group-hover:shadow-glow-intense {# Use main.css glow #}
                    ring-offset-2 ring-offset-gray-900 {# ring-offset might need adjustment with shadow glow #}
                    overflow-hidden"
        >
            <div class="h-32 flex items-center justify-center">
                 {# group-hover:!text-pink-600 changed to group-hover:text-magenta-primary for consistency #}
                <h2 class="text-2xl font-semibold group-hover:text-magenta-primary transition-colors duration-200">
                  {{ feature.icon }} {{ feature.title }}
                </h2>
            </div>
            <div
                class="absolute left-0 right-0 bottom-0
                       opacity-0 group-hover:opacity-100
                       transition-opacity duration-700 ease-in-out
                       px-6 pb-4
                       group-hover:delay-150
                       shadow-inner"
            >
                {# text-gray-300 is a light gray, suitable on dark card. Corresponds to text-text-color-muted or lighter. #}
                <p class="text-text-color-muted"> 
                   {{ feature.desc }}
                </p>
            </div>
        </div>
    {% endfor %}
    </div>
</div>
{% endblock %}
```
