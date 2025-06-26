document.addEventListener('DOMContentLoaded', function () {
  const menuToggle = document.getElementById('menuToggle');
  const sidebar = document.querySelector('.sidebar');
  const mainContent = document.querySelector('.main-content');

  if (menuToggle && sidebar && mainContent) {
    menuToggle.addEventListener('click', function () {
      sidebar.classList.toggle('open');
      mainContent.classList.toggle('expanded');
    });

    // Optional: Close sidebar when clicking outside
    document.addEventListener('click', function (event) {
      if (window.innerWidth <= 768) {
        const isInsideSidebar = sidebar.contains(event.target);
        const isToggle = menuToggle.contains(event.target);

        if (!isInsideSidebar && !isToggle && sidebar.classList.contains('open')) {
          sidebar.classList.remove('open');
          mainContent.classList.remove('expanded');
        }
      }
    });
  }
});
