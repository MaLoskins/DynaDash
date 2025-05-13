$(document).ready(function() {
  // Handle file selection
  const dropZone = $('#drop-zone');
  const fileInput = $('#file');
  const fileInfo = $('#file-info');
  const fileName = $('#file-name');
  const removeFile = $('#remove-file');
  const previewBtn = $('#preview-btn');
  const previewContainer = $('#preview-container');
  const previewContent = $('#preview-content');
  const processingModal = $('#processing-modal');
  const progressBar = $('#progress-bar');
  const progressLabel = $('#progress-label');

  fileInput.on('change', function() {
    if (fileInput[0].files.length > 0) {
      const file = fileInput[0].files[0];
      fileName.text(file.name);
      fileInfo.removeClass('hidden');
      previewBtn.removeClass('hidden');
    } else {
      fileInfo.addClass('hidden');
      previewBtn.addClass('hidden');
      previewContainer.addClass('hidden');
    }
  });

  // Handle drag & drop
  dropZone.on('dragover', function(e) {
    e.preventDefault();
    dropZone.addClass('border-blue-500');
  });

  dropZone.on('dragleave', function() {
    dropZone.removeClass('border-blue-500');
  });

  dropZone.on('drop', function(e) {
    e.preventDefault();
    dropZone.removeClass('border-blue-500');
    const files = e.originalEvent.dataTransfer.files;
    if (files.length > 0) {
      fileInput[0].files = files;
      fileName.text(files[0].name);
      fileInfo.removeClass('hidden');
      previewBtn.removeClass('hidden');
    }
  });

  // Remove selected file
  removeFile.on('click', function() {
    fileInput.val('');
    fileInfo.addClass('hidden');
    previewBtn.addClass('hidden');
    previewContainer.addClass('hidden');
  });

  // Preview selected file
  previewBtn.on('click', function() {
    if (fileInput[0].files.length > 0) {
      const file = fileInput[0].files[0];
      const reader = new FileReader();
      reader.onload = function(e) {
        let content = e.target.result;
        let html = '';

        if (file.name.endsWith('.csv')) {
          // Parse CSV
          const rows = content.split('\n');
          html = '<table class="min-w-full divide-y divide-gray-200">';
          rows.slice(0, 10).forEach((row, rowIndex) => {
            const cells = row.split(',');
            html += '<tr>';
            cells.forEach((cell, cellIndex) => {
              if (rowIndex === 0) {
                html += `<th class="px-3 py-2 bg-gray-50 text-left text-xs font-medium text-gray-500 uppercase tracking-wider">${cell}</th>`;
              } else {
                html += `<td class="px-3 py-2 whitespace-nowrap text-sm text-gray-500">${cell}</td>`;
              }
            });
            html += '</tr>';
          });
          html += '</table>';
        } else if (file.name.endsWith('.json')) {
          // Parse JSON
          try {
            const data = JSON.parse(content);
            html = '<pre class="text-sm text-gray-700">' + JSON.stringify(data, null, 2) + '</pre>';
          } catch (err) {
            html = '<div class="text-red-500">Invalid JSON file</div>';
          }
        }

        previewContent.html(html);
        previewContainer.removeClass('hidden');
      };
      reader.readAsText(file);
    }
  });

  // Handle form submission and show processing modal
  $('#upload-form').on('submit', function() {
    processingModal.removeClass('hidden');
    const socket = io();
    socket.on('progress_update', function(data) {
      progressBar.css('width', data.percent + '%');
      progressLabel.text(data.message);
    });
    socket.on('processing_complete', function() {
      progressBar.css('width', '100%');
      progressLabel.text('Processing complete!');
      // Server-side will redirect automatically
    });
    socket.on('processing_error', function(data) {
      processingModal.addClass('hidden');
      alert('Error: ' + data.message);
    });
  });
});
