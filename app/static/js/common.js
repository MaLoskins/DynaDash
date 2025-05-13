// Wrap in DOMContentLoaded to ensure elements are available
document.addEventListener('DOMContentLoaded', function() {
    // Toggle user menu
    document.getElementById('user-menu-button')?.addEventListener('click', function() {
        document.getElementById('user-menu').classList.toggle('hidden');
    });

    // Close user menu when clicking outside
    document.addEventListener('click', function(event) {
        const userMenu = document.getElementById('user-menu');
        const userMenuButton = document.getElementById('user-menu-button');
        if (userMenu && !userMenu.classList.contains('hidden') &&
            !userMenu.contains(event.target) &&
            !userMenuButton.contains(event.target)) {
            userMenu.classList.add('hidden');
        }
    });

    // Toggle mobile menu
    document.getElementById('mobile-menu-button')?.addEventListener('click', function() {
        document.getElementById('mobile-menu').classList.toggle('hidden');
    });

    // Close flash messages on click
    document.querySelectorAll('.close-flash').forEach(function(button) {
        button.addEventListener('click', function() {
            this.parentElement.style.display = 'none';
        });
    });

    // Auto-close flash messages after 5 seconds
    setTimeout(function() {
        document.querySelectorAll('.flash-message').forEach(function(message) {
            message.style.display = 'none';
        });
    }, 5000);

    // Socket.IO connection (only when authenticated)
    {% raw %}{% if current_user.is_authenticated %}{% endraw %}
    const socket = io();
    socket.on('connect', function() {
        console.log('Socket.IO connected');
        socket.emit('join', { user_id: {{ current_user.id }} });
    });
    socket.on('disconnect', function() {
        console.log('Socket.IO disconnected');
    });
    {% raw %}{% endif %}{% endraw %}
});