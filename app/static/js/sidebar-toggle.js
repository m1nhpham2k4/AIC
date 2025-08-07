document.addEventListener("DOMContentLoaded", () => {
  const layout = document.querySelector(".layout");
  const toggleBtn = document.querySelector(".sidebar-toggle");

  if (layout && toggleBtn) {
    toggleBtn.addEventListener("click", () => {
      layout.classList.toggle("collapsed");
    });
  }
});
