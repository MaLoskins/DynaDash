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