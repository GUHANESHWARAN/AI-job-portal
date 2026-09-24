document.addEventListener('DOMContentLoaded', function () {

  /* ── Sidebar toggle (mobile) ──────────────────────────────── */
  const profileMenu   = document.querySelector('.profile-menu');
  const profileTrigger = document.querySelector('.profile-trigger');
  const sidebar       = document.querySelector('.admin-sidebar');
  const toggleBtn     = document.querySelector('.sidebar-toggle');

  if (profileTrigger && profileMenu) {
    profileTrigger.addEventListener('click', function (e) {
      e.stopPropagation();
      profileMenu.classList.toggle('open');
    });
    document.addEventListener('click', function (e) {
      if (!profileMenu.contains(e.target)) {
        profileMenu.classList.remove('open');
      }
    });
  }

  if (toggleBtn && sidebar) {
    toggleBtn.addEventListener('click', function () {
      sidebar.classList.toggle('collapsed');
    });
  }

  /* ── Auto-dismiss Django messages / alerts ───────────────── */
  document.querySelectorAll('.alert').forEach(function (alert) {
    // Auto-close after 4 s
    const timer = setTimeout(function () { dismissAlert(alert); }, 4000);

    const closeBtn = alert.querySelector('.alert-close');
    if (closeBtn) {
      closeBtn.addEventListener('click', function () {
        clearTimeout(timer);
        dismissAlert(alert);
      });
    }
  });

  function dismissAlert(el) {
    el.style.transition = 'opacity 0.35s ease, transform 0.35s ease';
    el.style.opacity    = '0';
    el.style.transform  = 'translateY(-6px)';
    setTimeout(function () { el.remove(); }, 380);
  }

  /* ── Bar chart — animate bars on scroll ─────────────────── */
  if ('IntersectionObserver' in window) {
    const bars = document.querySelectorAll('.bar');
    const observer = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = el.style.height;
          el.style.height = '0';
          requestAnimationFrame(function () {
            el.style.transition = 'height 0.55s cubic-bezier(0.4,0,0.2,1)';
            el.style.height = target;
          });
          observer.unobserve(el);
        }
      });
    }, { threshold: 0.1 });

    bars.forEach(function (bar) { observer.observe(bar); });
  }

  /* ── Funnel bars — animate widths ────────────────────────── */
  if ('IntersectionObserver' in window) {
    const funnelBars = document.querySelectorAll('.funnel-bar');
    const funnelObs  = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = el.style.width;
          el.style.width = '0';
          requestAnimationFrame(function () {
            el.style.transition = 'width 0.65s cubic-bezier(0.4,0,0.2,1)';
            el.style.width = target;
          });
          funnelObs.unobserve(el);
        }
      });
    }, { threshold: 0.1 });

    funnelBars.forEach(function (bar) { funnelObs.observe(bar); });
  }

  /* ── Progress fill bars ───────────────────────────────────── */
  if ('IntersectionObserver' in window) {
    const fills = document.querySelectorAll('.progress-fill, .skill-bar-fill');
    const fillObs = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          const el = entry.target;
          const target = el.style.width;
          el.style.width = '0';
          requestAnimationFrame(function () {
            el.style.transition = 'width 0.5s cubic-bezier(0.4,0,0.2,1)';
            el.style.width = target;
          });
          fillObs.unobserve(el);
        }
      });
    }, { threshold: 0.1 });

    fills.forEach(function (fill) { fillObs.observe(fill); });
  }

  /* ── Confirm dangerous POST actions ─────────────────────── */
  document.querySelectorAll('[data-confirm]').forEach(function (el) {
    el.addEventListener('click', function (e) {
      if (!confirm(el.dataset.confirm)) {
        e.preventDefault();
        e.stopPropagation();
      }
    });
  });

  /* ── Auto-submit filter forms on select change ───────────── */
  document.querySelectorAll('.auto-submit select').forEach(function (sel) {
    sel.addEventListener('change', function () {
      sel.closest('form').submit();
    });
  });

});
