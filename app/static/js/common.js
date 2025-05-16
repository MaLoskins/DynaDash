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