/**
 * Main application JavaScript utilities
 * Senior Full-Stack Design System Interactions
 */

// CSRF Cookie Helper for Django AJAX Requests
function getCookie(name) {
  let cookieValue = null;
  if (document.cookie && document.cookie !== '') {
    const cookies = document.cookie.split(';');
    for (let i = 0; i < cookies.length; i++) {
      const cookie = cookies[i].trim();
      if (cookie.substring(0, name.length + 1) === (name + '=')) {
        cookieValue = decodeURIComponent(cookie.substring(name.length + 1));
        break;
      }
    }
  }
  return cookieValue;
}

document.addEventListener('DOMContentLoaded', () => {
  // Auto-dismiss alert banners with smooth slide-fade
  const alerts = document.querySelectorAll('.alert');
  alerts.forEach(alert => {
    const timer = setTimeout(() => {
      dismissAlert(alert);
    }, 5000);

    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', (e) => {
        e.preventDefault();
        clearTimeout(timer);
        dismissAlert(alert);
      });
    }
  });

  function dismissAlert(el) {
    el.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
    el.style.opacity = '0';
    el.style.transform = 'translateY(-8px)';
    setTimeout(() => {
      if (el.parentNode) el.remove();
    }, 380);
  }

  // Active navigation link highlighting based on current path
  const currentPath = window.location.pathname;
  document.querySelectorAll('.nav-menu .nav-link').forEach(link => {
    const href = link.getAttribute('href');
    if (href && href !== '/' && currentPath.startsWith(href)) {
      link.classList.add('active');
    } else if (href === '/' && currentPath === '/') {
      link.classList.add('active');
    }
  });
});
