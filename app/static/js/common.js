// app/static/js/common.js

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
            userMenuButton && !userMenuButton.contains(event.target)) {
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
        // Apply initial show animation class if needed
        flashMessages.forEach(function(message) {
            // Ensure it's visible before trying to fade it out
            // This assumes the flash-show class is added by server/another script to trigger entry
             if (!message.classList.contains('flash-show')) {
                message.classList.add('flash-show'); // Trigger entry if not already shown
             }
        });

        setTimeout(function() {
            flashMessages.forEach(function(message) {
                message.classList.remove('flash-show'); // Trigger hide animation
                // Actual display:none will be handled by CSS transition end or a JS timeout after animation
                // For simplicity, we can just hide it after the opacity transition
                setTimeout(() => { message.style.display = 'none'; }, 500); // matches 0.5s transition
            });
        }, 5000); // Time before starting fade out
    }

    // Socket.IO connection
    if (typeof window.dynadash_current_user_id !== 'undefined' && window.dynadash_current_user_id !== null) {
        try {
            // Ensure io is available
            if (typeof io === 'undefined') {
                console.error("Socket.IO library (io) is not defined. Make sure it's loaded before common.js.");
                return;
            }

            const socket = io(); 
            // If other scripts need to access this specific socket instance, you could do:
            // window.dynadashSocket = socket;

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
            
            socket.on('progress_update', function(data) {
                console.log('Progress update received by common.js:', data);
                const progressBar = document.getElementById('progress-bar'); 
                const progressLabel = document.getElementById('progress-label');
                if (progressBar) progressBar.style.width = data.percent + '%';
                if (progressLabel) progressLabel.textContent = data.message;
                
                if (typeof window.updateStepIndicator === 'function') {
                    window.updateStepIndicator(data.percent); // For generate.html
                }
            });

            socket.on('processing_complete', function(data) {
                console.log('Processing complete received by common.js:', data);
                const progressBar = document.getElementById('progress-bar');
                const progressLabel = document.getElementById('progress-label');
                const processingModal = document.getElementById('processing-modal');

                if (progressBar) progressBar.style.width = '100%';
                if (progressLabel) progressLabel.textContent = 'Processing complete! Redirecting...';
                
                if (typeof window.updateStepIndicator === 'function') {
                    window.updateStepIndicator(100); // For generate.html
                }

                if (data && data.redirect_url) {
                    // Give a moment for the user to see "complete" message before redirect
                    setTimeout(() => {
                        window.location.href = data.redirect_url;
                    }, 1000);
                } else if (processingModal) {
                    // If no redirect URL, hide the modal after a delay
                    setTimeout(() => { 
                        processingModal.classList.add('hidden'); 
                    }, 1500);
                }
            });

            socket.on('processing_error', function(data) {
                console.error('Processing error received by common.js:', data);
                const progressLabel = document.getElementById('progress-label');
                const errorMessageModalElement = document.getElementById('error-message-modal'); // Specific to generate.html modal
                const processingModal = document.getElementById('processing-modal'); // General processing modal (e.g., upload)

                if(progressLabel) progressLabel.textContent = 'Error: ' + (data.message || 'Unknown error');
                
                if(errorMessageModalElement) { // For generate.html's specific error display
                    errorMessageModalElement.textContent = 'Error: ' + (data.message || 'An unknown error occurred.');
                    errorMessageModalElement.classList.remove('hidden');
                } else if (processingModal && processingModal.querySelector('p.text-sm')) {
                    // If it's the generic upload modal, update its text
                    const modalMessageElement = processingModal.querySelector('p.text-sm');
                    if (modalMessageElement) {
                        modalMessageElement.innerHTML = `<strong class="text-danger">Error:</strong> ${data.message || 'An unknown error occurred. Please close this and try again.'}`;
                    }
                    // Optionally, add a close button or instruct user to refresh
                } else {
                    // Fallback for pages without a dedicated error display in the modal
                    alert('Error during processing: ' + (data.message || 'An unknown error occurred.'));
                }
                // Keep the modal open so the user can see the error.
            });

        } catch (e) {
            console.error("Failed to initialize Socket.IO in common.js:", e);
        }
    } else {
        console.log("Socket.IO not initialized: User not authenticated or user ID missing.");
    }
});