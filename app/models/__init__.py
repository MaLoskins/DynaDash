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