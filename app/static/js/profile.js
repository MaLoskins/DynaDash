// This file contains JavaScript code for the profile page.
// It handles the confirmation modal for deleting an account.

document.addEventListener('DOMContentLoaded', function() {
  // show the modal instead of browser confirm()
  window.confirmAndSubmit = function() {
    document.getElementById('delete-account-modal')
            .classList.remove('hidden');
  };

  // cancel hides the modal
  document.getElementById('cancel-delete-account')
          .addEventListener('click', function() {
    document.getElementById('delete-account-modal')
            .classList.add('hidden');
  });

  // confirm submits the hidden form
  document.getElementById('confirm-delete-account')
          .addEventListener('click', function() {
    document.getElementById('delete-account-form')
            .submit();
  });
});
