import os
from app import create_app, socketio
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Create the Flask application instance
app = create_app(os.getenv('FLASK_ENV', 'development'))

if __name__ == '__main__':
    # Run the application with Socket.IO support
    socketio.run(
        app,
        host=os.getenv('HOST', '0.0.0.0'),
        port=int(os.getenv('PORT', 5000)),
        debug=app.config['DEBUG']
    )