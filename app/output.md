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
from flask import Flask, redirect, url_for, request # Removed flask_current_app alias as it's not needed here
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

    # Initialize extensions with app
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
        # Use Flask's default logger which logs to stderr in debug mode
        app.logger.setLevel(logging.DEBUG)
        # Example of adding a stream handler if more control is needed in dev
        # console_handler = logging.StreamHandler()
        # console_formatter = logging.Formatter('%(asctime)s - %(name)s - %(levelname)s - %(message)s')
        # console_handler.setFormatter(console_formatter)
        # app.logger.addHandler(console_handler)
        app.logger.info(f"DynaDash starting in {config_name} mode (DEBUG={app.debug}, TESTING={app.testing})")
    else:
        logs_dir_config = app.config.get('LOGS_DIR')
        if logs_dir_config:
            logs_dir = logs_dir_config
        elif os.path.isabs(os.path.join(app.root_path, '..', 'logs')): # if app is a subdir
            logs_dir = os.path.join(app.root_path, '..', 'logs')
        else: # default to logs dir at project root
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
            app.logger.info(
                f'{request.method} {request.path} from {request.remote_addr} '
                f'user={getattr(current_user, "id", "anonymous")}'
            )
    
    upload_folder_path = app.config.get('UPLOAD_FOLDER', 'uploads')
    if not os.path.isabs(upload_folder_path):
        # Using app.instance_path is generally preferred for user-uploaded content
        # as it's outside the app package.
        upload_folder_path = os.path.join(app.instance_path, upload_folder_path) 
    
    # Ensure the directory for uploads exists (including parent if using instance_path)
    if not os.path.exists(os.path.dirname(upload_folder_path)):
         os.makedirs(os.path.dirname(upload_folder_path), exist_ok=True)
    os.makedirs(upload_folder_path, exist_ok=True)
    app.config['UPLOAD_FOLDER'] = upload_folder_path

    from .blueprints.auth import auth as auth_blueprint
    app.register_blueprint(auth_blueprint)
    
    try:
        from .blueprints.data import data as data_blueprint
        app.register_blueprint(data_blueprint)
        app.logger.info("Data blueprint registered.")
    except ImportError:
        app.logger.warning("Data blueprint (app.blueprints.data) not found or could not be imported. Skipping registration.")
    except Exception as e: # Catch other potential errors during data blueprint registration
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
    def inject_csrf_token():
        return dict(csrf_token=generate_csrf)

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
/* DynaDash Main Stylesheet */

/* Global Reset */
* {
    margin: 0;
    padding: 0;
    box-sizing: border-box;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

:root {
    /* Core Colors - Enhanced Palette */
    --dark-bg: #1a1a1a;
    --darker-bg: #121212;
    --darkest-bg: #0a0a0a;
    --card-bg: #242424;
    --card-bg-hover: #2a2a2a;
    --card-bg-active: #303030;
    --surface-1: #1e1e1e;
    --surface-2: #282828;
    --surface-3: #323232;
    --surface-4: #3d3d3d;
    
    /* Text Colors */
    --text-color: #f2f2f2;
    --text-color-muted: #d4d4d4;
    --text-secondary: #b8b8b8;
    --text-tertiary: #909090;
    --text-disabled: #707070;
    --text-inverse: #121212;
    
    /* Magenta Palette */
    --magenta-primary: #e83e8c;
    --magenta-light: #ff4fa3;
    --magenta-lighter: #ff7db8;
    --magenta-dark: #c01b65;
    --magenta-darker: #9c1452;
    --magenta-muted: #a51d5d;
    --magenta-secondary: #800335;
    --magenta-glow: rgba(232, 62, 140, 0.6);
    --magenta-glow-strong: rgba(232, 62, 140, 0.8);
    --magenta-glow-subtle: rgba(232, 62, 140, 0.3);
    --magenta-glow-faint: rgba(232, 62, 140, 0.15);
    
    /* Accent Colors */
    --accent-blue: #4285f4;
    --accent-blue-light: #6ea8fe;
    --accent-blue-dark: #1a73e8;
    --accent-cyan: #2bc4e9;
    --accent-cyan-light: #5bd1ef;
    --accent-cyan-dark: #0ba9d4;
    --accent-purple: #9c27b0;
    --accent-purple-light: #bb47d3;
    --accent-purple-dark: #7b1fa2;
    --accent-green: #28a745;
    --accent-green-light: #48c565;
    --accent-green-dark: #1e7e34;
    --accent-amber: #ffc107;
    --accent-amber-light: #ffcd39;
    --accent-amber-dark: #d39e00;
    --accent-red: #dc3545;
    --accent-red-light: #e35d6a;
    --accent-red-dark: #bd2130;
    
    /* Interface Colors */
    --border-color: #333;
    --border-color-light: #444;
    --border-color-lighter: #555;
    --border-color-focus: #666;
    --highlight: #2d2d2d;
    --highlight-hover: #3a3a3a;
    --highlight-active: #404040;
    --divider: rgba(255, 255, 255, 0.1);
    --divider-subtle: rgba(255, 255, 255, 0.05);
    
    /* Status Colors */
    --success: #28a745;
    --success-light: #48c565;
    --success-dark: #1e7e34;
    --warning: #ffc107;
    --warning-light: #ffcd39;
    --warning-dark: #d39e00;
    --danger: #dc3545;
    --danger-light: #e35d6a;
    --danger-dark: #bd2130;
    --info: var(--magenta-light);
    --info-light: var(--magenta-lighter);
    --info-dark: var(--magenta-dark);
    
    /* Shadows - Enhanced Depth */
    --shadow-xs: 0 1px 3px rgba(0, 0, 0, 0.15);
    --shadow-sm: 0 2px 8px rgba(0, 0, 0, 0.2);
    --shadow-md: 0 4px 16px rgba(0, 0, 0, 0.3);
    --shadow-lg: 0 8px 24px rgba(0, 0, 0, 0.4);
    --shadow-xl: 0 12px 32px rgba(0, 0, 0, 0.5);
    --shadow-2xl: 0 16px 48px rgba(0, 0, 0, 0.6);
    --shadow-inset: inset 0 2px 4px rgba(0, 0, 0, 0.3);
    --shadow-inset-deep: inset 0 3px 6px rgba(0, 0, 0, 0.4);
    --shadow-glow: 0 0 15px var(--magenta-glow);
    --shadow-glow-intense: 0 0 20px var(--magenta-glow-strong);
    --shadow-glow-subtle: 0 0 12px var(--magenta-glow-subtle);
    --shadow-glow-faint: 0 0 8px var(--magenta-glow-faint);
    
    /* Gradients */
    --gradient-bg: linear-gradient(135deg, var(--darker-bg) 0%, var(--dark-bg) 100%);
    --gradient-card: linear-gradient(160deg, var(--card-bg) 0%, var(--card-bg-hover) 100%);
    --gradient-card-hover: linear-gradient(160deg, var(--card-bg-hover) 0%, var(--card-bg-active) 100%);
    --gradient-magenta: linear-gradient(90deg, var(--magenta-primary) 0%, var(--magenta-light) 100%);
    --gradient-magenta-dark: linear-gradient(90deg, var(--magenta-dark) 0%, var(--magenta-primary) 100%);
    --gradient-magenta-subtle: linear-gradient(90deg, rgba(232, 62, 140, 0.8) 0%, rgba(255, 79, 163, 0.8) 100%);
    --gradient-dark-overlay: linear-gradient(rgba(26, 26, 26, 0.8), rgba(18, 18, 18, 0.9));
    --gradient-glow-overlay: linear-gradient(rgba(232, 62, 140, 0.05), rgba(26, 26, 26, 0.9));
    --gradient-surface: linear-gradient(135deg, var(--surface-1) 0%, var(--surface-2) 100%);
    --gradient-button: linear-gradient(to bottom, rgba(255,255,255,0.1) 0%, rgba(255,255,255,0) 50%, rgba(0,0,0,0.1) 100%);
    
    /* Typography */
    --font-weight-light: 300;
    --font-weight-regular: 400;
    --font-weight-medium: 500;
    --font-weight-semibold: 600;
    --font-weight-bold: 700;
    --font-weight-extrabold: 800;
    --letter-spacing-tightest: -1px;
    --letter-spacing-tighter: -0.5px;
    --letter-spacing-tight: -0.25px;
    --letter-spacing-normal: 0;
    --letter-spacing-wide: 0.5px;
    --letter-spacing-wider: 1px;
    --letter-spacing-widest: 1.5px;
    --line-height-none: 1;
    --line-height-tight: 1.1;
    --line-height-compact: 1.25;
    --line-height-normal: 1.5;
    --line-height-relaxed: 1.75;
    --line-height-loose: 2;
    --font-size-xs: 0.75rem;
    --font-size-sm: 0.875rem;
    --font-size-base: 1rem;
    --font-size-lg: 1.125rem;
    --font-size-xl: 1.25rem;
    --font-size-2xl: 1.5rem;
    --font-size-3xl: 1.875rem;
    --font-size-4xl: 2.25rem;
    
    /* Transitions */
    --transition-fastest: 0.1s ease-in-out;
    --transition-fast: 0.15s ease-in-out;
    --transition-normal: 0.25s ease-in-out;
    --transition-slow: 0.4s ease-in-out;
    --transition-slowest: 0.6s ease-in-out;
    --transition-bounce: 0.25s cubic-bezier(0.34, 1.56, 0.64, 1);
    --transition-smooth: 0.3s cubic-bezier(0.4, 0, 0.2, 1);
    --transition-decelerate: 0.3s cubic-bezier(0, 0, 0.2, 1);
    --transition-accelerate: 0.3s cubic-bezier(0.4, 0, 1, 1);
    
    /* Border Radius */
    --radius-sm: 0.25rem;
    --radius-md: 0.375rem;
    --radius-lg: 0.5rem;
    --radius-xl: 0.75rem;
    --radius-2xl: 1rem;
    --radius-full: 9999px;
    
    /* Z-index */
    --z-negative: -1;
    --z-base: 1;
    --z-dropdown: 10;
    --z-sticky: 20;
    --z-fixed: 30;
    --z-modal: 40;
    --z-popover: 50;
    --z-tooltip: 60;
}

/* Body theming */
body {
    background-color: var(--dark-bg);
    background-image: var(--gradient-bg);
    color: var(--text-color);
    line-height: var(--line-height-normal);
    transition: background-color var(--transition-slow);
}

/* Text colors */
.text-gray-700, .text-gray-600, .text-gray-500 {
    color: var(--text-secondary) !important;
}

/* Blue text overrides */
.text-blue-600, .text-blue-500, .text-blue-700 {
    color: var(--magenta-primary) !important;
}

/* Navigation styling - Enhanced with depth effects */
nav {
    background-color: var(--darker-bg) !important;
    background-image: linear-gradient(
        170deg,
        var(--darkest-bg) 0%,
        var(--darker-bg) 65%,
        var(--surface-1) 100%
    ) !important;
    border-bottom: 1px solid var(--border-color);
    box-shadow:
        0 3px 15px rgba(0, 0, 0, 0.4),
        0 0 2px var(--magenta-glow-faint),
        inset 0 1px 1px rgba(255, 255, 255, 0.05);
    position: relative;
    z-index: var(--z-fixed);
    backdrop-filter: blur(5px);
    -webkit-backdrop-filter: blur(5px);
}

/* Add subtle depth effect to navbar */
nav:after {
    content: '';
    position: absolute;
    bottom: -1px;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%,
        var(--magenta-glow-faint) 15%,
        var(--magenta-glow-subtle) 50%,
        var(--magenta-glow-faint) 85%,
        transparent 100%);
    opacity: 0.5;
    z-index: -1;
    animation: pulseGlow 4s infinite alternate ease-in-out;
}

@keyframes pulseGlow {
    0% { opacity: 0.3; }
    100% { opacity: 0.6; }
}

/* Add some glow to the header */
nav a.font-bold {
    color: var(--magenta-light) !important;
    text-shadow: var(--shadow-glow);
    transition: all var(--transition-bounce);
    font-weight: var(--font-weight-semibold);
    letter-spacing: var(--letter-spacing-wide);
    position: relative;
    padding: 0.25rem 0.5rem;
    border-radius: var(--radius-sm);
}

nav a.font-bold:hover {
    color: var(--magenta-lighter) !important;
    text-shadow: var(--shadow-glow-intense);
    transform: translateY(-2px) scale(1.03);
}

nav a.font-bold:after {
    content: '';
    position: absolute;
    bottom: -4px;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg, transparent, var(--magenta-primary), transparent);
    transform: scaleX(0);
    transition: transform var(--transition-bounce);
    transform-origin: center;
}

nav a.font-bold:hover:after {
    transform: scaleX(1);
}

/* Navigation links - Enhanced states */
nav a {
    color: var(--text-color) !important;
    transition: all var(--transition-normal), background-position 0.5s ease;
    letter-spacing: var(--letter-spacing-normal);
    position: relative;
    overflow: hidden;
    background-image: linear-gradient(
        to bottom,
        transparent 0%,
        transparent 90%,
        var(--magenta-glow-faint) 90%,
        var(--magenta-glow-faint) 100%
    );
    background-size: 100% 200%;
    background-position: 0 0;
    padding: 0.65rem 1rem;
    margin: 0 0.15rem;
    border-radius: var(--radius-sm);
}

nav a:hover {
    color: var(--text-color) !important;
    background-color: var(--highlight-hover) !important;
    transform: translateY(-2px);
    box-shadow:
        var(--shadow-sm),
        0 0 8px var(--magenta-glow-faint);
    background-position: 0 100%;
}

nav a:before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at center, var(--magenta-glow-faint) 0%, transparent 70%);
    opacity: 0;
    transition: opacity var(--transition-bounce);
    z-index: -1;
}

nav a:hover:before {
    opacity: 0.6;
    animation: pulseNav 1.5s infinite alternate ease-in-out;
}

@keyframes pulseNav {
    0% { opacity: 0.4; }
    100% { opacity: 0.7; }
}

/* Active nav items */
nav a.border-b-2 {
    border-color: var(--magenta-primary) !important;
    box-shadow:
        0 4px 10px -4px var(--magenta-glow-subtle),
        inset 0 -2px 0 var(--magenta-glow-subtle);
    background-color: var(--highlight-hover) !important;
}

nav a.border-b-2:after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 2px;
    background: linear-gradient(90deg,
        transparent 0%,
        var(--magenta-primary) 20%,
        var(--magenta-light) 50%,
        var(--magenta-primary) 80%,
        transparent 100%);
    animation: borderGlow 2s infinite alternate ease-in-out;
}

@keyframes borderGlow {
    0% { opacity: 0.7; box-shadow: 0 0 4px var(--magenta-glow-faint); }
    100% { opacity: 1; box-shadow: 0 0 8px var(--magenta-glow-subtle); }
}

/* User menu button - Enhanced styling */
#user-menu-button {
    background-color: var(--magenta-dark) !important;
    background-image:
        radial-gradient(
            circle at 70% 30%,
            var(--magenta-primary) 0%,
            var(--magenta-dark) 50%,
            var(--magenta-darker) 100%
        );
    transition: all var(--transition-bounce);
    box-shadow:
        var(--shadow-sm),
        inset 0 1px 1px rgba(255, 255, 255, 0.2),
        inset 0 -1px 1px rgba(0, 0, 0, 0.2);
    border: 1px solid rgba(255, 255, 255, 0.08);
    overflow: hidden;
    position: relative;
    transform-origin: center;
}

#user-menu-button:before {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.3), transparent);
    transition: left 0.6s cubic-bezier(0.34, 1.56, 0.64, 1);
    z-index: 1;
}

#user-menu-button:hover:before {
    left: 100%;
}

#user-menu-button:after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: radial-gradient(circle at center, transparent 30%, rgba(0, 0, 0, 0.2) 100%);
    opacity: 0;
    transition: opacity var(--transition-normal);
}

#user-menu-button:hover {
    transform: translateY(-2px) scale(1.05);
    box-shadow:
        var(--shadow-md),
        0 0 15px var(--magenta-glow),
        inset 0 1px 2px rgba(255, 255, 255, 0.3);
}

#user-menu-button:hover:after {
    opacity: 1;
}

#user-menu-button:focus {
    ring-color: var(--magenta-primary) !important;
    box-shadow: var(--shadow-glow-intense), 0 0 0 2px var(--magenta-glow-subtle);
}

/* User avatar - Enhanced styling */
.rounded-full.bg-blue-300,
.rounded-full.bg-blue-500,
.rounded-full.bg-blue-600,
.rounded-full.bg-blue-700 {
    background-color: var(--magenta-primary) !important;
    background-image:
        radial-gradient(
            circle at 30% 20%,
            var(--magenta-light) 0%,
            var(--magenta-primary) 60%,
            var(--magenta-dark) 100%
        ) !important;
    color: var(--text-color) !important;
    box-shadow:
        inset 0 2px 4px rgba(255, 255, 255, 0.15),
        inset 0 -2px 4px rgba(0, 0, 0, 0.25),
        0 0 8px var(--magenta-glow-faint);
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.4);
    font-weight: var(--font-weight-medium);
    transition: all var(--transition-bounce);
    border: 2px solid rgba(255, 255, 255, 0.1);
}

/* User dropdown menu - Enhanced with animations */
#user-menu {
    background-color: var(--card-bg) !important;
    background-image:
        linear-gradient(
            135deg,
            var(--card-bg) 0%,
            var(--card-bg-hover) 100%
        );
    border: 1px solid var(--border-color-light);
    box-shadow:
        var(--shadow-xl),
        0 0 20px var(--magenta-glow-faint),
        inset 0 1px 1px rgba(255, 255, 255, 0.05);
    border-radius: var(--radius-lg);
    overflow: hidden;
    transform-origin: top right;
    animation: dropdownFadeIn 0.3s var(--transition-bounce);
    backdrop-filter: blur(10px);
    -webkit-backdrop-filter: blur(10px);
}

@keyframes dropdownFadeIn {
    0% {
        opacity: 0;
        transform: translateY(-15px) scale(0.95);
        box-shadow: var(--shadow-xl), 0 0 0 var(--magenta-glow-faint);
    }
    70% {
        transform: translateY(2px) scale(1.01);
    }
    100% {
        opacity: 1;
        transform: translateY(0) scale(1);
        box-shadow: var(--shadow-xl), 0 0 20px var(--magenta-glow-faint);
    }
}

#user-menu:after {
    content: '';
    position: absolute;
    top: -5px;
    right: 10px;
    width: 10px;
    height: 10px;
    background: var(--card-bg-hover);
    border-left: 1px solid var(--border-color-light);
    border-top: 1px solid var(--border-color-light);
    transform: rotate(45deg);
    box-shadow: -2px -2px 5px rgba(0, 0, 0, 0.1);
}

#user-menu a {
    color: var(--text-color) !important;
    transition: all var(--transition-bounce);
    border-left: 3px solid transparent;
    padding: 0.75rem 1rem;
    position: relative;
    z-index: 1;
    display: flex;
    align-items: center;
    margin: 2px 0;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
}

#user-menu a:before {
    content: '';
    position: absolute;
    left: 0;
    top: 0;
    height: 100%;
    width: 0;
    background: linear-gradient(90deg, var(--magenta-glow-faint), transparent);
    z-index: -1;
    transition: width var(--transition-smooth) 0.05s;
}

#user-menu a:after {
    content: '';
    position: absolute;
    right: 10px;
    top: 50%;
    width: 5px;
    height: 5px;
    border-radius: 50%;
    background-color: var(--magenta-primary);
    opacity: 0;
    transform: translateY(-50%) scale(0);
    transition: transform var(--transition-bounce), opacity var(--transition-bounce);
}

#user-menu a:hover {
    background-color: rgba(232, 62, 140, 0.05) !important;
    border-left: 3px solid var(--magenta-primary);
    padding-left: calc(1rem - 3px);
    color: var(--magenta-lighter) !important;
    transform: translateX(5px);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.1);
}

#user-menu a:hover:before {
    width: 100%;
    animation: menuItemPulse 2s infinite alternate ease-in-out;
}

#user-menu a:hover:after {
    opacity: 1;
    transform: translateY(-50%) scale(1);
}

@keyframes menuItemPulse {
    0% { opacity: 0.4; }
    100% { opacity: 0.8; }
}

/* Mobile menu - Enhanced appearance and animations */
#mobile-menu {
    background-color: var(--darker-bg);
    background-image: linear-gradient(
        160deg,
        var(--darkest-bg) 0%,
        var(--darker-bg) 60%,
        var(--surface-1) 100%
    );
    border-top: 1px solid var(--border-color);
    box-shadow:
        inset 0 5px 15px -5px rgba(0, 0, 0, 0.3),
        0 10px 15px -5px rgba(0, 0, 0, 0.2);
    animation: slideDown 0.4s var(--transition-bounce);
    max-height: calc(100vh - 4rem);
    overflow-y: auto;
    border-radius: 0 0 var(--radius-md) var(--radius-md);
    backdrop-filter: blur(7px);
    -webkit-backdrop-filter: blur(7px);
}

@keyframes slideDown {
    0% {
        opacity: 0;
        transform: translateY(-15px);
        box-shadow: inset 0 5px 15px -5px rgba(0, 0, 0, 0.2);
    }
    70% {
        transform: translateY(3px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
        box-shadow: inset 0 5px 15px -5px rgba(0, 0, 0, 0.3);
    }
}

#mobile-menu a {
    transition: all var(--transition-bounce);
    border-left: 4px solid transparent;
    margin: 3px 0;
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    position: relative;
    overflow: hidden;
}

#mobile-menu a:before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, var(--magenta-glow-faint), transparent);
    opacity: 0;
    transition: opacity var(--transition-normal);
    z-index: -1;
}

#mobile-menu a:hover {
    background-color: var(--highlight-hover) !important;
    border-left: 4px solid var(--magenta-primary);
    transform: translateX(5px);
    box-shadow:
        0 2px 8px rgba(0, 0, 0, 0.15),
        0 0 3px var(--magenta-glow-faint);
    padding-left: calc(1.5rem - 4px);
}

#mobile-menu a:hover:before {
    opacity: 0.4;
}

#mobile-menu a.bg-highlight {
    background-color: var(--highlight-active) !important;
    border-left: 4px solid var(--magenta-light);
    box-shadow:
        inset 0 0 15px rgba(0, 0, 0, 0.3),
        0 0 5px var(--magenta-glow-faint);
    position: relative;
}

#mobile-menu a.bg-highlight:after {
    content: '';
    position: absolute;
    bottom: 0;
    left: 0;
    width: 100%;
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%,
        var(--magenta-glow-faint) 20%,
        var(--magenta-glow-subtle) 50%,
        var(--magenta-glow-faint) 80%,
        transparent 100%);
    opacity: 0.6;
}

#mobile-menu .border-t {
    border-color: var(--border-color-light) !important;
    box-shadow: 0 -1px 5px rgba(0, 0, 0, 0.2);
    position: relative;
}

#mobile-menu .border-t:before {
    content: '';
    position: absolute;
    top: -1px;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%,
        var(--magenta-glow-faint) 30%,
        var(--magenta-glow-faint) 70%,
        transparent 100%);
    opacity: 0.3;
}

/* Mobile menu button animation */
#mobile-menu-button {
    position: relative;
    overflow: hidden;
    border-radius: var(--radius-sm);
    transition: background-color var(--transition-normal);
}

#mobile-menu-button:before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: radial-gradient(circle at center, var(--magenta-glow-faint) 0%, transparent 70%);
    opacity: 0;
    transition: opacity var(--transition-normal);
    z-index: -1;
}

#mobile-menu-button:hover:before {
    opacity: 0.4;
}

#mobile-menu-button svg {
    transition: all var(--transition-bounce);
}

#mobile-menu-button:hover {
    background-color: var(--highlight-hover) !important;
}

#mobile-menu-button:hover svg {
    transform: scale(1.15) rotate(5deg);
    filter: drop-shadow(0 0 3px var(--magenta-glow-faint));
}

#mobile-menu-button:active svg {
    transform: scale(0.9) rotate(-5deg);
}

/* Login/Register buttons */
/* Login/Register buttons and navigation links */
a.text-white.hover\:bg-blue-700,
a.text-white.hover\:bg-blue-600,
a.text-white.hover\:bg-blue-500 {
    color: var(--text-color) !important;
}

a.text-white.hover\:bg-blue-700:hover,
a.text-white.hover\:bg-blue-600:hover,
a.text-white.hover\:bg-blue-500:hover {
    background-color: var(--highlight) !important;
}

a.bg-white.text-blue-600,
a.bg-white.text-blue-500,
a.bg-white.text-blue-700 {
    background-color: var(--magenta-primary) !important;
    color: var(--text-color) !important;
}

a.bg-white.text-blue-600:hover,
a.bg-white.text-blue-500:hover,
a.bg-white.text-blue-700:hover {
    background-color: var(--magenta-secondary) !important;
}

/* Navigation highlight for mobile */
.bg-highlight {
    background-color: var(--highlight) !important;
}

/* Footer styling */
footer {
    background-color: var(--darker-bg) !important;
    border-top: 1px solid var(--border-color);
}

footer .text-gray-500,
footer .text-sm {
    color: var(--text-secondary) !important;
}

footer .text-sm a {
    color: var(--magenta-primary) !important;
}

/* Flash messages */
.flash-messages {
    position: fixed;
    top: 1rem;
    right: 1rem;
    z-index: 1000;
}

.flash-message {
    margin-bottom: 0.75rem;
    padding: 0.875rem 1.25rem;
    border-radius: 0.375rem;
    box-shadow: var(--shadow-md);
    border: 1px solid var(--border-color);
    background-color: var(--card-bg);
    background-image: var(--gradient-card);
    color: var(--text-color);
    display: flex;
    justify-content: space-between;
    align-items: center;
    transform: translateX(0);
    transition: all var(--transition-normal);
    overflow: hidden;
    max-width: 400px;
    position: relative;
}

.flash-message:before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 4px;
}

.flash-message:hover {
    transform: translateX(-3px);
    box-shadow: var(--shadow-lg);
}

.flash-success {
    border-left: 4px solid var(--success);
}

.flash-success:before {
    background-color: var(--success);
}

.flash-danger {
    border-left: 4px solid var(--danger);
}

.flash-danger:before {
    background-color: var(--danger);
}

.flash-warning {
    border-left: 4px solid var(--warning);
}

.flash-warning:before {
    background-color: var(--warning);
}

.flash-info {
    border-left: 4px solid var(--magenta-primary);
}

.flash-info:before {
    background-color: var(--magenta-primary);
}

/* Button close for flash messages */
.close-flash {
    cursor: pointer;
    opacity: 0.7;
    transition: opacity var(--transition-fast);
    padding: 0.25rem;
    border-radius: 50%;
    background-color: rgba(255, 255, 255, 0.1);
    width: 24px;
    height: 24px;
    display: flex;
    align-items: center;
    justify-content: center;
}

.close-flash:hover {
    opacity: 1;
    background-color: rgba(255, 255, 255, 0.2);
}

/* Links */
a {
    color: var(--magenta-primary);
    transition: all var(--transition-normal);
    text-decoration: none;
    position: relative;
}

a:hover {
    color: var(--magenta-light);
    text-decoration: none;
}

a:not(nav a):not(.btn):hover:after {
    content: '';
    position: absolute;
    width: 100%;
    height: 1px;
    background: var(--gradient-magenta);
    bottom: -2px;
    left: 0;
    transform: scaleX(1);
    transform-origin: left;
    transition: transform var(--transition-normal);
}

/* Cards styling */
.bg-white, .bg-white.rounded-2xl, div.p-6.bg-white {
    background-color: var(--card-bg) !important;
    background-image: var(--gradient-card);
    color: var(--text-color) !important;
    border: 1px solid var(--border-color);
    transition: all var(--transition-normal);
}

.bg-white:hover, .bg-white.rounded-2xl:hover, div.p-6.bg-white:hover {
    transform: translateY(-2px);
    box-shadow: var(--shadow-md);
    border-color: var(--border-color-light);
}

/* Ensure headings use the correct color */
h1, h2, h3, h4, h5, h6 {
    color: var(--text-color) !important;
    letter-spacing: var(--letter-spacing-tight);
    line-height: var(--line-height-compact);
    font-weight: var(--font-weight-semibold);
}

h1 {
    font-weight: var(--font-weight-bold);
    letter-spacing: var(--letter-spacing-wide);
}

/* Ensure paragraphs are readable */
p {
    color: var(--text-color) !important;
    line-height: var(--line-height-relaxed);
    margin-bottom: 1rem;
}

p.lead, .text-lg {
    font-weight: var(--font-weight-light);
    letter-spacing: var(--letter-spacing-normal);
}

p.small, .text-sm {
    color: var(--text-secondary) !important;
    line-height: var(--line-height-normal);
}

/* Welcome page card styling */
.grid-cols-1 .p-6 {
    background-color: var(--card-bg) !important;
    border: 1px solid var(--border-color);
}

/* Ensure proper card shadows */
.shadow {
    box-shadow: var(--shadow-sm) !important;
    transition: box-shadow var(--transition-normal);
}

.shadow-md {
    box-shadow: var(--shadow-md) !important;
    transition: box-shadow var(--transition-normal);
}

.shadow-lg {
    box-shadow: var(--shadow-lg) !important;
    transition: box-shadow var(--transition-normal);
}

.hover\:shadow-md:hover {
    box-shadow: var(--shadow-xl) !important;
    transform: translateY(-2px);
    transition: all var(--transition-normal);
}

/* Auth pages styling */
.bg-gray-100 {
    background-color: var(--dark-bg) !important;
}

.text-gray-900 {
    color: var(--text-color) !important;
}

.text-gray-600, .text-gray-500, .text-gray-400 {
    color: var(--text-secondary) !important;
}

/* Error messages */
.text-red-500 {
    color: #EF4444 !important;
}

/* Auth form card styling */
.min-h-screen.flex.items-center.justify-center .max-w-md {
    background-color: var(--card-bg);
    border: 1px solid var(--border-color);
    border-radius: 0.5rem;
    box-shadow: var(--shadow-md);
    padding: 2rem;
}

/* Forms and inputs - Enhanced with depth and polish */

/* Form containers and general form styling */
.form-group, form > div {
    margin-bottom: 1.75rem;
    position: relative;
}

/* Form section styling */
.form-section {
    padding: 1.5rem;
    border-radius: var(--radius-lg);
    background-color: rgba(30, 30, 30, 0.3);
    border: 1px solid var(--border-color);
    box-shadow: var(--shadow-sm);
    margin-bottom: 2rem;
}

.form-section-title {
    font-size: 1.1rem;
    font-weight: var(--font-weight-semibold);
    margin-bottom: 1.25rem;
    padding-bottom: 0.5rem;
    border-bottom: 1px solid var(--border-color-light);
    color: var(--magenta-light);
}

/* Labels styling - Enhanced typography and spacing */
label {
    display: block;
    margin-bottom: 0.625rem;
    color: var(--text-color-muted);
    font-weight: var(--font-weight-medium);
    font-size: var(--font-size-sm);
    letter-spacing: var(--letter-spacing-wide);
    transition: all var(--transition-normal);
    position: relative;
    padding-left: 0.125rem;
}

label:focus-within {
    color: var(--magenta-light);
    transform: translateX(2px);
}

/* Animated label underline on focus */
label:focus-within::after {
    content: '';
    position: absolute;
    width: 2rem;
    height: 2px;
    background: var(--gradient-magenta);
    left: 0;
    bottom: -0.25rem;
    transform: scaleX(1);
    transform-origin: left;
    transition: transform var(--transition-normal);
    opacity: 0.8;
}

/* Label required indicator with pulse animation */
label.required::after {
    content: '*';
    color: var(--magenta-light);
    margin-left: 0.25rem;
    animation: pulse 2s infinite;
}

@keyframes pulse {
    0% { opacity: 0.6; }
    50% { opacity: 1; }
    100% { opacity: 0.6; }
}

/* Text inputs, textareas and selects - Enhanced with depth effects */
input[type="text"],
input[type="email"],
input[type="password"],
input[type="number"],
input[type="search"],
input[type="tel"],
input[type="url"],
input[type="date"],
input[type="datetime-local"],
textarea,
select {
    width: 100%;
    background-color: var(--surface-1) !important;
    background-image: linear-gradient(to bottom, rgba(18, 18, 18, 0.7), var(--surface-1)) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-color) !important;
    padding: 0.875rem 1.125rem !important;
    border-radius: var(--radius-md);
    font-size: 0.95rem;
    letter-spacing: var(--letter-spacing-normal);
    transition: all var(--transition-bounce);
    box-shadow: var(--shadow-inset),
                0 2px 4px rgba(0, 0, 0, 0.15),
                inset 0 1px 3px rgba(0, 0, 0, 0.2);
    outline: none;
    position: relative;
}

/* Input field hover state with subtle highlight */
input:hover:not(:disabled),
textarea:hover:not(:disabled),
select:hover:not(:disabled) {
    border-color: var(--border-color-lighter) !important;
    box-shadow: var(--shadow-inset),
                0 3px 6px rgba(0, 0, 0, 0.2),
                inset 0 1px 3px rgba(0, 0, 0, 0.1),
                0 0 0 1px var(--magenta-glow-faint);
    background-image: linear-gradient(to bottom, rgba(20, 20, 20, 0.7), var(--surface-1)) !important;
}

input::placeholder,
textarea::placeholder {
    color: var(--text-tertiary);
    opacity: 0.7;
    transition: opacity var(--transition-normal);
}

input:focus::placeholder,
textarea:focus::placeholder {
    opacity: 0.4;
    transform: translateX(3px);
}

/* Enhanced focus states for inputs */
input:focus,
textarea:focus,
select:focus {
    border-color: var(--magenta-primary) !important;
    box-shadow: var(--shadow-inset),
                0 0 0 3px var(--magenta-glow-subtle),
                0 4px 8px rgba(0, 0, 0, 0.2);
    background-image: linear-gradient(to bottom, rgba(22, 22, 22, 0.7), var(--surface-2)) !important;
    transform: translateY(-1px);
}

/* Disabled state with subtle indication */
input:disabled,
textarea:disabled,
select:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    background-color: var(--surface-2) !important;
    border-color: var(--border-color-light) !important;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.1);
    position: relative;
}

input:disabled::after,
textarea:disabled::after,
select:disabled::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: repeating-linear-gradient(
        45deg,
        rgba(255, 255, 255, 0.05),
        rgba(255, 255, 255, 0.05) 5px,
        transparent 5px,
        transparent 10px
    );
    pointer-events: none;
    border-radius: inherit;
}

/* Textarea specific styling with resizing handle */
textarea {
    min-height: 120px;
    resize: vertical;
    line-height: 1.5;
    background-image: linear-gradient(to bottom, rgba(18, 18, 18, 0.8), var(--surface-1) 50%) !important;
}

textarea:focus {
    background-image: linear-gradient(to bottom, rgba(22, 22, 22, 0.8), var(--surface-2) 50%) !important;
}

/* Resizing handle with custom styling */
textarea::-webkit-resizer {
    border-width: 8px;
    border-style: solid;
    border-color: transparent var(--magenta-glow-faint) var(--magenta-glow-faint) transparent;
    background-color: transparent;
}

/* Enhanced select styling with animated dropdown icon */
select {
    appearance: none;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23e83e8c' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: right 0.75rem center !important;
    background-size: 16px 16px !important;
    padding-right: 2.5rem !important;
    cursor: pointer;
}

select:hover {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23ff4fa3' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: right 0.75rem center !important;
}

select:focus {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23ff4fa3' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M6 9l6 6 6-6'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: right 0.75rem center !important;
    background-size: 16px 16px !important;
}

/* Improved form validation states with better visual cues */
input.is-valid,
textarea.is-valid,
select.is-valid {
    border-color: var(--success) !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2328a745' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M20 6L9 17l-5-5'/%3E%3C/svg%3E"), linear-gradient(to bottom, rgba(18, 18, 18, 0.7), var(--surface-1)) !important;
    background-repeat: no-repeat !important;
    background-position: right 0.75rem center, center !important;
    background-size: 16px 16px, 100% !important;
    padding-right: 2.5rem !important;
    box-shadow: var(--shadow-inset), 0 0 0 1px rgba(40, 167, 69, 0.2);
}

input.is-invalid,
textarea.is-invalid,
select.is-invalid {
    border-color: var(--danger) !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23dc3545' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cline x1='18' y1='6' x2='6' y2='18'%3E%3C/line%3E%3Cline x1='6' y1='6' x2='18' y2='18'%3E%3C/line%3E%3C/svg%3E"), linear-gradient(to bottom, rgba(18, 18, 18, 0.7), var(--surface-1)) !important;
    background-repeat: no-repeat !important;
    background-position: right 0.75rem center, center !important;
    background-size: 16px 16px, 100% !important;
    padding-right: 2.5rem !important;
    box-shadow: var(--shadow-inset), 0 0 0 1px rgba(220, 53, 69, 0.2);
}

/* Enhanced validation feedback messages */
.validation-feedback {
    margin-top: 0.375rem;
    font-size: var(--font-size-xs);
    line-height: 1.4;
    display: flex;
    align-items: center;
    opacity: 0;
    height: 0;
    overflow: hidden;
    transition: all var(--transition-normal);
}

.invalid-feedback {
    color: var(--danger-light);
    display: none;
}

.valid-feedback {
    color: var(--success-light);
    display: none;
}

.validation-feedback:before {
    content: '';
    display: inline-block;
    width: 0.75rem;
    height: 0.75rem;
    margin-right: 0.375rem;
    background-size: contain;
    background-repeat: no-repeat;
}

.invalid-feedback:before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%23dc3545' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Ccircle cx='12' cy='12' r='10'%3E%3C/circle%3E%3Cline x1='12' y1='8' x2='12' y2='12'%3E%3C/line%3E%3Cline x1='12' y1='16' x2='12.01' y2='16'%3E%3C/line%3E%3C/svg%3E");
}

.valid-feedback:before {
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='16' height='16' viewBox='0 0 24 24' fill='none' stroke='%2328a745' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3E%3Cpath d='M22 11.08V12a10 10 0 1 1-5.93-9.14'%3E%3C/path%3E%3Cpolyline points='22 4 12 14.01 9 11.01'%3E%3C/polyline%3E%3C/svg%3E");
}

input.is-invalid ~ .invalid-feedback,
textarea.is-invalid ~ .invalid-feedback,
select.is-invalid ~ .invalid-feedback,
input.is-valid ~ .valid-feedback,
textarea.is-valid ~ .valid-feedback,
select.is-valid ~ .valid-feedback {
    display: flex;
    opacity: 1;
    height: auto;
    animation: slideDown var(--transition-normal);
}

@keyframes slideDown {
    from {
        opacity: 0;
        transform: translateY(-8px);
        height: 0;
    }
    to {
        opacity: 1;
        transform: translateY(0);
        height: auto;
    }
}

/* Enhanced checkboxes and radio buttons */
input[type="checkbox"],
input[type="radio"] {
    appearance: none;
    -webkit-appearance: none;
    width: 1.25rem;
    height: 1.25rem;
    border: 1px solid var(--border-color);
    background-color: var(--surface-1);
    position: relative;
    cursor: pointer;
    margin-right: 0.625rem;
    vertical-align: middle;
    transition: all var(--transition-bounce);
    box-shadow: var(--shadow-inset), 0 1px 2px rgba(0, 0, 0, 0.1);
}

input[type="checkbox"] {
    border-radius: var(--radius-sm);
}

input[type="radio"] {
    border-radius: 50%;
}

input[type="checkbox"]:hover,
input[type="radio"]:hover {
    border-color: var(--magenta-glow-faint);
    box-shadow: var(--shadow-inset), 0 2px 4px rgba(0, 0, 0, 0.15), 0 0 0 1px var(--magenta-glow-faint);
}

input[type="checkbox"]:checked,
input[type="radio"]:checked {
    border-color: var(--magenta-primary);
    background-color: var(--magenta-primary);
    background-image: var(--gradient-magenta-dark);
    box-shadow: 0 0 0 1px var(--magenta-glow-faint), 0 1px 3px rgba(0, 0, 0, 0.2);
}

input[type="checkbox"]:checked::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -60%) rotate(45deg);
    width: 0.3rem;
    height: 0.6rem;
    border-bottom: 2px solid white;
    border-right: 2px solid white;
    box-shadow: 0 0 2px rgba(0, 0, 0, 0.3);
    animation: checkmarkAppear 0.2s ease-out;
}

@keyframes checkmarkAppear {
    from {
        opacity: 0;
        transform: translate(-50%, -60%) rotate(45deg) scale(0.5);
    }
    to {
        opacity: 1;
        transform: translate(-50%, -60%) rotate(45deg) scale(1);
    }
}

input[type="radio"]:checked::before {
    content: '';
    position: absolute;
    top: 50%;
    left: 50%;
    transform: translate(-50%, -50%);
    width: 0.5rem;
    height: 0.5rem;
    border-radius: 50%;
    background-color: white;
}

input[type="checkbox"]:focus,
input[type="radio"]:focus {
    border-color: var(--magenta-primary);
    box-shadow: 0 0 0 2px var(--magenta-glow-subtle);
}

input[type="checkbox"]:disabled,
input[type="radio"]:disabled {
    opacity: 0.5;
    cursor: not-allowed;
}

.checkbox-label,
.radio-label {
    display: inline-flex;
    align-items: center;
    cursor: pointer;
    margin-right: 1rem;
    margin-bottom: 0.5rem;
    transition: color var(--transition-fast);
}

.checkbox-label:hover,
.radio-label:hover {
    color: var(--text-color);
}

/* Switch toggle */
.switch {
    position: relative;
    display: inline-block;
    width: 3rem;
    height: 1.5rem;
}

.switch input {
    opacity: 0;
    width: 0;
    height: 0;
}

.slider {
    position: absolute;
    cursor: pointer;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--surface-3);
    transition: var(--transition-normal);
    border-radius: var(--radius-full);
    box-shadow: var(--shadow-inset);
}

.slider:before {
    position: absolute;
    content: '';
    height: 1rem;
    width: 1rem;
    left: 0.25rem;
    bottom: 0.25rem;
    background-color: var(--text-color);
    transition: var(--transition-normal);
    border-radius: 50%;
    box-shadow: var(--shadow-sm);
}

input:checked + .slider {
    background-color: var(--magenta-primary);
    box-shadow: 0 0 0 1px var(--magenta-glow-faint);
}

input:focus + .slider {
    box-shadow: 0 0 0 2px var(--magenta-glow-subtle);
}

input:checked + .slider:before {
    transform: translateX(1.5rem);
    background-color: white;
}

/* Button styling - Enhanced with animations */
button,
.btn,
input[type="button"],
input[type="submit"],
input[type="reset"] {
    display: inline-block;
    padding: 0.7rem 1.5rem;
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    text-align: center;
    text-decoration: none;
    white-space: nowrap;
    border-radius: var(--radius-md);
    cursor: pointer;
    transition: all var(--transition-bounce);
    border: 1px solid transparent;
    position: relative;
    overflow: hidden;
    z-index: 1;
    user-select: none;
    -webkit-user-select: none;
    letter-spacing: var(--letter-spacing-wide);
    line-height: var(--line-height-normal);
    box-shadow: var(--shadow-sm);
}

/* Button gradient effect on hover */
button::before,
.btn::before,
input[type="button"]::before,
input[type="submit"]::before,
input[type="reset"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: var(--gradient-button);
    z-index: -1;
    opacity: 0;
    transition: opacity var(--transition-normal);
}

/* Button after effect for glow */
button::after,
.btn::after,
input[type="button"]::after,
input[type="submit"]::after,
input[type="reset"]::after {
    content: '';
    position: absolute;
    top: -2px;
    left: -2px;
    right: -2px;
    bottom: -2px;
    background: var(--gradient-magenta);
    z-index: -2;
    opacity: 0;
    border-radius: var(--radius-md);
    transition: opacity var(--transition-fast);
}

button:hover::before,
.btn:hover::before,
input[type="button"]:hover::before,
input[type="submit"]:hover::before,
input[type="reset"]:hover::before {
    opacity: 1;
}

button:hover::after,
.btn:hover::after,
input[type="button"]:hover::after,
input[type="submit"]:hover::after,
input[type="reset"]:hover::after {
    opacity: 0.2;
    animation: pulse-border 1.5s infinite;
}

@keyframes pulse-border {
    0% { opacity: 0.1; }
    50% { opacity: 0.2; }
    100% { opacity: 0.1; }
}

button:focus,
.btn:focus,
input[type="button"]:focus,
input[type="submit"]:focus,
input[type="reset"]:focus {
    outline: none;
    box-shadow: 0 0 0 3px var(--magenta-glow-subtle);
}

button:active,
.btn:active,
input[type="button"]:active,
input[type="submit"]:active,
input[type="reset"]:active {
    transform: translateY(1px) scale(0.98);
}

button:disabled,
.btn:disabled,
input[type="button"]:disabled,
input[type="submit"]:disabled,
input[type="reset"]:disabled {
    opacity: 0.6;
    cursor: not-allowed;
    pointer-events: none;
    position: relative;
}

button:disabled::before,
.btn:disabled::before,
input[type="button"]:disabled::before,
input[type="submit"]:disabled::before,
input[type="reset"]:disabled::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background: repeating-linear-gradient(
        45deg,
        rgba(255, 255, 255, 0.05),
        rgba(255, 255, 255, 0.05) 10px,
        transparent 10px,
        transparent 20px
    );
    border-radius: inherit;
}

/* Primary button with enhanced hover effects */
.btn-primary,
input[type="submit"] {
    background-color: var(--magenta-primary);
    background-image: var(--gradient-magenta);
    color: white;
    box-shadow: 0 4px 6px rgba(0, 0, 0, 0.15), 0 1px 3px rgba(0, 0, 0, 0.2);
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.1);
}

.btn-primary:hover,
input[type="submit"]:hover {
    background-image: var(--gradient-magenta-dark);
    box-shadow: 0 6px 10px rgba(0, 0, 0, 0.2),
                0 3px 6px rgba(0, 0, 0, 0.15),
                0 0 0 1px var(--magenta-glow-faint);
    transform: translateY(-2px) scale(1.02);
}

/* Button hover shine effect */
.btn-primary:hover::before,
input[type="submit"]:hover::before {
    background: linear-gradient(
        to right,
        transparent 0%,
        rgba(255, 255, 255, 0.2) 50%,
        transparent 100%
    );
    animation: shine 1.5s infinite;
}

@keyframes shine {
    0% { transform: translateX(-100%); }
    60% { transform: translateX(100%); }
    100% { transform: translateX(100%); }
}

.btn-primary:active,
input[type="submit"]:active {
    background-image: none;
    background-color: var(--magenta-dark);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1), inset 0 1px 3px rgba(0, 0, 0, 0.2);
    transform: translateY(1px) scale(0.98);
}

/* Secondary button with consistent styling */
.btn-secondary,
input[type="reset"] {
    background-color: var(--surface-2);
    color: var(--text-color);
    border: 1px solid var(--border-color-light);
    box-shadow: 0 2px 4px rgba(0, 0, 0, 0.1);
}

.btn-secondary:hover,
input[type="reset"]:hover {
    background-color: var(--surface-3);
    color: var(--magenta-light);
    border-color: var(--border-color-lighter);
    transform: translateY(-2px) scale(1.01);
    box-shadow: 0 4px 8px rgba(0, 0, 0, 0.15), 0 0 0 1px var(--magenta-glow-faint);
}

.btn-secondary:active,
input[type="reset"]:active {
    background-color: var(--surface-1);
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
    transform: translateY(1px) scale(0.98);
}

/* Button group styling */
.btn-group {
    display: flex;
    gap: 0.5rem;
}

.btn-group.btn-group-vertical {
    flex-direction: column;
}

/* Small buttons */
.btn-sm {
    padding: 0.4rem 0.8rem;
    font-size: 0.8rem;
}

/* Large buttons */
.btn-lg {
    padding: 0.8rem 1.8rem;
    font-size: 1.1rem;
}

/* Enhanced file input */
input[type="file"] {
    position: relative;
    width: 100%;
    height: auto;
    min-height: 2.75rem;
    padding: 0.625rem;
    cursor: pointer;
    background-color: var(--surface-1);
    border: 1px dashed var(--border-color);
    border-radius: var(--radius-md);
    transition: all var(--transition-normal);
    display: flex;
    align-items: center;
}

input[type="file"]:hover {
    border-color: var(--border-color-lighter);
    background-color: var(--surface-2);
    box-shadow: 0 2px 6px rgba(0, 0, 0, 0.1);
}

input[type="file"]::file-selector-button {
    font-size: var(--font-size-sm);
    font-weight: var(--font-weight-medium);
    padding: 0.5rem 1rem;
    border-radius: var(--radius-sm);
    background-color: var(--surface-2);
    background-image: linear-gradient(to bottom, rgba(255, 255, 255, 0.05), transparent);
    color: var(--text-color);
    border: 1px solid var(--border-color-light);
    cursor: pointer;
    transition: all var(--transition-bounce);
    margin-right: 1rem;
    position: relative;
    overflow: hidden;
}

input[type="file"]:hover::file-selector-button {
    background-color: var(--magenta-primary);
    background-image: var(--gradient-magenta);
    border-color: var(--magenta-primary);
    color: white;
    transform: translateY(-1px);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.2);
}

input[type="file"]:focus {
    outline: none;
    box-shadow: 0 0 0 2px var(--magenta-glow-subtle);
    border-color: var(--magenta-primary);
}

/* File input - Filename display styling */
.file-input-wrapper {
    position: relative;
}

.file-name-display {
    margin-top: 0.5rem;
    font-size: 0.875rem;
    color: var(--text-color-muted);
    display: flex;
    align-items: center;
    gap: 0.5rem;
}

.file-name-display i {
    color: var(--magenta-primary);
}

/* Drag and drop zone styling */
.drop-zone {
    border: 2px dashed var(--border-color-light);
    border-radius: var(--radius-lg);
    padding: 2rem;
    text-align: center;
    transition: all var(--transition-normal);
    background-color: rgba(0, 0, 0, 0.1);
}

.drop-zone:hover,
.drop-zone.drag-over {
    border-color: var(--magenta-primary);
    background-color: rgba(232, 62, 140, 0.05);
    box-shadow: 0 0 0 1px var(--magenta-glow-faint), 0 4px 10px rgba(0, 0, 0, 0.1);
}

.drop-zone .icon {
    font-size: 2.5rem;
    color: var(--text-secondary);
    margin-bottom: 1rem;
    transition: all var(--transition-bounce);
}

.drop-zone:hover .icon,
.drop-zone.drag-over .icon {
    transform: translateY(-5px) scale(1.1);
    color: var(--magenta-primary);
}

/* Enhanced range slider */
input[type="range"] {
    -webkit-appearance: none;
    appearance: none;
    width: 100%;
    height: 0.5rem;
    background: linear-gradient(to right, var(--surface-1), var(--surface-3));
    border-radius: var(--radius-full);
    outline: none;
    margin: 0.75rem 0;
    cursor: pointer;
    position: relative;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
}

input[type="range"]::before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: var(--range-progress, 0%);
    background: linear-gradient(to right, var(--magenta-dark), var(--magenta-primary));
    border-radius: var(--radius-full);
    z-index: 1;
    transition: width 0.1s ease-in-out;
}

input[type="range"]::-webkit-slider-runnable-track {
    width: 100%;
    height: 0.5rem;
    border-radius: var(--radius-full);
}

input[type="range"]::-webkit-slider-thumb {
    -webkit-appearance: none;
    appearance: none;
    width: 1.3rem;
    height: 1.3rem;
    border-radius: 50%;
    background-color: var(--magenta-primary);
    background-image: var(--gradient-magenta);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3), 0 0 0 2px rgba(232, 62, 140, 0.2);
    cursor: pointer;
    transition: all var(--transition-bounce);
    margin-top: -0.4rem;
    z-index: 2;
    position: relative;
}

input[type="range"]::-moz-range-track {
    width: 100%;
    height: 0.5rem;
    border-radius: var(--radius-full);
}

input[type="range"]::-moz-range-progress {
    height: 0.5rem;
    background: linear-gradient(to right, var(--magenta-dark), var(--magenta-primary));
    border-radius: var(--radius-full);
}

input[type="range"]::-moz-range-thumb {
    width: 1.3rem;
    height: 1.3rem;
    border-radius: 50%;
    background-color: var(--magenta-primary);
    background-image: var(--gradient-magenta);
    box-shadow: 0 2px 5px rgba(0, 0, 0, 0.3), 0 0 0 2px rgba(232, 62, 140, 0.2);
    cursor: pointer;
    transition: all var(--transition-bounce);
    border: none;
    z-index: 2;
}

input[type="range"]::-webkit-slider-thumb:hover {
    background-color: var(--magenta-light);
    transform: scale(1.15);
    box-shadow: 0 0 10px var(--magenta-glow-subtle), 0 0 0 2px rgba(255, 105, 180, 0.3);
}

input[type="range"]::-moz-range-thumb:hover {
    background-color: var(--magenta-light);
    transform: scale(1.15);
    box-shadow: 0 0 10px var(--magenta-glow-subtle), 0 0 0 2px rgba(255, 105, 180, 0.3);
}

input[type="range"]:focus {
    box-shadow: 0 0 0 2px var(--magenta-glow-subtle);
}

/* Range value display */
.range-value {
    position: relative;
    display: flex;
    justify-content: space-between;
    margin-top: -0.5rem;
    color: var(--text-secondary);
    font-size: 0.75rem;
}

/* Form grid layout for responsive forms */
.form-grid {
    display: grid;
    grid-template-columns: repeat(12, 1fr);
    gap: 1rem;
}

.form-grid .col-12 { grid-column: span 12; }
.form-grid .col-6 { grid-column: span 6; }
.form-grid .col-4 { grid-column: span 4; }
.form-grid .col-3 { grid-column: span 3; }

@media (max-width: 768px) {
    .form-grid .col-6,
    .form-grid .col-4,
    .form-grid .col-3 {
        grid-column: span 12;
    }
}

/* Form field spacing and alignment helpers */
.form-row {
    display: flex;
    gap: 1rem;
    margin-bottom: 1.5rem;
}

@media (max-width: 640px) {
    .form-row {
        flex-direction: column;
        gap: 0.75rem;
    }
}

.form-spacer {
    height: 1.5rem;
}

.form-divider {
    width: 100%;
    height: 1px;
    background: var(--border-color);
    margin: 1.5rem 0;
    position: relative;
}

.form-divider::after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    height: 1px;
    background: linear-gradient(90deg,
        transparent 0%,
        var(--magenta-glow-faint) 50%,
        transparent 100%);
    opacity: 0.5;
}

/* Field set and legend */
fieldset {
    border: 1px solid var(--border-color-light);
    border-radius: var(--radius-md);
    padding: 1.5rem;
    margin-bottom: 1.5rem;
    background-color: rgba(0, 0, 0, 0.1);
}

legend {
    padding: 0 0.5rem;
    font-weight: var(--font-weight-medium);
    color: var(--magenta-light);
}

/* Responsive form adjustments */
@media (max-width: 768px) {
    .form-group, form > div {
        margin-bottom: 1.25rem;
    }
    
    input[type="text"],
    input[type="email"],
    input[type="password"],
    input[type="number"],
    input[type="search"],
    input[type="tel"],
    input[type="url"],
    input[type="date"],
    input[type="datetime-local"],
    textarea,
    select {
        padding: 0.625rem 0.875rem !important;
        font-size: 0.9rem;
    }
    
    button,
    .btn,
    input[type="button"],
    input[type="submit"],
    input[type="reset"] {
        width: 100%;
        margin-bottom: 0.5rem;
        padding: 0.5rem 1rem;
    }
    
    fieldset {
        padding: 1rem;
    }
    
    .checkbox-label,
    .radio-label {
        display: flex;
        margin-right: 0;
    }
}

/* Form grid for responsive layouts */
.form-grid {
    display: grid;
    grid-template-columns: repeat(auto-fit, minmax(250px, 1fr));
    gap: 1.5rem;
}

/* Helper classes for form layouts */
.form-inline {
    display: flex;
    align-items: center;
    flex-wrap: wrap;
    gap: 1rem;
}

.form-inline label {
    margin-right: 0.5rem;
    margin-bottom: 0;
}

.form-row {
    display: flex;
    flex-wrap: wrap;
    margin-right: -0.75rem;
    margin-left: -0.75rem;
}

.form-col {
    flex: 1 0 0%;
    padding-right: 0.75rem;
    padding-left: 0.75rem;
}

/* Enhance form elements with glass effect */
input[type="text"],
input[type="email"],
input[type="password"],
input[type="number"],
input[type="search"],
input[type="tel"],
input[type="url"],
input[type="date"],
input[type="datetime-local"],
textarea,
select {
    box-shadow:
        var(--shadow-inset),
        inset 0 2px 3px rgba(0, 0, 0, 0.25),
        0 1px 0 rgba(255, 255, 255, 0.05),
        0 1px 3px rgba(0, 0, 0, 0.4);
    position: relative;
    width: 100%;
    transform: translateZ(0); /* Hardware acceleration for smoother animations */
    backdrop-filter: blur(1px);
    -webkit-backdrop-filter: blur(1px);
    border-radius: var(--radius-md);
    padding: 0.75rem 1rem;
    font-size: var(--font-size-base);
}

/* Pseudo element for enhanced depth effect */
input:before,
select:before,
textarea:before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    border-radius: inherit;
    background: linear-gradient(to bottom, rgba(255, 255, 255, 0.05), transparent);
    opacity: 0;
    transition: opacity var(--transition-normal);
    pointer-events: none;
}

input:hover, select:hover, textarea:hover {
    border-color: var(--border-color-light) !important;
    background-color: var(--surface-1) !important;
    box-shadow:
        var(--shadow-inset-deep),
        0 1px 0 rgba(255, 255, 255, 0.08),
        0 0 6px var(--magenta-glow-faint);
    transform: translateY(-1px) scale(1.005);
    border-bottom: 1px solid rgba(232, 62, 140, 0.3);
}

input:hover:before, select:hover:before, textarea:hover:before {
    opacity: 1;
}

input:focus, select:focus, textarea:focus {
    border-color: var(--magenta-primary) !important;
    box-shadow:
        0 0 0 2px var(--magenta-glow),
        0 0 10px var(--magenta-glow-faint),
        var(--shadow-inset) !important;
    background-color: var(--surface-1) !important;
    outline: none;
    transform: translateY(-2px) scale(1.01);
    transition: all var(--transition-bounce);
    background-image: linear-gradient(to bottom, rgba(18, 18, 18, 0.7), var(--surface-1)) !important;
    border-top: 1px solid rgba(255, 255, 255, 0.07);
    border-bottom: 1px solid var(--magenta-primary);
}

input:focus:before, select:focus:before, textarea:focus:before {
    opacity: 0;
}

input:disabled, select:disabled, textarea:disabled {
    background-color: var(--darker-bg) !important;
    border-color: var(--border-color) !important;
    color: var(--text-disabled) !important;
    cursor: not-allowed;
    opacity: 0.75;
    box-shadow: none;
    transform: none;
}

/* Form groups with improved spacing and organization */
.form-group {
    margin-bottom: 1.5rem;
    position: relative;
}

/* Enhanced Form labels styling */
label {
    display: block;
    margin-bottom: 0.75rem;
    font-weight: var(--font-weight-medium);
    color: var(--text-color) !important;
    letter-spacing: var(--letter-spacing-wide);
    font-size: 0.95rem;
    transition: all var(--transition-bounce);
    text-shadow: 0 1px 2px rgba(0, 0, 0, 0.3);
    position: relative;
    padding-left: 0.85rem;
    background: linear-gradient(90deg,
        rgba(232, 62, 140, 0.07) 0%,
        transparent 60%);
    border-radius: var(--radius-sm);
    padding-top: 0.5rem;
    padding-bottom: 0.5rem;
    position: relative;
    overflow: hidden;
    font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
}

label:before {
    content: '';
    position: absolute;
    left: 0;
    top: 50%;
    transform: translateY(-50%);
    width: 3px;
    height: 1.25em;
    background: var(--magenta-primary);
    border-radius: 0 var(--radius-sm) var(--radius-sm) 0;
    opacity: 0.7;
    transition: all var(--transition-bounce);
    box-shadow:
        0 0 5px var(--magenta-glow-faint),
        inset 0 0 3px rgba(255, 255, 255, 0.3);
}

label:hover {
    color: var(--magenta-lighter) !important;
    transform: translateX(2px);
    background: linear-gradient(90deg,
        rgba(232, 62, 140, 0.1) 0%,
        transparent 70%);
}

label:hover:before {
    background: var(--magenta-light);
    background-image: linear-gradient(to bottom, var(--magenta-light), var(--magenta-primary));
    box-shadow:
        0 0 8px var(--magenta-glow),
        inset 0 0 3px rgba(255, 255, 255, 0.5);
    height: 1.4em;
    opacity: 1;
    width: 4px;
}

/* Add subtle effect to labels */
label:after {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(to right,
        rgba(255, 255, 255, 0.05) 0%,
        transparent 10%,
        transparent 100%);
    opacity: 0;
    transition: opacity 0.3s ease;
    pointer-events: none;
}

label:hover:after {
    opacity: 1;
}

/* Subtle label animation when input is focused */
input:focus + label,
select:focus + label,
textarea:focus + label {
    color: var(--magenta-light) !important;
    transform: translateX(4px);
    background: linear-gradient(90deg,
        rgba(232, 62, 140, 0.1) 0%,
        transparent 70%);
}

input:focus + label:before,
select:focus + label:before,
textarea:focus + label:before {
    height: 1.4em;
    width: 4px;
    background: var(--gradient-magenta);
    box-shadow: 0 0 10px var(--magenta-glow);
}

/* Required field indicator */
label.required:after {
    content: '*';
    color: var(--magenta-light);
    margin-left: 0.3rem;
    font-size: 1.2em;
    font-weight: var(--font-weight-bold);
    text-shadow: 0 0 5px var(--magenta-glow);
    animation: pulseGlow 2s infinite alternate ease-in-out;
    display: inline-block;
    transform: translateY(1px);
    position: relative;
}

@keyframes pulseGlow {
    0% { text-shadow: 0 0 5px var(--magenta-glow-faint); opacity: 0.7; }
    100% { text-shadow: 0 0 10px var(--magenta-glow); opacity: 1; }
}

/* Placeholder text enhancements */
::placeholder {
    color: var(--text-tertiary) !important;
    opacity: 0.7 !important;
    transition: all var(--transition-normal);
    font-style: italic;
    font-size: 0.95em;
}

input:focus::placeholder,
textarea:focus::placeholder {
    opacity: 0.4 !important;
    transform: translateX(8px);
    color: var(--text-disabled) !important;
    font-size: 0.9em;
}

/* Create a subtle floating placeholder effect */
.form-field {
    position: relative;
}

.form-field.has-value label,
.form-field input:focus ~ label,
.form-field textarea:focus ~ label,
.form-field select:focus ~ label {
    font-size: 0.8rem;
    transform: translateY(-150%);
    color: var(--magenta-light) !important;
    background: transparent;
}

/* Auth form inputs with consistent style */
.appearance-none {
    background-color: var(--dark-bg) !important;
    border-color: var(--border-color) !important;
    color: var(--text-color) !important;
    box-shadow:
        var(--shadow-inset),
        inset 0 1px 1px rgba(0, 0, 0, 0.2),
        0 1px 0 rgba(255, 255, 255, 0.05);
}

.appearance-none:focus {
    border-color: var(--magenta-primary) !important;
    box-shadow: 0 0 0 2px var(--magenta-glow), var(--shadow-inset) !important;
    transform: translateY(-1px);
}

.border-gray-300 {
    border-color: var(--border-color) !important;
}

.rounded-t-md, .rounded-b-md, .rounded-md {
    border-radius: 0.375rem !important;
}

/* Improve form layout spacing and structure */
.form-group {
    margin-bottom: 1.25rem;
    position: relative;
}

/* Buttons - Enhanced with depth, animations and visual appeal */
.btn, button[type="submit"], .bg-blue-600, .bg-blue-500, .bg-blue-700 {
    background-color: var(--magenta-primary) !important;
    background-image: var(--gradient-magenta) !important;
    color: var(--text-color) !important;
    transition: all var(--transition-bounce);
    border: none;
    padding: 0.75rem 1.85rem;
    border-radius: var(--radius-md);
    font-weight: var(--font-weight-medium);
    letter-spacing: var(--letter-spacing-wide);
    position: relative;
    overflow: hidden;
    box-shadow:
        var(--shadow-sm),
        inset 0 1px 2px rgba(255, 255, 255, 0.2),
        inset 0 -1px 1px rgba(0, 0, 0, 0.2),
        0 2px 4px rgba(0, 0, 0, 0.3);
    text-shadow: 0 1px 1px rgba(0, 0, 0, 0.3);
    cursor: pointer;
    transform-origin: center;
    backface-visibility: hidden; /* Prevents flicker during animations */
    z-index: 1;
    font-size: 0.975rem;
}

/* Highlight effect overlays */
.btn:before, button[type="submit"]:before, .bg-blue-600:before, .bg-blue-500:before, .bg-blue-700:before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    width: 100%;
    height: 100%;
    background: linear-gradient(to bottom,
        rgba(255,255,255,0.18) 0%,
        rgba(255,255,255,0.08) 40%,
        rgba(0,0,0,0.08) 60%,
        rgba(0,0,0,0.15) 100%);
    opacity: 0.85;
    transition: opacity var(--transition-normal), transform var(--transition-bounce);
    z-index: -1;
}

/* Button glow effect */
.btn:after, button[type="submit"]:after, .bg-blue-600:after, .bg-blue-500:after, .bg-blue-700:after {
    content: '';
    position: absolute;
    top: -3px;
    left: -3px;
    right: -3px;
    bottom: -3px;
    background: var(--magenta-glow-faint);
    border-radius: calc(var(--radius-md) + 3px);
    z-index: -2;
    opacity: 0;
    transition: opacity var(--transition-normal), transform var(--transition-bounce);
    transform: scale(0.95);
}

/* Hover state - lift, glow, and color shift */
.btn:hover, button[type="submit"]:hover, .bg-blue-600:hover, .bg-blue-500:hover, .bg-blue-700:hover {
    background-color: var(--magenta-light) !important;
    background-image: linear-gradient(135deg, var(--magenta-light) 0%, var(--magenta-primary) 100%) !important;
    box-shadow:
        var(--shadow-glow),
        var(--shadow-md),
        0 4px 8px rgba(0, 0, 0, 0.4),
        inset 0 1px 3px rgba(255, 255, 255, 0.3);
    cursor: pointer;
    transform: translateY(-3px) scale(1.04);
    letter-spacing: var(--letter-spacing-wide);
    color: white !important;
    transition: all 0.25s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

/* Active state - pressed down effect */
.btn:active, button[type="submit"]:active, .bg-blue-600:active, .bg-blue-500:active, .bg-blue-700:active {
    transform: translateY(-1px) scale(0.98);
    box-shadow:
        var(--shadow-sm),
        0 2px 4px rgba(0, 0, 0, 0.3),
        inset 0 1px 2px rgba(0, 0, 0, 0.2);
    background-image: linear-gradient(135deg, var(--magenta-primary) 0%, var(--magenta-darker) 100%) !important;
    transition: all 0.1s cubic-bezier(0.175, 0.885, 0.32, 1.275);
}

.btn:hover:before, button[type="submit"]:hover:before, .bg-blue-600:hover:before, .bg-blue-500:hover:before, .bg-blue-700:hover:before {
    opacity: 1;
    transform: translateY(-2px);
}

.btn:hover:after, button[type="submit"]:hover:after, .bg-blue-600:hover:after, .bg-blue-500:hover:after, .bg-blue-700:hover:after {
    opacity: 0.7;
    animation: buttonGlow 2s infinite alternate ease-in-out;
    transform: scale(1.03);
}

@keyframes buttonGlow {
    0% { opacity: 0.4; box-shadow: 0 0 5px var(--magenta-glow-faint); }
    25% { opacity: 0.6; box-shadow: 0 0 10px var(--magenta-glow); }
    50% { opacity: 0.8; box-shadow: 0 0 15px var(--magenta-glow); }
    75% { opacity: 0.7; box-shadow: 0 0 12px var(--magenta-glow-strong); }
    100% { opacity: 0.9; box-shadow: 0 0 20px var(--magenta-glow-strong); }
}

/* Form validation feedback styling */
.form-feedback {
    margin-top: 0.5rem;
    font-size: 0.875rem;
    border-radius: var(--radius-sm);
    padding: 0.5rem 0.75rem;
    position: relative;
    overflow: hidden;
    transition: all var(--transition-normal);
}

/* Error state styling */
.form-feedback.error,
.invalid-feedback,
.error-message {
    background-color: rgba(220, 38, 38, 0.08);
    color: rgb(248, 113, 113);
    border-left: 3px solid rgb(220, 38, 38);
}

/* Success state styling */
.form-feedback.success,
.valid-feedback,
.success-message {
    background-color: rgba(16, 185, 129, 0.08);
    color: rgb(52, 211, 153);
    border-left: 3px solid rgb(16, 185, 129);
}

/* Input validation visual states */
input.is-invalid,
select.is-invalid,
textarea.is-invalid {
    border-color: rgb(220, 38, 38) !important;
    box-shadow: 0 0 0 1px rgba(220, 38, 38, 0.25) !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%23dc2626' viewBox='0 0 16 16'%3E%3Cpath d='M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zM5.354 4.646a.5.5 0 1 0-.708.708L7.293 8l-2.647 2.646a.5.5 0 0 0 .708.708L8 8.707l2.646 2.647a.5.5 0 0 0 .708-.708L8.707 8l2.647-2.646a.5.5 0 0 0-.708-.708L8 7.293 5.354 4.646z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right calc(0.375em + 0.1875rem) center;
    background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
    padding-right: calc(1.5em + 0.75rem) !important;
}

input.is-valid,
select.is-valid,
textarea.is-valid {
    border-color: rgb(16, 185, 129) !important;
    box-shadow: 0 0 0 1px rgba(16, 185, 129, 0.25) !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' width='12' height='12' fill='%2310b981' viewBox='0 0 16 16'%3E%3Cpath d='M16 8A8 8 0 1 1 0 8a8 8 0 0 1 16 0zm-3.97-3.03a.75.75 0 0 0-1.08.022L7.477 9.417 5.384 7.323a.75.75 0 0 0-1.06 1.06L6.97 11.03a.75.75 0 0 0 1.079-.02l3.992-4.99a.75.75 0 0 0-.01-1.05z'/%3E%3C/svg%3E");
    background-repeat: no-repeat;
    background-position: right calc(0.375em + 0.1875rem) center;
    background-size: calc(0.75em + 0.375rem) calc(0.75em + 0.375rem);
    padding-right: calc(1.5em + 0.75rem) !important;
}
/* Active state - press down effect */
.btn:active, button[type="submit"]:active, .bg-blue-600:active, .bg-blue-500:active, .bg-blue-700:active {
    transform: translateY(2px) scale(0.97);
    background-image: linear-gradient(135deg, var(--magenta-dark) 0%, var(--magenta-primary) 100%) !important;
    box-shadow:
        var(--shadow-glow-subtle),
        inset 0 3px 5px rgba(0, 0, 0, 0.3),
        inset 0 1px 1px rgba(0, 0, 0, 0.2);
    transition: all 0.1s ease-out;
    border-bottom: 1px solid rgba(255, 255, 255, 0.1);
}

.btn:active:before, button[type="submit"]:active:before, .bg-blue-600:active:before, .bg-blue-500:active:before, .bg-blue-700:active:before {
    opacity: 0.5;
    transform: translateY(0);
}

/* Focus state - accessibility ring */
.btn:focus, button[type="submit"]:focus, .bg-blue-600:focus, .bg-blue-500:focus, .bg-blue-700:focus {
    outline: none;
    box-shadow:
        0 0 0 3px var(--magenta-glow),
        0 0 8px var(--magenta-glow-faint),
        var(--shadow-sm),
        inset 0 1px 1px rgba(255, 255, 255, 0.15);
}

/* Ensure focus-visible for keyboard navigation - accessibility improvement */
.btn:focus-visible, button[type="submit"]:focus-visible, .bg-blue-600:focus-visible,
.bg-blue-500:focus-visible, .bg-blue-700:focus-visible {
    outline: 2px solid white;
    outline-offset: 2px;
}

/* Button with icon spacing */
.btn svg, button[type="submit"] svg, .bg-blue-600 svg, .bg-blue-500 svg, .bg-blue-700 svg {
    margin-right: 0.5rem;
    transition: transform var(--transition-bounce);
}

.btn:hover svg, button[type="submit"]:hover svg, .bg-blue-600:hover svg, .bg-blue-500:hover svg, .bg-blue-700:hover svg {
    transform: scale(1.15);
}

/* Loading state for buttons */
.btn.loading, button[type="submit"].loading, .bg-blue-600.loading, .bg-blue-500.loading, .bg-blue-700.loading {
    position: relative;
    color: transparent !important;
    pointer-events: none;
}

.btn.loading:after, button[type="submit"].loading:after, .bg-blue-600.loading:after, .bg-blue-500.loading:after, .bg-blue-700.loading:after {
    content: '';
    position: absolute;
    top: calc(50% - 0.5em);
    left: calc(50% - 0.5em);
    width: 1em;
    height: 1em;
    border: 2px solid rgba(255, 255, 255, 0.2);
    border-radius: 50%;
    border-top-color: white;
    animation: spin 0.8s linear infinite;
    opacity: 1;
}

@keyframes spin {
    to { transform: rotate(360deg); }
}

/* Disabled state */
.btn:disabled, button[type="submit"]:disabled, .bg-blue-600:disabled, .bg-blue-500:disabled, .bg-blue-700:disabled {
    background-image: linear-gradient(135deg, var(--surface-3), var(--surface-2)) !important;
    color: var(--text-disabled) !important;
    cursor: not-allowed;
    box-shadow: none;
    transform: none;
    opacity: 0.7;
}

/* Button variations with enhanced styling */
.btn-secondary {
    background-image: linear-gradient(135deg, var(--surface-2), var(--surface-3)) !important;
    background-color: var(--surface-2) !important;
    color: var(--text-color) !important;
    border: 1px solid var(--border-color);
    box-shadow:
        var(--shadow-xs),
        inset 0 1px 0 rgba(255, 255, 255, 0.1);
}

.btn-secondary:hover {
    background-color: var(--surface-3) !important;
    background-image: linear-gradient(135deg, var(--surface-2) 30%, var(--surface-3) 100%) !important;
    box-shadow: var(--shadow-md);
    border-color: var(--border-color-light);
}

.btn-secondary:active {
    background-image: linear-gradient(135deg, var(--surface-3), var(--surface-2)) !important;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.2);
}

.btn-outline {
    background-color: transparent !important;
    background-image: none !important;
    border: 2px solid var(--magenta-primary);
    color: var(--magenta-primary) !important;
    box-shadow: none;
    text-shadow: none;
    position: relative;
    z-index: 1;
}

.btn-outline:before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    right: 0;
    bottom: 0;
    background-color: var(--magenta-primary);
    opacity: 0;
    transition: opacity var(--transition-normal);
    z-index: -1;
    border-radius: calc(var(--radius-md) - 2px);
}

.btn-outline:hover {
    color: var(--text-color) !important;
    border-color: var(--magenta-light);
    box-shadow: var(--shadow-glow-faint);
    transform: translateY(-1px);
}

.btn-outline:hover:before {
    opacity: 0.15;
}

.btn-outline:active {
    transform: translateY(1px);
    box-shadow: none;
}

.btn-small {
    padding: 0.4rem 0.8rem;
    font-size: 0.85rem;
}

.btn-large {
    padding: 0.75rem 2rem;
    font-size: 1.1rem;
}

/* Floating action button */
.btn-float {
    border-radius: var(--radius-full);
    width: 3.5rem;
    height: 3.5rem;
    display: flex;
    align-items: center;
    justify-content: center;
    padding: 0;
    box-shadow: var(--shadow-lg);
}

.btn-float:hover {
    transform: translateY(-3px) scale(1.05);
    box-shadow: var(--shadow-xl), var(--shadow-glow);
}

/* Enhanced checkbox and radio buttons */
input[type="checkbox"], input[type="radio"] {
    appearance: none;
    -webkit-appearance: none;
    width: 1.35rem;
    height: 1.35rem;
    border: 2px solid var(--border-color-light);
    background-color: var(--dark-bg);
    position: relative;
    cursor: pointer;
    margin-right: 0.625rem;
    vertical-align: middle;
    transition: all var(--transition-bounce);
    box-shadow:
        inset 0 1px 2px rgba(0, 0, 0, 0.15),
        0 1px 0 rgba(255, 255, 255, 0.05);
    background-image: linear-gradient(to bottom,
        rgba(0, 0, 0, 0.2),
        transparent 60%);
}

input[type="checkbox"] {
    border-radius: var(--radius-sm);
}

input[type="radio"] {
    border-radius: var(--radius-full);
}

input[type="checkbox"]:hover, input[type="radio"]:hover {
    border-color: var(--magenta-primary);
    background-color: var(--surface-1);
    transform: scale(1.08);
    box-shadow:
        inset 0 1px 2px rgba(0, 0, 0, 0.1),
        0 0 5px var(--magenta-glow-faint);
}

input[type="checkbox"]:active, input[type="radio"]:active {
    transform: scale(0.92);
}

input[type="checkbox"]:checked, input[type="radio"]:checked {
    background-color: var(--magenta-primary);
    border-color: var(--magenta-light);
    box-shadow:
        0 0 8px var(--magenta-glow-faint),
        inset 0 -1px 2px rgba(0, 0, 0, 0.2),
        inset 0 1px 1px rgba(255, 255, 255, 0.2);
    background-image: linear-gradient(to bottom,
        var(--magenta-light) 0%,
        var(--magenta-primary) 100%);
}

input[type="checkbox"]:checked:after {
    content: '';
    position: absolute;
    top: 0.15rem;
    left: 0.35rem;
    width: 0.4rem;
    height: 0.75rem;
    border: solid white;
    border-width: 0 2.5px 2.5px 0;
    transform: rotate(45deg);
    animation: checkmarkAppear 0.2s var(--transition-bounce);
}

@keyframes checkmarkAppear {
    0% { opacity: 0; transform: rotate(45deg) scale(0.5); }
    50% { opacity: 1; transform: rotate(45deg) scale(1.3); }
    100% { opacity: 1; transform: rotate(45deg) scale(1); }
}

input[type="radio"]:checked:after {
    content: '';
    position: absolute;
    top: calc(50% - 0.275rem);
    left: calc(50% - 0.275rem);
    width: 0.55rem;
    height: 0.55rem;
    border-radius: 50%;
    background-color: white;
    box-shadow: 0 0 3px rgba(0, 0, 0, 0.4);
    animation: radioAppear 0.3s var(--transition-bounce);
}

@keyframes radioAppear {
    0% { transform: scale(0); opacity: 0; }
    50% { transform: scale(1.4); opacity: 0.5; }
    100% { transform: scale(1); opacity: 1; }
}

input[type="checkbox"]:focus, input[type="radio"]:focus {
    outline: none;
    border-color: var(--magenta-light);
    box-shadow: 0 0 0 3px var(--magenta-glow-faint);
}

/* Make checkbox labels align properly and enhance their appearance */
input[type="checkbox"] + label,
input[type="radio"] + label {
    display: inline-block;
    padding-left: 0.25rem;
    vertical-align: middle;
    transition: all var(--transition-bounce);
    padding: 0.15rem 0.5rem;
    border-radius: var(--radius-sm);
}

input[type="checkbox"]:hover + label,
input[type="radio"]:hover + label {
    color: var(--magenta-lighter);
}

input[type="checkbox"]:checked + label,
input[type="radio"]:checked + label {
    color: var(--magenta-light);
    text-shadow: 0 0 5px var(--magenta-glow-faint);
}

/* Checkbox and radio button container for better alignment */
.checkbox-container,
.radio-container {
    display: flex;
    align-items: center;
    margin-bottom: 0.75rem;
    padding: 0.25rem;
    border-radius: var(--radius-sm);
    transition: all var(--transition-normal);
}

.checkbox-container:hover,
.radio-container:hover {
    background-color: rgba(232, 62, 140, 0.05);
}

/* Enhanced select dropdowns */
select {
    appearance: none;
    -webkit-appearance: none;
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23e83e8c' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e") !important;
    background-repeat: no-repeat !important;
    background-position: right 0.75rem center !important;
    background-size: 1em !important;
    padding-right: 2.75rem !important;
    cursor: pointer;
    background-color: var(--dark-bg) !important;
    border: 1px solid var(--border-color) !important;
    color: var(--text-color) !important;
    border-radius: var(--radius-md);
    transition: all var(--transition-bounce);
    z-index: 1;
    position: relative;
}

select:hover {
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23ff4fa3' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='6 9 12 15 18 9'%3e%3c/polyline%3e%3c/svg%3e") !important;
    border-color: var(--border-color-light) !important;
    background-color: var(--surface-1) !important;
}

select:focus {
    border-color: var(--magenta-primary) !important;
    box-shadow: 0 0 0 3px var(--magenta-glow-faint) !important;
    outline: none;
}

/* Custom select styling for enhanced appearance */
.custom-select {
    position: relative;
    display: inline-block;
    width: 100%;
}

.custom-select select {
    width: 100%;
}

.custom-select:after {
    content: '';
    position: absolute;
    top: 0;
    right: 0;
    width: 2.5rem;
    height: 100%;
    background-color: rgba(232, 62, 140, 0.1);
    pointer-events: none;
    border-radius: 0 var(--radius-md) var(--radius-md) 0;
    transition: all var(--transition-normal);
}

.custom-select:hover:after {
    background-color: rgba(232, 62, 140, 0.2);
}

/* Form validation feedback enhancements */
.is-valid, input.is-valid, select.is-valid, textarea.is-valid {
    border-color: var(--success) !important;
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%2328a745' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cpolyline points='20 6 9 17 4 12'%3e%3c/polyline%3e%3c/svg%3e") !important;
    background-repeat: no-repeat !important;
    background-position: right 0.75rem center !important;
    background-size: 1em !important;
    padding-right: 2.5rem !important;
    box-shadow:
        0 0 0 1px var(--success-light),
        inset 0 1px 1px rgba(0, 0, 0, 0.2),
        0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

.is-invalid, input.is-invalid, select.is-invalid, textarea.is-invalid {
    border-color: var(--danger) !important;
    background-image: url("data:image/svg+xml;charset=UTF-8,%3csvg xmlns='http://www.w3.org/2000/svg' viewBox='0 0 24 24' fill='none' stroke='%23dc3545' stroke-width='2' stroke-linecap='round' stroke-linejoin='round'%3e%3cline x1='18' y1='6' x2='6' y2='18'%3e%3c/line%3e%3cline x1='6' y1='6' x2='18' y2='18'%3e%3c/line%3e%3c/svg%3e") !important;
    background-repeat: no-repeat !important;
    background-position: right 0.75rem center !important;
    background-size: 1em !important;
    padding-right: 2.5rem !important;
    box-shadow:
        0 0 0 1px var(--danger-light),
        inset 0 1px 1px rgba(0, 0, 0, 0.2),
        0 1px 0 rgba(255, 255, 255, 0.05) !important;
}

/* Validation message styling */
.invalid-feedback, .text-red-500 {
    color: var(--danger-light) !important;
    font-size: 0.85rem;
    margin-top: 0.4rem;
    display: block;
    font-weight: var(--font-weight-medium);
    animation: fadeInUp 0.3s ease-out;
    background-color: rgba(220, 53, 69, 0.07);
    padding: 0.5rem 0.75rem;
    border-radius: var(--radius-sm);
    border-left: 3px solid var(--danger);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.05),
        0 1px 3px rgba(0, 0, 0, 0.1);
    position: relative;
}

.invalid-feedback:before, .text-red-500:before {
    content: '⚠️';
    margin-right: 0.5rem;
    font-size: 0.9rem;
}

.valid-feedback {
    color: var(--success-light) !important;
    font-size: 0.85rem;
    margin-top: 0.4rem;
    display: block;
    animation: fadeInUp 0.3s ease-out;
    background-color: rgba(40, 167, 69, 0.07);
    padding: 0.5rem 0.75rem;
    border-radius: var(--radius-sm);
    border-left: 3px solid var(--success);
    box-shadow:
        inset 0 1px 0 rgba(255, 255, 255, 0.05),
        0 1px 3px rgba(0, 0, 0, 0.1);
    position: relative;
}

.valid-feedback:before {
    content: '✓';
    margin-right: 0.5rem;
    font-size: 1rem;
    font-weight: bold;
}

@keyframes fadeInUp {
    0% {
        opacity: 0;
        transform: translateY(10px);
    }
    70% {
        transform: translateY(-2px);
    }
    100% {
        opacity: 1;
        transform: translateY(0);
    }
}

/* Form field with validation visual cues */
.form-field.error label {
    color: var(--danger-light) !important;
}

.form-field.error label:before {
    background: var(--danger);
}

.form-field.success label {
    color: var(--success-light) !important;
}

.form-field.success label:before {
    background: var(--success);
}

/* Submit buttons with enhanced animations */
[type="submit"] {
    background-color: var(--magenta-primary) !important;
    background-image: var(--gradient-magenta) !important;
    color: var(--text-color) !important;
    transition: all var(--transition-bounce);
    font-weight: var(--font-weight-medium);
    position: relative;
    overflow: hidden;
}

[type="submit"]:hover {
    background-color: var(--magenta-light) !important;
    background-image: linear-gradient(135deg, var(--magenta-light) 0%, var(--magenta-primary) 100%) !important;
    box-shadow:
        var(--shadow-glow),
        var(--shadow-md),
        inset 0 1px 2px rgba(255, 255, 255, 0.2);
    transform: translateY(-2px) scale(1.03);
}

[type="submit"]:active {
    transform: translateY(1px) scale(0.98);
    box-shadow: var(--shadow-glow-subtle);
    transition: all 0.1s ease-out;
}

/* Submit button shimmer effect */
[type="submit"]:after {
    content: '';
    position: absolute;
    top: -50%;
    left: -50%;
    width: 200%;
    height: 200%;
    background: linear-gradient(
        to right,
        rgba(255, 255, 255, 0) 0%,
        rgba(255, 255, 255, 0.1) 50%,
        rgba(255, 255, 255, 0) 100%
    );
    transform: rotate(30deg);
    opacity: 0;
    transition: opacity 0.3s;
}

[type="submit"]:hover:after {
    animation: shimmer 1.5s ease-in-out;
}

@keyframes shimmer {
    0% {
        opacity: 0;
        transform: rotate(30deg) translateX(-150%);
    }
    20% {
        opacity: 0.3;
    }
    100% {
        opacity: 0;
        transform: rotate(30deg) translateX(150%);
    }
}

/* Form elements responsiveness */
@media (max-width: 768px) {
    input, select, textarea {
        font-size: 1rem; /* Slightly larger on mobile for better touch targets */
        padding: 0.75rem 1.15rem; /* More padding on mobile */
    }
    
    label {
        font-size: 1rem;
        margin-bottom: 0.625rem;
    }
    
    .form-group {
        margin-bottom: 1.25rem;
    }
    
    .btn, button[type="submit"] {
        width: 100%; /* Full width buttons on mobile */
        padding: 0.85rem 1.25rem;
        font-size: 1.05rem;
        display: flex;
        justify-content: center;
        align-items: center;
    }
    
    input[type="checkbox"], input[type="radio"] {
        width: 1.5rem;
        height: 1.5rem;
    }
    
    input[type="checkbox"]:checked:after {
        top: 0.25rem;
        left: 0.45rem;
        width: 0.45rem;
        height: 0.8rem;
        border-width: 0 3px 3px 0;
    }
    
    input[type="radio"]:checked:after {
        top: calc(50% - 0.3rem);
        left: calc(50% - 0.3rem);
        width: 0.6rem;
        height: 0.6rem;
    }
    
    .invalid-feedback, .valid-feedback, .text-red-500 {
        font-size: 0.9rem;
        padding: 0.6rem 0.8rem;
    }
    
    /* Stack form fields in columns on very small screens */
    @media (max-width: 480px) {
        .flex-row {
            flex-direction: column;
        }
        
        .form-inline .form-group {
            width: 100%;
            margin-right: 0;
        }
        
        /* Add more space between stacked form elements */
        input, select, textarea {
            margin-bottom: 0.5rem;
        }
        
        .btn + .btn {
            margin-top: 0.75rem;
        }
    }
}

/* Tables */
table {
    background-color: var(--card-bg);
    background-image: var(--gradient-card);
    color: var(--text-color);
    border-collapse: separate;
    border-spacing: 0;
    width: 100%;
    margin-bottom: 1.5rem;
    border-radius: 0.5rem;
    box-shadow: var(--shadow-md);
    overflow: hidden;
    border: 1px solid var(--border-color);
}

table th, table td {
    padding: 1rem 1.25rem;
    border-bottom: 1px solid var(--border-color);
    border-right: 1px solid var(--border-color);
    transition: background-color var(--transition-fast);
    position: relative;
}

table th:last-child, table td:last-child {
    border-right: none;
}

table tr:last-child td {
    border-bottom: none;
}

table th {
    background-color: var(--surface-2);
    font-weight: var(--font-weight-semibold);
    text-align: left;
    letter-spacing: var(--letter-spacing-wide);
    text-transform: uppercase;
    font-size: 0.85em;
}

table tbody tr:hover td {
    background-color: var(--highlight-hover);
}

table tbody tr:hover {
    box-shadow: var(--shadow-sm);
}

/* Ensure all text is readable on dark backgrounds */
.text-black {
    color: var(--text-color) !important;
}

/* Additional styling for welcome page */
.text-5xl {
    text-shadow: 0 0 10px var(--magenta-glow), 0 0 30px var(--magenta-glow-subtle);
    letter-spacing: var(--letter-spacing-wider);
    font-weight: var(--font-weight-bold);
    background: var(--gradient-magenta);
    -webkit-background-clip: text;
    background-clip: text;
    color: transparent !important;
    -webkit-text-fill-color: transparent;
}
/* Additional alert styles for Bootstrap-like alerts */
.alert {
    padding: 1rem 1.5rem;
    margin-bottom: 1.25rem;
    border: 1px solid transparent;
    border-radius: 0.375rem;
    color: var(--text-color);
    background-color: var(--card-bg);
    background-image: var(--gradient-card);
    box-shadow: var(--shadow-sm);
    position: relative;
    padding-left: 1.5rem;
    overflow: hidden;
}

.alert:before {
    content: '';
    position: absolute;
    top: 0;
    left: 0;
    height: 100%;
    width: 4px;
}

.alert-success {
    background-color: rgba(40, 167, 69, 0.1);
    border-color: var(--success);
}

.alert-success:before {
    background-color: var(--success);
}

.alert-info {
    background-color: rgba(232, 62, 140, 0.1);
    border-color: var(--magenta-primary);
}

.alert-info:before {
    background-color: var(--magenta-primary);
}

.alert-warning {
    background-color: rgba(255, 193, 7, 0.1);
    border-color: var(--warning);
}

.alert-warning:before {
    background-color: var(--warning);
}

.alert-danger {
    background-color: rgba(220, 53, 69, 0.1);
    border-color: var(--danger);
}

.alert-danger:before {
    background-color: var(--danger);
}

/* Make all bg-gray-50 and bg-gray-100 elements use dark background */
.bg-gray-50, .bg-gray-100 {
    background-color: var(--dark-bg) !important;
    background-image: var(--gradient-bg);
}

/* Ensure consistent border colors */
.border-gray-200, .border-gray-300 {
    border-color: var(--border-color) !important;
}

/* Add mobile responsiveness improvements */
@media (max-width: 768px) {
    .flash-message {
        max-width: 90vw;
    }
    
    table {
        overflow-x: auto;
        display: block;
    }
    
    table th, table td {
        white-space: nowrap;
    }
}

/* Scrollbars */
::-webkit-scrollbar {
    width: 10px;
    height: 10px;
}

::-webkit-scrollbar-track {
    background: var(--darker-bg);
    border-radius: 5px;
}

::-webkit-scrollbar-thumb {
    background: var(--highlight);
    border-radius: 5px;
    transition: all var(--transition-normal);
}

::-webkit-scrollbar-thumb:hover {
    background: var(--magenta-muted);
}

/* Focus styles for accessibility */
:focus {
    outline: 2px solid var(--magenta-glow);
    outline-offset: 2px;
}

/* Selection styling */
::selection {
    background-color: var(--magenta-primary);
    color: var(--text-color);
}

/* Code blocks */
code, pre {
    font-family: 'Courier New', Courier, monospace;
    background-color: var(--surface-1);
    color: var(--text-color);
    padding: 0.2em 0.4em;
    border-radius: 3px;
    font-size: 0.9em;
    border: 1px solid var(--border-color);
}

pre {
    padding: 1rem;
    overflow-x: auto;
    line-height: 1.5;
    background-image: linear-gradient(to bottom, var(--surface-1), var(--surface-2));
}

pre code {
    background-color: transparent;
    padding: 0;
    border: none;
}


/* Progress Bar Container */
.progress-container {
    width: 100%;
    background-color: #1e1e1e;
    border-radius: 1rem;
    margin-bottom: 1rem;
    overflow: hidden;
    height: 0.75rem;
    position: relative;
    box-shadow: inset 0 1px 3px rgba(0, 0, 0, 0.3);
    border: 1px solid rgba(255, 255, 255, 0.05);
}

/* Progress Bar Indicator */
#progress-bar {
    height: 100%;
    background: linear-gradient(90deg, #e83e8c 0%, #ff4fa3 100%);
    border-radius: 1rem;
    transition: width 0.5s ease-in-out;
    position: relative;
    overflow: hidden;
    box-shadow: 0 0 8px rgba(232, 62, 140, 0.6);
}

/* Shimmer effect */
#progress-bar:after {
    content: '';
    position: absolute;
    top: 0;
    left: -100%;
    width: 100%;
    height: 100%;
    background: linear-gradient(90deg, transparent, rgba(255, 255, 255, 0.2), transparent);
    animation: shimmer 2s infinite;
}

@keyframes shimmer {
    100% {
        left: 100%;
    }
}

/* Progress label styling */
#progress-label {
    color: #d4d4d4;
    font-size: 0.875rem;
    margin-top: 0.5rem;
    font-weight: 500;
}

/* Step indicators */
.step-indicator {
    display: inline-block;
    width: 1rem;
    height: 1rem;
    border-radius: 50%;
    margin-right: 0.5rem;
    background-color: #323232;
    border: 1px solid rgba(255, 255, 255, 0.1);
    transition: all 0.3s ease;
}

/* Active step */
.step-active {
    background-color: #4285f4;
    box-shadow: 0 0 8px rgba(66, 133, 244, 0.5);
    animation: pulse 1.5s infinite alternate;
}

/* Completed step */
.step-completed {
    background-color: #28a745;
    box-shadow: 0 0 5px rgba(40, 167, 69, 0.5);
}

@keyframes pulse {
    0% {
        transform: scale(1);
        opacity: 0.8;
    }
    100% {
        transform: scale(1.1);
        opacity: 1;
    }
}

/* Step text styling */
#steps-container li {
    margin-bottom: 0.5rem;
    display: flex;
    align-items: center;
    transition: color 0.3s ease;
}

#steps-container li.active {
    color: #f2f2f2;
}

#steps-container li.completed {
    color: #b8b8b8;
}
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
            !userMenuButton.contains(event.target)) {
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
                // Add a fade-out effect (optional)
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
            const socket = io(); // Ensure io is defined (Socket.IO client loaded)
            socket.on('connect', function() {
                console.log('Socket.IO connected');
                socket.emit('join', { user_id: window.dynadash_current_user_id });
            });
            socket.on('disconnect', function() {
                console.log('Socket.IO disconnected');
            });
            socket.on('connect_error', (err) => {
                console.error('Socket.IO connection error:', err);
            });
             // Listen for progress updates (this is more generic, specific handling might be in other files)
            socket.on('progress_update', function(data) {
                console.log('Progress update:', data);
                const progressBar = document.getElementById('progress-bar'); // General progress bar
                const progressLabel = document.getElementById('progress-label'); // General progress label
                if (progressBar) progressBar.style.width = data.percent + '%';
                if (progressLabel) progressLabel.textContent = data.message;
            });
            socket.on('processing_complete', function(data) {
                console.log('Processing complete:', data);
                 const progressBar = document.getElementById('progress-bar');
                const progressLabel = document.getElementById('progress-label');
                if (progressBar) progressBar.style.width = '100%';
                if (progressLabel) progressLabel.textContent = 'Processing complete!';
                if (data && data.redirect_url) {
                    window.location.href = data.redirect_url;
                }
            });
            socket.on('processing_error', function(data) {
                console.error('Processing error from server:', data);
                alert('Error during processing: ' + data.message);
                // Hide any general processing modal if one exists
                const processingModal = document.getElementById('processing-modal');
                if(processingModal) processingModal.classList.add('hidden');
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
  // They are injected by app/templates/visual/view.html
  const dashboardTemplateHtml = window.dynadashDashboardTemplateHtml; 
  const actualDatasetJson = window.dynadashDatasetJson; // This is already a JS object/array

  function buildFullHtml(template, data) {
      if (!template) {
          console.error("Dashboard template is missing.");
          return "<html><body>Error: Dashboard template missing.</body></html>";
      }
      // Create the script tag to inject data
      // The data is already a JS object/array from the template, so stringify it
      const dataScript = `<script>window.dynadashData = ${JSON.stringify(data)};<\/script>`;
      
      // Inject data script into the head or start of body for early availability
      let finalHtml = template;
      if (template.includes("</head>")) {
          finalHtml = template.replace("</head>", dataScript + "\n</head>");
      } else if (template.includes("<body>")) {
          finalHtml = template.replace("<body>", "<body>\n" + dataScript);
      } else {
          // Fallback if no head or body, prepend (less ideal)
          finalHtml = dataScript + template;
      }
      return finalHtml;
  }

  function loadDashboard() {
      if (!dashboardFrame || !fullscreenFrame || !loadingIndicator || !dashboardError) {
          console.error("One or more dashboard elements are missing from the DOM.");
          return;
      }
      
      if (!dashboardTemplateHtml) {
          console.error("Dashboard template HTML is not available (window.dynadashDashboardTemplateHtml).");
          showDashboardError("Dashboard template is missing.");
          return;
      }
      if (typeof actualDatasetJson === 'undefined') { // Check if it's defined at all
           console.error("Actual dataset JSON is not available (window.dynadashDatasetJson).");
          // Allow dashboard to load with empty data, internal JS should handle this
          // showDashboardError("Dataset for dashboard is missing.");
          // return;
      }


      loadingIndicator.style.display = 'flex';
      dashboardError.style.display = 'none';
      dashboardFrame.style.display = 'none';
      fullscreenFrame.style.display = 'none';


      try {
          const fullHtmlContent = buildFullHtml(dashboardTemplateHtml, actualDatasetJson);

          dashboardFrame.srcdoc = fullHtmlContent;
          fullscreenFrame.srcdoc = fullHtmlContent; // Also for fullscreen

          let primaryFrameLoaded = false;

          dashboardFrame.onload = function () {
              console.log("Dashboard iframe loaded.");
              primaryFrameLoaded = true;
              loadingIndicator.style.display = 'none';
              dashboardFrame.style.display = 'block';
              // checkDashboardLoaded(dashboardFrame); // Optional check if content truly rendered
          };

          dashboardFrame.onerror = function () {
              console.error("Error loading dashboard iframe content.");
              showDashboardError("Failed to load dashboard content in iframe.");
          };
          
          // Fallback timer if onload doesn't fire or content is minimal
          setTimeout(() => {
              if (!primaryFrameLoaded && loadingIndicator.style.display !== 'none') {
                  console.warn("Dashboard iframe onload event did not fire or content is minimal after timeout. Attempting to show anyway or show error.");
                   // A simple check, might need to be more robust
                  if (dashboardFrame.contentDocument && dashboardFrame.contentDocument.body && dashboardFrame.contentDocument.body.children.length > 0) {
                      loadingIndicator.style.display = 'none';
                      dashboardFrame.style.display = 'block';
                  } else {
                      showDashboardError("Dashboard did not load correctly after timeout.");
                  }
              }
          }, 7000); // Increased timeout

      } catch (err) {
          console.error("Error setting up dashboard srcdoc:", err);
          showDashboardError(err.message);
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

  // Fullscreen controls
  const fullscreenBtn = document.getElementById('fullscreen-btn');
  const exitFullscreenBtn = document.getElementById('exit-fullscreen-btn');
  const fullscreenContainer = document.getElementById('fullscreen-container');

  if (fullscreenBtn && exitFullscreenBtn && fullscreenContainer) {
      fullscreenBtn.addEventListener('click', () => {
          fullscreenContainer.style.display = 'block';
          document.body.style.overflow = 'hidden';
          // Ensure fullscreen iframe is also loaded
          if (fullscreenFrame.srcdoc !== dashboardFrame.srcdoc) { // only if not already set
               fullscreenFrame.srcdoc = dashboardFrame.srcdoc;
          }
      });

      exitFullscreenBtn.addEventListener('click', () => {
          fullscreenContainer.style.display = 'none';
          document.body.style.overflow = 'auto';
      });

      document.addEventListener('keydown', (e) => {
          if (e.key === "Escape" && fullscreenContainer.style.display === 'block') {
              fullscreenContainer.style.display = 'none';
              document.body.style.overflow = 'auto';
          }
      });
  }
  
  // Reload/Refresh buttons
  document.getElementById('reload-dashboard-btn')?.addEventListener('click', loadDashboard); // Error specific
  document.getElementById('refresh-btn-dashboard')?.addEventListener('click', loadDashboard); // General refresh


  // Download dashboard HTML (now includes injected data script)
  const downloadBtn = document.getElementById('download-btn-dashboard');
  if (downloadBtn) {
      downloadBtn.addEventListener('click', () => {
          if (!dashboardTemplateHtml) {
              alert("No dashboard template to download.");
              return;
          }
          const fullHtmlToDownload = buildFullHtml(dashboardTemplateHtml, actualDatasetJson);
          const link = document.createElement('a');
          const blob = new Blob([fullHtmlToDownload], { type: 'text/html' });
          const url = URL.createObjectURL(blob);
          link.href = url;
          link.download = 'dynadash_dashboard.html';
          document.body.appendChild(link);
          link.click();
          document.body.removeChild(link);
          URL.revokeObjectURL(url);
      });
  }

  // Start loading the dashboard
  loadDashboard();
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
    
    <!-- Tailwind CSS -->
    <script src="https://cdn.tailwindcss.com"></script>
    
    <!-- jQuery -->
    <script src="https://code.jquery.com/jquery-3.6.0.min.js"></script>
    
    <!-- Font Awesome -->
    <link rel="stylesheet" href="https://cdnjs.cloudflare.com/ajax/libs/font-awesome/6.0.0-beta3/css/all.min.css">
    
    <!-- Socket.IO -->
    <script src="https://cdn.socket.io/4.0.0/socket.io.min.js"></script>
    
    <!-- DOMPurify -->
    <script src="https://cdnjs.cloudflare.com/ajax/libs/dompurify/2.3.0/purify.min.js"></script>
    
    <!-- Main CSS -->
    <link rel="stylesheet" href="{{ url_for('static', filename='css/main.css') }}">

    {% block head_scripts %}
    {# Moved user_id injection here to ensure it's defined before common.js runs #}
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
    <!-- Navigation -->
    <nav
       class="
         fixed top-0 left-0 w-full
         text-white      
         shadow-md z-50  
         h-16            
       "
    >
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
                    {# Check if request.endpoint is defined before using startswith #}
                    <a href="{{ url_for('visual.index') }}"
                       class="inline-flex items-center px-1 pt-1 text-sm font-medium {% if request.endpoint and request.endpoint.startswith('visual') %}border-b-2{% endif %}">
                          Visualizations
                    </a>
                    <a href="{{ url_for('data.index') if 'data.index' in current_app.view_functions else url_for('visual.index') }}"
                      class="inline-flex items-center px-1 pt-1 text-sm font-medium {% if request.endpoint and request.endpoint.startswith('data') and request.endpoint != 'data.upload' %}border-b-2{% endif %}">
                        Datasets 
                    </a>
                    <a href="{{ url_for('data.upload') if 'data.upload' in current_app.view_functions else url_for('visual.index') }}"
                        class="inline-flex items-center px-1 pt-1 text-sm font-medium {% if request.endpoint and request.endpoint == 'data.upload' %}border-b-2{% endif %}">
                         Upload   
                    </a>
                   </div>
                    {% endif %}
                </div>
                <div class="hidden sm:ml-6 sm:flex sm:items-center">
                    {% if current_user.is_authenticated %}
                    <div class="ml-3 relative">
                        <div class="flex items-center">
                            <span class="mr-2">{{ current_user.name }}</span>
                            <div class="relative">
                                <button type="button" id="user-menu-button" class="flex text-sm rounded-full focus:outline-none focus:ring-2 focus:ring-offset-2">
                                    <span class="sr-only">Open user menu</span>
                                    <div class="h-8 w-8 rounded-full flex items-center justify-center" style="background-color: var(--magenta-primary); color: var(--text-color);">
                                        {{ current_user.name[0] }}
                                    </div>
                                </button>
                            </div>
                            <div id="user-menu" class="hidden absolute right-0 top-full mt-2 w-48 bg-white rounded-md shadow-xl z-50 py-1 focus:outline-none ring-1 ring-black ring-opacity-5" role="menu" aria-orientation="vertical" aria-labelledby="user-menu-button" tabindex="-1">
                                <a href="{{ url_for('auth.profile') }}" class="block px-4 py-2 text-sm hover:bg-gray-100" role="menuitem">Your Profile</a>
                                <a href="{{ url_for('auth.change_password') }}" class="block px-4 py-2 text-sm hover:bg-gray-100" role="menuitem">Change Password</a>
                                <a href="{{ url_for('auth.logout') }}" class="block px-4 py-2 text-sm hover:bg-gray-100" role="menuitem">Sign out</a>
                            </div>
                        </div>
                    </div>
                    {% else %}
                    <div class="flex space-x-4">
                        <a href="{{ url_for('auth.login') }}" class="text-white px-3 py-2 rounded-md text-sm font-medium">Login</a>
                        <a href="{{ url_for('auth.register') }}" class="px-3 py-2 rounded-md text-sm font-medium">Register</a>
                    </div>
                    {% endif %}
                </div>
                <div class="-mr-2 flex items-center sm:hidden">
                    <button type="button" id="mobile-menu-button" class="inline-flex items-center justify-center p-2 rounded-md text-white focus:outline-none focus:ring-2 focus:ring-inset focus:ring-white">
                        <span class="sr-only">Open main menu</span>
                        <svg class="block h-6 w-6" xmlns="http://www.w3.org/2000/svg" fill="none" viewBox="0 0 24 24" stroke="currentColor" aria-hidden="true">
                            <path stroke-linecap="round" stroke-linejoin="round" stroke-width="2" d="M4 6h16M4 12h16M4 18h16" />
                        </svg>
                    </button>
                </div>
            </div>
        </div>

        <div id="mobile-menu" class="hidden sm:hidden">
            <div class="pt-2 pb-3 space-y-1">
                {% if current_user.is_authenticated %}
                <a href="{{ url_for('visual.index') }}" class="{% if request.endpoint and request.endpoint == 'visual.index' %}bg-highlight{% endif %} block pl-3 pr-4 py-2 text-base font-medium">
                    Visualizations
                </a>
                <a href="{{ url_for('data.index') if 'data.index' in current_app.view_functions else url_for('visual.index') }}" class="block pl-3 pr-4 py-2 text-base font-medium {% if request.endpoint and request.endpoint.startswith('data') and request.endpoint != 'data.upload' %}bg-highlight{% endif %}">
                    Datasets
                </a>
                <a href="{{ url_for('data.upload') if 'data.upload' in current_app.view_functions else url_for('visual.index') }}" class="block pl-3 pr-4 py-2 text-base font-medium {% if request.endpoint and request.endpoint == 'data.upload' %}bg-highlight{% endif%} ">
                    Upload
                </a>
                {% else %}
                <a href="{{ url_for('auth.login') }}" class="block pl-3 pr-4 py-2 text-base font-medium">
                    Login
                </a>
                <a href="{{ url_for('auth.register') }}" class="block pl-3 pr-4 py-2 text-base font-medium">
                    Register
                </a>
                {% endif %}
            </div>
            {% if current_user.is_authenticated %}
            <div class="pt-4 pb-3 border-t border-1">
                <div class="flex items-center px-4">
                    <div class="flex-shrink-0">
                        <div class="h-10 w-10 rounded-full flex items-center justify-center" style="background-color: var(--magenta-primary); color: var(--text-color);">
                            {{ current_user.name[0] }}
                        </div>
                    </div>
                    <div class="ml-3">
                        <div class="text-base font-medium">{{ current_user.name }}</div>
                        <div class="text-sm font-medium" style="color: var(--text-secondary);">{{ current_user.email }}</div>
                    </div>
                </div>
                <div class="mt-3 space-y-1">
                    <a href="{{ url_for('auth.profile') }}" class="block px-4 py-2 text-base font-medium">
                        Your Profile
                    </a>
                    <a href="{{ url_for('auth.change_password') }}" class="block px-4 py-2 text-base font-medium">
                        Change Password
                    </a>
                    <a href="{{ url_for('auth.logout') }}" class="block px-4 py-2 text-base font-medium">
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
                        {{ message }}
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
            <div class="flex justify-between items-center">
                <div class="text-sm">
                    © 2025 DynaDash. All rights reserved.
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
<div class="flex flex-col items-center justify-center py-16">
    <div class="text-red-500 text-6xl font-bold mb-4">{{ error_code }}</div>
    <h1 class="text-3xl font-bold text-gray-800 mb-6">{{ error_message }}</h1>
    
    <p class="text-gray-600 mb-8 text-center max-w-lg">
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
    
    <div class="flex space-x-4">
        <a href="{{ url_for('visual.index') }}" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded transition duration-300">
            Go to Home
        </a>
        <button onclick="window.history.back()" class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-2 px-4 rounded transition duration-300">
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

{% block content %}
<div class="flex flex-col items-center justify-center py-12">
    <h1 class="text-4xl font-bold text-blue-600 mb-6">Welcome to DynaDash</h1>
    <p class="text-xl text-gray-700 mb-8 text-center max-w-3xl">
        A web-based data-analytics platform that lets you upload datasets, 
        receive automated visualizations powered by Claude AI, and share insights with your team.
    </p>
    
    <div class="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-4 gap-8 w-full max-w-6xl mb-12">
        <!-- Feature 1 -->
        <div class="bg-white p-6 rounded-lg shadow-md">
            <div class="text-blue-500 text-4xl mb-4">
                <i class="fas fa-upload"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">Upload Datasets</h3>
            <p class="text-gray-600">
                Securely upload your CSV or JSON datasets and preview them instantly.
            </p>
        </div>
        
        <!-- Feature 2 -->
        <div class="bg-white p-6 rounded-lg shadow-md">
            <div class="text-blue-500 text-4xl mb-4">
                <i class="fas fa-chart-bar"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">AI-Powered Visualizations</h3>
            <p class="text-gray-600">
                Get automated exploratory analyses & visualizations generated by Claude AI.
            </p>
        </div>
        
        <!-- Feature 3 -->
        <div class="bg-white p-6 rounded-lg shadow-md">
            <div class="text-blue-500 text-4xl mb-4">
                <i class="fas fa-cubes"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">Manage Your Gallery</h3>
            <p class="text-gray-600">
                Curate, annotate & manage visualizations in your personal gallery.
            </p>
        </div>
        
        <!-- Feature 4 -->
        <div class="bg-white p-6 rounded-lg shadow-md">
            <div class="text-blue-500 text-4xl mb-4">
                <i class="fas fa-share-alt"></i>
            </div>
            <h3 class="text-xl font-semibold mb-2">Share Insights</h3>
            <p class="text-gray-600">
                Selectively share chosen datasets or charts with nominated peers.
            </p>
        </div>
    </div>
    
    {% if not current_user.is_authenticated %}
    <div class="flex flex-col md:flex-row gap-6">
        <a href="{{ url_for('auth.register') }}" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300">
            Register Now
        </a>
        <a href="{{ url_for('auth.login') }}" class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-3 px-6 rounded-lg transition duration-300">
            Login
        </a>
    </div>
    {% else %}
    <div class="flex flex-col md:flex-row gap-6">
        <a href="{{ url_for('data.upload') }}" class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-3 px-6 rounded-lg transition duration-300">
            Upload Dataset
        </a>
        <a href="{{ url_for('visual.index') }}" class="bg-gray-200 hover:bg-gray-300 text-gray-800 font-bold py-3 px-6 rounded-lg transition duration-300">
            View Visualizations
        </a>
    </div>
    {% endif %}
</div>

<!-- How It Works Section -->
<div class="bg-gray-50 py-16">
    <div class="container mx-auto px-4">
        <h2 class="text-3xl font-bold text-center mb-12">How It Works</h2>
        
        <div class="flex flex-col md:flex-row justify-between items-center mb-16">
            <div class="md:w-1/2 mb-8 md:mb-0 md:pr-8">
                <h3 class="text-2xl font-semibold mb-4">1. Upload Your Data</h3>
                <p class="text-gray-600 mb-4">
                    Upload your CSV or JSON datasets securely to the platform. 
                    Our system validates your data and provides an instant preview.
                </p>
                <ul class="list-disc list-inside text-gray-600">
                    <li>Support for CSV and JSON formats</li>
                    <li>Secure file handling</li>
                    <li>Instant data preview</li>
                </ul>
            </div>
            <div class="md:w-1/2">
                <div class="bg-white p-4 rounded-lg shadow-md">
                    <!-- Placeholder for an image or illustration -->
                    <div class="bg-gray-200 h-64 rounded flex items-center justify-center">
                        <span class="text-gray-500">Upload Interface</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="flex flex-col md:flex-row justify-between items-center mb-16">
            <div class="md:w-1/2 md:order-2 mb-8 md:mb-0 md:pl-8">
                <h3 class="text-2xl font-semibold mb-4">2. Generate Visualizations</h3>
                <p class="text-gray-600 mb-4">
                    Our AI-powered system analyzes your data and generates meaningful visualizations 
                    automatically using Anthropic's Claude API.
                </p>
                <ul class="list-disc list-inside text-gray-600">
                    <li>AI-powered data analysis</li>
                    <li>Multiple chart types</li>
                    <li>Real-time progress tracking</li>
                </ul>
            </div>
            <div class="md:w-1/2 md:order-1">
                <div class="bg-white p-4 rounded-lg shadow-md">
                    <!-- Placeholder for an image or illustration -->
                    <div class="bg-gray-200 h-64 rounded flex items-center justify-center">
                        <span class="text-gray-500">Visualization Process</span>
                    </div>
                </div>
            </div>
        </div>
        
        <div class="flex flex-col md:flex-row justify-between items-center">
            <div class="md:w-1/2 mb-8 md:mb-0 md:pr-8">
                <h3 class="text-2xl font-semibold mb-4">3. Share and Collaborate</h3>
                <p class="text-gray-600 mb-4">
                    Curate your visualizations in a personal gallery and selectively share them 
                    with team members for collaboration.
                </p>
                <ul class="list-disc list-inside text-gray-600">
                    <li>Fine-grained access control</li>
                    <li>Personal visualization gallery</li>
                    <li>Team collaboration features</li>
                </ul>
            </div>
            <div class="md:w-1/2">
                <div class="bg-white p-4 rounded-lg shadow-md">
                    <!-- Placeholder for an image or illustration -->
                    <div class="bg-gray-200 h-64 rounded flex items-center justify-center">
                        <span class="text-gray-500">Sharing Interface</span>
                    </div>
                </div>
            </div>
        </div>
    </div>
</div>
{% endblock %}

{% block scripts %}
<!-- Font Awesome for icons -->
<script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
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
            <h1 class="text-3xl font-bold text-gray-800">Generate Dashboard</h1>
            {# Ensure data.view exists or provide a fallback #}
            <a href="{{ url_for('data.view', id=dataset.id) if 'data.view' in current_app.view_functions else url_for('visual.index') }}" class="text-blue-600 hover:text-blue-800">
                <i class="fas fa-arrow-left mr-1"></i> Back to Dataset
            </a>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Dataset Info -->
            <div class="md:col-span-1">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-gray-800">Dataset Details</h2>
                    </div>
                    <div class="p-4">
                        <h3 class="font-medium text-gray-200 mb-1">{{ dataset.original_filename }}</h3>
                        <p class="text-sm text-gray-500 mb-4">
                            {{ dataset.file_type.upper() }} • {{ dataset.n_rows }} rows • {{ dataset.n_columns }} columns
                        </p>
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Uploaded:</span> {{ dataset.uploaded_at.strftime('%b %d, %Y') }}
                        </p>
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Visibility:</span> 
                            <span class="{{ 'text-green-600' if dataset.is_public else 'text-gray-800' }}">
                                {{ 'Public' if dataset.is_public else 'Private' }}
                            </span>
                        </p>
                    </div>
                </div>
            </div>
            
            <!-- Dashboard Form -->
            <div class="md:col-span-2">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-gray-800">Dashboard Options</h2>
                    </div>
                    <div class="p-4">
                        <form method="POST" action="{{ url_for('visual.generate', dataset_id=dataset.id) }}" id="dashboard-form">
                            {{ form.hidden_tag() }}
                            
                            <div class="mb-4">
                                <label for="title" class="block text-sm font-medium text-gray-700">
                                    {{ form.title.label }}
                                </label>
                                <div class="mt-1">
                                    {{ form.title(class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md") }}
                                    {% if form.title.errors %}
                                        <div class="text-red-500 text-xs mt-1">
                                            {% for error in form.title.errors %}
                                                <span>{{ error }}</span>
                                            {% endfor %}
                                        </div>
                                    {% endif %}
                                </div>
                            </div>
                            
                            <div class="mb-4">
                                <label for="description" class="block text-sm font-medium text-gray-700">
                                    {{ form.description.label }}
                                </label>
                                <div class="mt-1">
                                    {{ form.description(class="shadow-sm focus:ring-blue-500 focus:border-blue-500 block w-full sm:text-sm border-gray-300 rounded-md", rows=3, placeholder="Describe what insights you're looking for or what aspects of the data you want to highlight...") }}
                                    {% if form.description.errors %}
                                        <div class="text-red-500 text-xs mt-1">
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
                                <div class="bg-blue-50 border border-blue-200 rounded p-3">
                                    <span class="text-blue-800 text-sm">
                                        <strong>Note:</strong> Claude will analyze your dataset and automatically create a fully interactive dashboard with multiple visualizations. This process may take up to 60-90 seconds for larger datasets.
                                    </span>
                                </div>
                            </div>
                            
                            <div class="flex justify-end">
                                {{ form.submit(class="inline-flex justify-center py-2 px-4 border border-transparent shadow-sm text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700 focus:outline-none focus:ring-2 focus:ring-offset-2 focus:ring-blue-500", value="Generate Dashboard", id="submit-button") }}
                            </div>
                        </form>
                    </div>
                </div>
            </div>
        </div>
        
        <!-- Processing Modal -->
        <div id="processing-modal" class="fixed inset-0 bg-gray-900 bg-opacity-50 flex items-center justify-center hidden z-50">
            <div class="bg-card-bg rounded-lg shadow-lg p-6 max-w-md w-full border border-border-color">
                <h3 class="text-xl font-bold text-text-color mb-4">Generating Dashboard</h3>
                <div class="mb-4">
                    <div class="progress-container">
                        <div id="progress-bar" style="width: 0%"></div>
                    </div>
                    <p id="progress-label" class="text-sm text-text-secondary mt-2">Initializing...</p>
                </div>
                <div class="text-text-secondary text-sm">
                    <p class="mb-2">Claude is analyzing your data and creating a custom dashboard. This may take 60-90 seconds to complete.</p>
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
                <div id="error-message-modal" class="mt-4 p-3 bg-red-100 border border-red-300 rounded text-red-700 text-sm hidden">
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
                if (currentPercent >= step.percent) {
                    indicatorEl.classList.remove('bg-gray-300');
                    indicatorEl.classList.add('step-completed'); // Or 'step-active' if it's the current one
                    textEl.classList.remove('text-text-tertiary');
                    textEl.classList.add('text-text-color');
                } else {
                     indicatorEl.classList.remove('step-completed', 'step-active');
                     indicatorEl.classList.add('bg-gray-300');
                     textEl.classList.remove('text-text-color');
                     textEl.classList.add('text-text-tertiary');
                }
            }
        }
    }


    if (dashboardForm && processingModal && progressBar && progressLabel) {
        dashboardForm.addEventListener('submit', function(event) {
            // Client-side validation can be added here if needed before showing modal
            processingModal.classList.remove('hidden');
            progressBar.style.width = '0%';
            progressLabel.textContent = 'Initializing...';
            if(errorMessageModal) errorMessageModal.classList.add('hidden'); // Clear previous errors
            updateStepIndicator(0); // Reset step indicators

            // SocketIO event listeners are now in common.js
            // This script just needs to trigger the submission
        });
    }

    // This part will be handled by common.js now
    // const socket = io(); // Assuming common.js initializes socket if user is authenticated
    // if (typeof socket !== 'undefined') { // Check if socket was initialized
    //     socket.on('progress_update', function(data) {
    //         if (progressBar && progressLabel) {
    //             progressBar.style.width = data.percent + '%';
    //             progressLabel.textContent = data.message;
    //             updateStepIndicator(data.percent);
    //         }
    //     });

    //     socket.on('processing_complete', function(data) {
    //         if (progressBar && progressLabel) {
    //             progressBar.style.width = '100%';
    //             progressLabel.textContent = 'Dashboard completed! Redirecting...';
    //             updateStepIndicator(100);
    //         }
    //         if (data && data.redirect_url) {
    //             window.location.href = data.redirect_url;
    //         } else {
    //             // Fallback if no redirect URL is provided
    //             setTimeout(() => { processingModal.classList.add('hidden'); }, 2000);
    //         }
    //     });

    //     socket.on('processing_error', function(data) {
    //         if (processingModal && errorMessageModal && progressLabel) {
    //             progressLabel.textContent = 'Error occurred.';
    //             errorMessageModal.textContent = 'Error: ' + data.message;
    //             errorMessageModal.classList.remove('hidden');
    //             // Optionally hide modal after a delay or provide a close button
    //             // setTimeout(() => { processingModal.classList.add('hidden'); }, 5000);
    //         } else {
    //             alert('Error: ' + data.message); // Fallback
    //         }
    //     });
    // }
});
</script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/index.html

```
{% extends "shared/base.html" %}

{% block title %}My Visualizations - DynaDash{% endblock %}

{% block content %}
<script src="{{ url_for('static', filename='js/visual.js') }}"></script>
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/share.html

```
{% extends "shared/base.html" %}

{% block title %}Share Visualization - DynaDash{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-4xl mx-auto">
        <div class="flex items-center justify-between mb-6">
            <h1 class="text-3xl font-bold text-gray-800">Share Visualization</h1>
            <a href="{{ url_for('visual.view', id=visualisation.id) }}" class="text-blue-600 hover:text-blue-800">
                <i class="fas fa-arrow-left mr-1"></i> Back to Visualization
            </a>
        </div>
        
        <div class="grid grid-cols-1 md:grid-cols-3 gap-6">
            <!-- Visualization Info -->
            <div class="md:col-span-1">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-gray-800">Visualization Details</h2>
                    </div>
                    <div class="p-4">
                        <h3 class="font-medium text-gray-200 mb-1">{{ visualisation.title }}</h3>
                        {% if visualisation.description %}
                            <p class="text-sm text-gray-500 mb-4">{{ visualisation.description }}</p>
                        {% endif %}
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Created:</span> {{ visualisation.created_at.strftime('%b %d, %Y') }}
                        </p>
                        <p class="text-sm text-gray-500">
                            <span class="font-medium">Dataset:</span> {{ dataset.original_filename }}
                        </p>
                        
                        <div class="mt-4 p-2 bg-gray-50 rounded">
                            <div class="text-xs text-gray-500 mb-1">Preview:</div>
                            <div class="h-32 flex items-center justify-center bg-gray-100 rounded">
                                <span class="text-gray-400 text-sm">Visualization Preview</span>
                            </div>
                        </div>
                    </div>
                </div>
            </div>
            
            <!-- Share Form -->
            <div class="md:col-span-2">
                <div class="bg-white shadow-md rounded-lg overflow-hidden">
                    <div class="p-4 border-b border-gray-200">
                        <h2 class="text-lg font-semibold text-gray-800">Share with Users</h2>
                    </div>
                    <div class="p-4">
                        <form method="POST" action="{{ url_for('visual.share', id=visualisation.id) }}">
                            {{ form.hidden_tag() }}
                            
                            <div class="mb-6">
                                <label for="user_id" class="block text-gray-700 text-sm font-bold mb-2">
                                    {{ form.user_id.label }}
                                </label>
                                {{ form.user_id(class="shadow appearance-none border rounded w-full py-2 px-3 text-gray-700 leading-tight focus:outline-none focus:shadow-outline") }}
                                {% if form.user_id.errors %}
                                    <div class="text-red-500 text-xs mt-1">
                                        {% for error in form.user_id.errors %}
                                            <span>{{ error }}</span>
                                        {% endfor %}
                                    </div>
                                {% endif %}
                            </div>
                            
                            <div class="flex justify-end">
                                {{ form.submit(class="bg-blue-600 hover:bg-blue-700 text-white font-bold py-2 px-4 rounded focus:outline-none focus:shadow-outline transition duration-300") }}
                            </div>
                        </form>
                        
                        <div class="mt-8">
                            <h3 class="text-lg font-medium text-gray-700 mb-4">Currently Shared With</h3>
                            
                            {% if shared_with %}
                                <div class="bg-white border rounded-lg overflow-hidden">
                                    <table class="min-w-full divide-y divide-gray-200">
                                        <thead class="bg-gray-50">
                                            <tr>
                                                <th class="px-6 py-3 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    User
                                                </th>
                                                <th class="px-6 py-3 text-right text-xs font-medium text-gray-500 uppercase tracking-wider">
                                                    Actions
                                                </th>
                                            </tr>
                                        </thead>
                                        <tbody class="bg-white divide-y divide-gray-200">
                                            {% for user in shared_with %}
                                                <tr>
                                                    <td class="px-6 py-4 whitespace-nowrap">
                                                        <div class="flex items-center">
                                                            <div class="flex-shrink-0 h-10 w-10 bg-gray-200 rounded-full flex items-center justify-center">
                                                                <span class="text-gray-500">{{ user.name[0] }}</span>
                                                            </div>
                                                            <div class="ml-4">
                                                                <div class="text-sm font-medium text-gray-900">
                                                                    {{ user.name }}
                                                                </div>
                                                                <div class="text-sm text-gray-500">
                                                                    {{ user.email }}
                                                                </div>
                                                            </div>
                                                        </div>
                                                    </td>
                                                    <td class="px-6 py-4 whitespace-nowrap text-right text-sm font-medium">
                                                        <form action="{{ url_for('visual.unshare', id=visualisation.id, user_id=user.id) }}" method="POST" class="inline">
                                                            <button type="submit" class="text-red-600 hover:text-red-900">
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
                                <div class="bg-gray-50 rounded-lg p-6 text-center">
                                    <div class="text-gray-400 text-4xl mb-3">
                                        <i class="fas fa-users-slash"></i>
                                    </div>
                                    <p class="text-gray-600">
                                        This visualization is not shared with anyone yet.
                                    </p>
                                </div>
                            {% endif %}
                        </div>
                    </div>
                </div>
                
                <div class="mt-6 bg-blue-50 border border-blue-200 rounded-lg p-4">
                    <h3 class="text-lg font-semibold text-blue-800 mb-2">Sharing Information</h3>
                    <ul class="list-disc list-inside text-blue-700 space-y-1">
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
<script src="https://kit.fontawesome.com/a076d05399.js" crossorigin="anonymous"></script>
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
        .dashboard-frame { width: 100%; height: 800px; min-height: 800px; border: none; background-color: white; }
        .dashboard-frame canvas { max-width: 100%; }
        .dashboard-container { height: auto; min-height: 800px; position: relative; width: 100%; }
        .fullscreen-toggle { position: absolute; top: 10px; right: 10px; z-index: 100; padding: 5px 10px; background-color: rgba(0,0,0,0.5); color: white; border: none; border-radius: 4px; cursor: pointer; font-size: 12px; }
        .fullscreen-container { position: fixed; top: 0; left: 0; width: 100vw; height: 100vh; z-index: 9999; background-color: white; display: none; }
        .fullscreen-container .dashboard-frame { height: 100%; width: 100%; }
        .fullscreen-container .fullscreen-toggle { top: 20px; right: 20px; }
        .dashboard-error { padding: 20px; text-align: center; background-color: #fff3f3; border: 1px solid #ffcaca; border-radius: 8px; margin: 20px 0; }
        .dashboard-error h3 { color: #e74c3c; margin-bottom: 10px; }
        .dashboard-error p { margin-bottom: 15px; }
        .dashboard-loading { display: flex; flex-direction: column; align-items: center; justify-content: center; height: 400px; }
        .spinner { border: 4px solid rgba(0, 0, 0, 0.1); width: 40px; height: 40px; border-radius: 50%; border-left-color: #3498db; animation: spin 1s ease infinite; margin-bottom: 15px; }
        @keyframes spin { 0% { transform: rotate(0deg); } 100% { transform: rotate(360deg); } }
        .lg\:col-span-3 { width: 100%; }
        /* Ensure no default margin/padding in iframe body */
        /* These styles will be applied by prepare_dashboard_template_html if needed */
        /* .dashboard-frame html, .dashboard-frame body { height: 100%; width: 100%; margin: 0; padding: 0; overflow: auto; } */
    </style>
    {# Inject actual dataset JSON into a global JS variable for the dashboard renderer #}
    <script>
        window.dynadashDatasetJson = {{ actual_dataset_json|safe }};
        window.dynadashDashboardTemplateHtml = {{ dashboard_template_html|tojson|safe }};
    </script>
{% endblock %}

{% block content %}
<div class="py-8">
    <div class="max-w-7xl mx-auto px-4 sm:px-6 lg:px-8">
        <div class="flex justify-between items-center mb-6">
            <div>
                <h1 class="text-3xl font-bold text-text-color">{{ visualisation.title }}</h1>
                {% if visualisation.description %}
                    <p class="text-text-secondary mt-1">{{ visualisation.description }}</p>
                {% endif %}
            </div>
            <div class="flex space-x-3">
                <a href="{{ url_for('visual.index') }}" class="btn btn-secondary">
                    <i class="fas fa-arrow-left mr-1"></i> Back to Dashboards
                </a>
                
                {% if dataset.user_id == current_user.id %}
                    <a href="{{ url_for('visual.share', id=visualisation.id) }}" class="btn bg-green-600 hover:bg-green-700">
                        <i class="fas fa-share-alt mr-1"></i> Share
                    </a>
                    
                    <form action="{{ url_for('visual.delete', id=visualisation.id) }}" method="POST" class="inline">
                        {# CSRF token should be included if CSRFProtect is active for POSTs #}
                        <input type="hidden" name="csrf_token" value="{{ csrf_token() }}">
                        <button type="submit" class="btn bg-red-600 hover:bg-red-700" 
                                onclick="return confirm('Are you sure you want to delete this dashboard? This action cannot be undone.');">
                            <i class="fas fa-trash-alt mr-1"></i> Delete
                        </button>
                    </form>
                {% endif %}
            </div>
        </div>
        
        <div class="grid grid-cols-1 lg:grid-cols-4 gap-6">
            <div class="lg:col-span-1">
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
                            <a href="{{ url_for('visual.share', id=visualisation.id) }}" class="btn bg-green-600 hover:bg-green-700 text-white w-full text-center">
                                <i class="fas fa-share-alt mr-1"></i> Share Dashboard
                            </a>
                        {% endif %}
                        
                        <a href="{{ url_for('data.view', id=dataset.id) if 'data.view' in current_app.view_functions else '#' }}" class="btn bg-accent-blue hover:bg-accent-blue-dark text-white w-full text-center">
                            <i class="fas fa-database mr-1"></i> View Dataset
                        </a>
                        
                        <button id="fullscreen-btn" class="btn bg-accent-purple hover:bg-accent-purple-dark text-white w-full text-center">
                            <i class="fas fa-expand mr-1"></i> Fullscreen Mode
                        </button>
                        
                        <button id="download-btn-dashboard" class="btn bg-gray-500 hover:bg-gray-600 text-white w-full text-center">
                            <i class="fas fa-download mr-1"></i> Download HTML
                        </button>
                        
                        <button id="refresh-btn-dashboard" class="btn bg-accent-cyan hover:bg-accent-cyan-dark text-white w-full text-center">
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
                            <p class="text-text-secondary">There was a problem displaying the dashboard. This may be due to browser security restrictions or a temporary issue.</p>
                            <div>
                                <button id="reload-dashboard-btn" class="btn bg-accent-blue hover:bg-accent-blue-dark text-white">
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

{# The dashboard_template_html and actual_dataset_json are now passed via <script> in head_scripts block #}
{% endblock %}

{% block scripts %}
    {# Rename visual_generate.js to dashboard_renderer.js and include it here #}
    <script src="{{ url_for('static', filename='js/dashboard_renderer.js') }}" defer></script>
    {# visual.js might still be needed for general visual page interactions if any remain #}
    <script src="{{ url_for('static', filename='js/visual.js') }}" defer></script> 
{% endblock %}
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/templates/visual/welcome.html

```
{% extends "shared/base.html" %}

{% block content %}
<div class="flex flex-col items-center justify-center min-h-screen text-center px-4 space-y-8 pt-12">
    <h1 class="text-5xl font-extrabold text-blue-600">Say Hello to DynaDash!</h1>
    
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
        <div class="relative group
                    bg-white rounded-2xl 
                    transform hover:-translate-y-1
                    transition-transform duration-300 
                    ring-0 hover:ring-4 hover:ring-pink-500/50
                    ring-offset-2 ring-offset-gray-900 
                    overflow-hidden
                    filter hover:drop-shadow-[0_0_10px_rgba(236,72,153,0.6)]"
        >
            <div class="h-32 flex items-center justify-center">
                <h2 class="text-2xl font-semibold group-hover:!text-pink-600 transition-colors duration-200">
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
                <p class="text-gray-300">
                   {{ feature.desc }}
                </p>
            </div>
        </div>
    {% endfor %}
    </div>
</div>
{% endblock %}

```
