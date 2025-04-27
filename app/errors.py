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