document.addEventListener("DOMContentLoaded", function () {
  console.log("✅ visual_generate.js loaded");

  const dashboardHtml = document.getElementById('dashboard-html').value;
  const dashboardFrame = document.getElementById('dashboard-frame');
  const fullscreenFrame = document.getElementById('fullscreen-frame');
  const loadingIndicator = document.getElementById('dashboard-loading');
  const dashboardError = document.getElementById('dashboard-error');

  function loadDashboard() {
    try {
      dashboardFrame.srcdoc = dashboardHtml;
      fullscreenFrame.srcdoc = dashboardHtml;

      dashboardFrame.onload = function () {
        loadingIndicator.style.display = 'none';
        dashboardFrame.style.display = 'block';
        checkDashboardLoaded();
      };

      dashboardFrame.onerror = function () {
        showDashboardError();
      };

      setTimeout(() => {
        if (loadingIndicator.style.display !== 'none') {
          checkDashboardLoaded();
        }
      }, 5000);
    } catch (err) {
      showDashboardError();
    }
  }

  function checkDashboardLoaded() {
    try {
      const frameDoc = dashboardFrame.contentDocument || dashboardFrame.contentWindow.document;
      if (frameDoc && frameDoc.body && frameDoc.body.innerHTML.length > 100) {
        loadingIndicator.style.display = 'none';
        dashboardFrame.style.display = 'block';
      } else {
        showDashboardError();
      }
    } catch (e) {
      showDashboardError();
    }
  }

  function showDashboardError() {
    loadingIndicator.style.display = 'none';
    dashboardError.style.display = 'block';
    dashboardFrame.style.display = 'none';
  }

  // Fullscreen controls
  const fullscreenBtn = document.getElementById('fullscreen-btn');
  const exitFullscreenBtn = document.getElementById('exit-fullscreen-btn');
  const fullscreenContainer = document.getElementById('fullscreen-container');

  fullscreenBtn?.addEventListener('click', () => {
    fullscreenContainer.style.display = 'block';
    document.body.style.overflow = 'hidden';
  });

  exitFullscreenBtn?.addEventListener('click', () => {
    fullscreenContainer.style.display = 'none';
    document.body.style.overflow = 'auto';
  });

  document.addEventListener('keydown', (e) => {
    if (e.key === "Escape") {
      fullscreenContainer.style.display = 'none';
      document.body.style.overflow = 'auto';
    }
  });

  // Reload buttons
  document.getElementById('reload-dashboard')?.addEventListener('click', () => {
    dashboardError.style.display = 'none';
    loadingIndicator.style.display = 'flex';
    dashboardFrame.style.display = 'none';
    setTimeout(loadDashboard, 300);
  });

  document.getElementById('refresh-btn')?.addEventListener('click', () => {
    dashboardError.style.display = 'none';
    loadingIndicator.style.display = 'flex';
    dashboardFrame.style.display = 'none';
    setTimeout(loadDashboard, 300);
  });

  // Download dashboard
  document.getElementById('download-btn')?.addEventListener('click', () => {
    const link = document.createElement('a');
    const blob = new Blob([dashboardHtml], { type: 'text/html' });
    const url = URL.createObjectURL(blob);
    link.href = url;
    link.download = 'dashboard.html';
    document.body.appendChild(link);
    link.click();
    document.body.removeChild(link);
    URL.revokeObjectURL(url);
  });

  // Start loading
  loadDashboard();
});