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