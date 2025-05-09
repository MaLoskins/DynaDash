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