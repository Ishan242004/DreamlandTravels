/* =========================================================
   Dreamland Travels — main.js
   Vanilla JS. No backend/API calls — all UI-only behavior.
   ========================================================= */

document.addEventListener('DOMContentLoaded', function () {

  /* ---------- Page loader ---------- */
  var loader = document.getElementById('page-loader');
  if (loader) {
    window.addEventListener('load', function () {
      setTimeout(function () { loader.classList.add('loaded'); }, 350);
    });
    // fallback in case 'load' already fired
    setTimeout(function () { loader.classList.add('loaded'); }, 1200);
  }

  /* ---------- Sticky navbar on scroll ---------- */
  var navbar = document.querySelector('.navbar-dreamland');
  function handleNavScroll() {
    if (!navbar) return;
    if (window.scrollY > 40) navbar.classList.add('scrolled');
    else navbar.classList.remove('scrolled');
  }
  handleNavScroll();
  window.addEventListener('scroll', handleNavScroll);

  /* ---------- Back to top ---------- */
  var backToTop = document.getElementById('back-to-top');
  if (backToTop) {
    window.addEventListener('scroll', function () {
      if (window.scrollY > 500) backToTop.classList.add('show');
      else backToTop.classList.remove('show');
    });
    backToTop.addEventListener('click', function () {
      window.scrollTo({ top: 0, behavior: 'smooth' });
    });
  }

  /* ---------- Scroll reveal animations ---------- */
  var revealEls = document.querySelectorAll('.reveal');
  if ('IntersectionObserver' in window && revealEls.length) {
    var io = new IntersectionObserver(function (entries) {
      entries.forEach(function (entry) {
        if (entry.isIntersecting) {
          entry.target.classList.add('in');
          io.unobserve(entry.target);
        }
      });
    }, { threshold: 0.15 });
    revealEls.forEach(function (el) { io.observe(el); });
  } else {
    revealEls.forEach(function (el) { el.classList.add('in'); });
  }

  /* ---------- Statistic counters ---------- */
  var counters = document.querySelectorAll('[data-counter]');
  if (counters.length) {
    var counted = new WeakSet();
    var runCounter = function (el) {
      var target = parseInt(el.getAttribute('data-counter'), 10) || 0;
      var duration = 1400;
      var start = null;
      var startVal = 0;
      function step(ts) {
        if (!start) start = ts;
        var progress = Math.min((ts - start) / duration, 1);
        var eased = 1 - Math.pow(1 - progress, 3);
        el.textContent = Math.floor(startVal + (target - startVal) * eased).toLocaleString();
        if (progress < 1) requestAnimationFrame(step);
        else el.textContent = target.toLocaleString();
      }
      requestAnimationFrame(step);
    };
    if ('IntersectionObserver' in window) {
      var cio = new IntersectionObserver(function (entries) {
        entries.forEach(function (entry) {
          if (entry.isIntersecting && !counted.has(entry.target)) {
            counted.add(entry.target);
            runCounter(entry.target);
          }
        });
      }, { threshold: 0.4 });
      counters.forEach(function (el) { cio.observe(el); });
    } else {
      counters.forEach(runCounter);
    }
  }

  /* ---------- Password show/hide toggle ---------- */
  document.querySelectorAll('.toggle-pw').forEach(function (btn) {
    btn.addEventListener('click', function () {
      var input = btn.parentElement.querySelector('input');
      if (!input) return;
      var isPw = input.getAttribute('type') === 'password';
      input.setAttribute('type', isPw ? 'text' : 'password');
      btn.querySelector('i').className = isPw ? 'bi bi-eye-slash' : 'bi bi-eye';
    });
  });

  /* ---------- Dashboard sidebar toggle (mobile) ---------- */
  var sidebarToggle = document.getElementById('sidebar-toggle-btn');
  var sidebar = document.querySelector('.dash-sidebar');
  if (sidebarToggle && sidebar) {
    sidebarToggle.addEventListener('click', function () {
      sidebar.classList.toggle('show');
    });
    document.addEventListener('click', function (e) {
      if (window.innerWidth <= 991 && sidebar.classList.contains('show') &&
          !sidebar.contains(e.target) && e.target !== sidebarToggle && !sidebarToggle.contains(e.target)) {
        sidebar.classList.remove('show');
      }
    });
  }

  /* ---------- Admin Sidebar Dropdown ---------- */
  document.querySelectorAll('.dash-dropdown-toggle').forEach(function(toggle) {
    toggle.addEventListener('click', function(e) {
      if (window.location.pathname.indexOf('admin-profile') !== -1) {
        e.preventDefault();
        var container = toggle.parentElement;
        container.classList.toggle('open');
      }
    });
  });

  /* ---------- Filter pill toggles (Packages page) ---------- */
  document.querySelectorAll('[data-filter-group]').forEach(function (group) {
    var pills = group.querySelectorAll('.filter-pill');
    pills.forEach(function (pill) {
      pill.addEventListener('click', function () {
        pills.forEach(function (p) { p.classList.remove('active'); });
        pill.classList.add('active');
      });
    });
  });

  /* ---------- Star rating widget (Feedback page) ---------- */
  document.querySelectorAll('.star-rating').forEach(function (group) {
    var stars = group.querySelectorAll('i');
    var hiddenInput = document.getElementById(group.getAttribute('data-target'));
    stars.forEach(function (star, idx) {
      star.addEventListener('mouseenter', function () {
        stars.forEach(function (s, i) { s.classList.toggle('hovered', i <= idx); });
      });
      star.addEventListener('click', function () {
        stars.forEach(function (s, i) { s.classList.toggle('active', i <= idx); });
        if (hiddenInput) hiddenInput.value = idx + 1;
      });
    });
    group.addEventListener('mouseleave', function () {
      stars.forEach(function (s) { s.classList.remove('hovered'); });
    });
  });

  /* ---------- Package details: gallery thumbnail swap ---------- */
  var heroImg = document.getElementById('gallery-main-img');
  document.querySelectorAll('.gallery-thumbs img').forEach(function (thumb) {
    thumb.addEventListener('click', function () {
      if (heroImg) heroImg.src = thumb.src.replace('w=300', 'w=1200');
    });
  });

  /* ---------- Payment method selector ---------- */
  document.querySelectorAll('.payment-method-card').forEach(function (card) {
    card.addEventListener('click', function () {
      document.querySelectorAll('.payment-method-card').forEach(function (c) { c.classList.remove('active-method'); });
      card.classList.add('active-method');
      var radio = card.querySelector('input[type="radio"]');
      if (radio) radio.checked = true;

      var method = card.getAttribute('data-method-option');
      if (method) {
        document.querySelectorAll('.method-detail-panel').forEach(function (panel) {
          panel.classList.toggle('d-none', panel.getAttribute('data-panel') !== method);
        });
      }
    });
  });

  /* ---------- Coupon apply (UI only) ---------- */
  var couponBtn = document.getElementById('apply-coupon-btn');
  if (couponBtn) {
    couponBtn.addEventListener('click', function (e) {
      e.preventDefault();
      var msg = document.getElementById('coupon-msg');
      var input = document.getElementById('coupon-input');
      if (msg && input) {
        if (input.value.trim().length > 0) {
          msg.textContent = 'Coupon "' + input.value.trim().toUpperCase() + '" applied — 10% off!';
          msg.className = 'small mt-2 text-success fw-semibold';
        } else {
          msg.textContent = 'Please enter a coupon code.';
          msg.className = 'small mt-2 text-danger fw-semibold';
        }
      }
    });
  }

  /* ---------- Print invoice ---------- */
  var printBtn = document.getElementById('print-invoice-btn');
  if (printBtn) printBtn.addEventListener('click', function () { window.print(); });

  /* ---------- Generic form "submit" UI feedback (frontend only, no backend) ---------- */
  document.querySelectorAll('form[data-ui-only]').forEach(function (form) {
    form.addEventListener('submit', function (e) {
      e.preventDefault();
      var alertBox = form.querySelector('.form-ui-alert');
      if (alertBox) {
        alertBox.classList.remove('d-none');
        setTimeout(function () { alertBox.classList.add('d-none'); }, 4000);
      }
    });
  });

  /* ---------- Bootstrap tooltips ---------- */
  var tooltipEls = [].slice.call(document.querySelectorAll('[data-bs-toggle="tooltip"]'));
  tooltipEls.forEach(function (el) {
    if (window.bootstrap) new bootstrap.Tooltip(el);
  });

  /* ---------- Auto-close mobile navbar on link click ---------- */
  document.querySelectorAll('.navbar-collapse .nav-link').forEach(function (link) {
    link.addEventListener('click', function () {
      var collapseEl = document.querySelector('.navbar-collapse.show');
      if (collapseEl && window.bootstrap) {
        bootstrap.Collapse.getOrCreateInstance(collapseEl).hide();
      }
    });
  });

  /* ---------- Select-all row checkboxes in admin tables ---------- */
  document.querySelectorAll('[data-check-all]').forEach(function (master) {
    master.addEventListener('change', function () {
      var table = master.closest('table');
      if (!table) return;
      table.querySelectorAll('tbody input[type="checkbox"]').forEach(function (cb) { cb.checked = master.checked; });
    });
  });

});

