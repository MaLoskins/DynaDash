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