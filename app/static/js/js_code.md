# CODEBASE

## Directory Tree:

### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js

```
/mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js
├── .gitkeep
├── common.js
├── dashboard_renderer.js
├── profile.js
├── upload.js
├── view.js
└── visual.js
```

## Code Files


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/.gitkeep

```
# This file is intentionally left empty to ensure the js directory is included in the Git repository.
# The js directory is used to store JavaScript files for the application.
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/common.js

```
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
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/dashboard_renderer.js

```
document.addEventListener("DOMContentLoaded", function () {
    console.log("✅ dashboard_renderer.js loaded");

    const dashboardFrame = document.getElementById('dashboard-frame');
    const fullscreenFrame = document.getElementById('fullscreen-frame');
    const loadingIndicator = document.getElementById('dashboard-loading');
    const dashboardError = document.getElementById('dashboard-error');

    // Data and template are now expected to be on the window object
    // They are injected by app/templates/visual/view.html's head_scripts block
    const dashboardTemplateHtml = window.dynadashDashboardTemplateHtml; 
    const actualDatasetData = window.dynadashDatasetJson; 

    function buildFullHtml(template, data) {
        if (typeof template !== 'string' || !template) {
            console.error("Dashboard template is missing or not a string.");
            return "<html><body>Error: Dashboard template missing.</body></html>";
        }
        // Ensure data is an array, default to empty if undefined/null
        const dataToInject = (typeof data !== 'undefined' && data !== null) ? data : [];
        const dataScript = `<script>window.dynadashData = ${JSON.stringify(dataToInject)};<\/script>`;
        
        let finalHtml = template;
        const headEndTag = '</head>';
        const bodyStartTag = '<body>';
        const headEndIndex = template.toLowerCase().lastIndexOf(headEndTag); // Use lastIndexOf for head
        const bodyStartIndex = template.toLowerCase().indexOf(bodyStartTag);

        if (headEndIndex !== -1) {
            finalHtml = template.slice(0, headEndIndex) + dataScript + "\n" + template.slice(headEndIndex);
        } else if (bodyStartIndex !== -1) {
            finalHtml = template.slice(0, bodyStartIndex + bodyStartTag.length) + "\n" + dataScript + template.slice(bodyStartIndex + bodyStartTag.length);
        } else {
            finalHtml = dataScript + template; 
        }
        return finalHtml;
    }

    function loadDashboard() {
        if (!dashboardFrame || !loadingIndicator || !dashboardError) { // fullscreenFrame is optional for this function
            console.error("One or more essential dashboard display elements are missing from the DOM.");
            if (loadingIndicator) loadingIndicator.style.display = 'none';
            if (dashboardError) {
                 dashboardError.style.display = 'block';
                 dashboardError.querySelector('p').textContent = "Essential dashboard elements missing from page.";
            }
            return;
        }
        
        if (typeof dashboardTemplateHtml === 'undefined' || dashboardTemplateHtml === null || dashboardTemplateHtml.trim() === "") {
            console.error("Dashboard template HTML is not available (window.dynadashDashboardTemplateHtml is empty or undefined).");
            showDashboardError("Dashboard template is missing or could not be loaded.");
            return;
        }

        loadingIndicator.style.display = 'flex';
        dashboardError.style.display = 'none';
        dashboardFrame.style.display = 'none';
        if(fullscreenFrame) fullscreenFrame.setAttribute('srcdoc', '');


        try {
            const fullHtmlContent = buildFullHtml(dashboardTemplateHtml, actualDatasetData);
            
            // Function to handle iframe load/error
            const handleIframeLoad = (frameElement, isPrimary) => {
                console.log(`Iframe ${frameElement.id} loaded.`);
                if(isPrimary) {
                    loadingIndicator.style.display = 'none';
                    dashboardFrame.style.display = 'block';
                }
            };

            const handleIframeError = (frameElement, isPrimary, errorMsg) => {
                console.error(`Error loading ${frameElement.id} iframe content:`, errorMsg);
                if(isPrimary) {
                    showDashboardError(`Failed to load dashboard content in iframe (${frameElement.id}).`);
                }
            };
            
            dashboardFrame.onload = () => handleIframeLoad(dashboardFrame, true);
            dashboardFrame.onerror = (e) => handleIframeError(dashboardFrame, true, e.type);
            dashboardFrame.setAttribute('srcdoc', fullHtmlContent);

            if (fullscreenFrame) { 
                fullscreenFrame.onload = () => handleIframeLoad(fullscreenFrame, false);
                fullscreenFrame.onerror = (e) => handleIframeError(fullscreenFrame, false, e.type);
                fullscreenFrame.setAttribute('srcdoc', fullHtmlContent);
            }

            // Fallback timer
            setTimeout(() => {
                const isDashboardFrameVisible = dashboardFrame.style.display === 'block';
                if (!isDashboardFrameVisible && loadingIndicator.style.display !== 'none') {
                    console.warn("Dashboard iframe onload event might not have fired as expected after timeout.");
                    let frameDoc = dashboardFrame.contentDocument || dashboardFrame.contentWindow?.document;
                    if (frameDoc && frameDoc.body && frameDoc.body.children.length > 0 && frameDoc.readyState === 'complete') {
                        loadingIndicator.style.display = 'none';
                        dashboardFrame.style.display = 'block';
                    } else {
                        showDashboardError("Dashboard did not load correctly or is empty after timeout.");
                    }
                }
            }, 8000);

        } catch (err) {
            console.error("Error setting up dashboard srcdoc:", err);
            showDashboardError("A JavaScript error occurred while preparing the dashboard: " + err.message);
        }
    }

    function showDashboardError(message = "An unknown error occurred while loading the dashboard.") {
        if (loadingIndicator) loadingIndicator.style.display = 'none';
        if (dashboardError) {
            dashboardError.style.display = 'block';
            const p = dashboardError.querySelector('p');
            if(p) p.textContent = message;
        }
        if (dashboardFrame) dashboardFrame.style.display = 'none';
    }

    const fullscreenBtn = document.getElementById('fullscreen-btn');
    const exitFullscreenBtn = document.getElementById('exit-fullscreen-btn');
    const fullscreenContainer = document.getElementById('fullscreen-container');

    if (fullscreenBtn && exitFullscreenBtn && fullscreenContainer && fullscreenFrame) {
        fullscreenBtn.addEventListener('click', () => {
            fullscreenContainer.style.display = 'block';
            document.body.style.overflow = 'hidden';
        });

        exitFullscreenBtn.addEventListener('click', () => {
            fullscreenContainer.style.display = 'none';
            document.body.style.overflow = 'auto';
        });

        document.addEventListener('keydown', (e) => {
            if (e.key === "Escape" && fullscreenContainer.style.display === 'block') {
                exitFullscreenBtn.click();
            }
        });
    }
    
    document.getElementById('reload-dashboard-btn')?.addEventListener('click', loadDashboard); 
    document.getElementById('refresh-btn-dashboard')?.addEventListener('click', loadDashboard); 

    const downloadBtn = document.getElementById('download-btn-dashboard');
    if (downloadBtn) {
        downloadBtn.addEventListener('click', () => {
            if (typeof dashboardTemplateHtml === 'undefined' || dashboardTemplateHtml === null) {
                alert("No dashboard template available to download.");
                return;
            }
            const fullHtmlToDownload = buildFullHtml(dashboardTemplateHtml, actualDatasetData || []);
            const link = document.createElement('a');
            const blob = new Blob([fullHtmlToDownload], { type: 'text/html;charset=utf-8' });
            const url = URL.createObjectURL(blob);
            link.href = url;
            link.download = 'dynadash_dashboard.html';
            document.body.appendChild(link);
            link.click();
            document.body.removeChild(link);
            URL.revokeObjectURL(url);
        });
    }

    // Initial load
    if (document.readyState === 'complete' || (document.readyState !== 'loading' && !document.documentElement.doScroll)) {
      loadDashboard();
    } else {
      document.addEventListener('DOMContentLoaded', loadDashboard);
    }
});
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/profile.js

```
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

```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/upload.js

```
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

```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/view.js

```
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
```


### /mnt/c/Users/matth/Desktop/2-DSM/AgileWeb/Dynadash-15-05-25/DynaDash/app/static/js/visual.js

```
document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ visual.js loaded");

  // ---------- Share Page: confirm deletion ----------
  const unshareForms = document.querySelectorAll('form[action*="/unshare/"]');
  unshareForms.forEach(form => {
    form.addEventListener('submit', function (e) {
      const confirmed = confirm("Are you sure you want to remove this user's access?");
      if (!confirmed) {
        e.preventDefault();
      }
    });
  });

  // ---------- View Page: fullscreen mode ----------
  const fullscreenBtn = document.getElementById("fullscreen-btn");
  const exitFullscreenBtn = document.getElementById("exit-fullscreen-btn");
  const fullscreenContainer = document.getElementById("fullscreen-container");

  if (fullscreenBtn && exitFullscreenBtn && fullscreenContainer) {
    fullscreenBtn.addEventListener("click", () => {
      fullscreenContainer.style.display = "block";
      document.body.style.overflow = "hidden";
    });

    exitFullscreenBtn.addEventListener("click", () => {
      fullscreenContainer.style.display = "none";
      document.body.style.overflow = "auto";
    });

    document.addEventListener("keydown", (e) => {
      if (e.key === "Escape") {
        fullscreenContainer.style.display = "none";
        document.body.style.overflow = "auto";
      }
    });
  }

  // ---------- View Page: delete confirmation ----------
  const deleteBtn = document.querySelector('form[action*="/delete/"] button[type="submit"]');
  if (deleteBtn) {
    deleteBtn.addEventListener("click", function (e) {
      const confirmed = confirm("Are you sure you want to delete this dashboard?");
      if (!confirmed) e.preventDefault();
    });
  }

  // ---------- Shared Pages: auto-hide flash messages ----------
  const flash = document.querySelector(".alert");
  if (flash) {
    setTimeout(() => {
      flash.style.display = "none";
    }, 3000);
  }
});
```
