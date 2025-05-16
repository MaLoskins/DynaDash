// app/static/js/profile.js

document.addEventListener('DOMContentLoaded', function () {
    const deleteAccountModal = document.getElementById('delete-account-modal');
    const deleteModalContent = document.getElementById('delete-modal-content');
    const cancelDeleteButton = document.getElementById('cancel-delete-account');
    const confirmDeleteButton = document.getElementById('confirm-delete-account');
    const deleteAccountForm = document.getElementById('delete-account-form');

    // The button that opens the modal (assuming it still has onclick="confirmAndSubmit()")
    // If you change it to a button with an ID like 'open-delete-modal-btn',
    // you can use an event listener instead of the global window.confirmAndSubmit.

    function showDeleteModal() {
        if (deleteAccountModal && deleteModalContent) {
            deleteAccountModal.classList.remove('hidden'); // Show backdrop and container

            // Force a reflow, then apply animation classes
            // This ensures the 'display: block' (from removing 'hidden')
            // is processed before the transition starts.
            void deleteModalContent.offsetWidth; 

            deleteModalContent.classList.remove('opacity-0', 'scale-95');
            deleteModalContent.classList.add('opacity-100', 'scale-100');
        }
    }

    function hideDeleteModal() {
        if (deleteAccountModal && deleteModalContent) {
            // Start by making the content invisible/scaled down
            deleteModalContent.classList.add('opacity-0', 'scale-95');
            deleteModalContent.classList.remove('opacity-100', 'scale-100');

            // Wait for the transition to finish (300ms matches your HTML transition duration)
            // then hide the main modal container.
            setTimeout(() => {
                deleteAccountModal.classList.add('hidden');
            }, 300); 
        }
    }

    // This makes the function available for the inline onclick="confirmAndSubmit()"
    // in your profile.html.
    window.confirmAndSubmit = function () {
        showDeleteModal();
    };

    if (cancelDeleteButton) {
        cancelDeleteButton.addEventListener('click', function () {
            hideDeleteModal();
        });
    }

    if (confirmDeleteButton && deleteAccountForm) {
        confirmDeleteButton.addEventListener('click', function () {
            // Optionally add a loading state to the button here
            confirmDeleteButton.disabled = true;
            confirmDeleteButton.innerHTML = '<i class="fas fa-spinner fa-spin mr-2"></i> Deleting...';
            
            deleteAccountForm.submit();
            // No need to call hideDeleteModal here as the page will redirect.
        });
    }
});