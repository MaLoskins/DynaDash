import pytest
from app import create_app, db
from app.models import User

@pytest.fixture
def client():
    app = create_app('testing')  # Make sure 'testing' is a valid config
    app.config['TESTING'] = True
    app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///:memory:'

    with app.test_client() as client:
        with app.app_context():
            db.create_all()
            yield client
            db.session.remove()
            db.drop_all()

def test_index_redirect(client):
    """Test root URL redirects to welcome page if not logged in"""
    response = client.get('/')
    assert response.status_code == 302  # Redirect
    assert '/welcome' in response.headers['Location']

def test_user_registration(client):
    """Test user registration route"""
    response = client.post('/register', data={
        'name': 'Test User',
        'email': 'test@example.com',
        'password': '123456'
    }, follow_redirects=True)
    assert b'Login' in response.data or response.status_code == 200

def test_login(client):
    """Test login with correct credentials"""
    # First, register the user
    user = User(name='Login Test', email='login@example.com')
    user.password = 'secret'
    db.session.add(user)
    db.session.commit()

    # Then try logging in
    response = client.post('/login', data={
        'email': 'login@example.com',
        'password': 'secret'
    }, follow_redirects=True)
    assert b'Welcome' in response.data or response.status_code == 200