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