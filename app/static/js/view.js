$(document).ready(function() {
    // Delete confirmation modal
    const deleteModal = $('#delete-modal');

    $('#delete-btn').on('click', function() {
        deleteModal.removeClass('hidden');
    });

    $('#cancel-delete').on('click', function() {
        deleteModal.addClass('hidden');
    });

    // Close modal when clicking outside the modal element
    $(window).on('click', function(event) {
        if (event.target === deleteModal[0]) {
            deleteModal.addClass('hidden');
        }
    });

    // Download dataset
    $('#download-btn').on('click', function() {
        const downloadUrl = $(this).data('download-url');
        window.location.href = downloadUrl;
    });
});