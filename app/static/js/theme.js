/**
 * theme.js — Light / Dark Mode Toggle
 * =====================================
 * HOW IT WORKS:
 * 1. On page load, read saved theme from localStorage
 * 2. Apply it immediately (before paint) to avoid flash
 * 3. When user clicks toggle, switch theme and save to localStorage
 * 4. Also send to server so the preference is saved in DB
 */

(function () {
  'use strict';

  // ── Apply theme immediately on script load (prevents flash) ──
  const savedTheme = localStorage.getItem('theme') === 'dark' ? 'dark' : 'light';
  document.documentElement.setAttribute('data-theme', savedTheme);

  // ── DOM ready ──
  document.addEventListener('DOMContentLoaded', function () {

    // Update all toggle buttons/icons to reflect current theme
    updateThemeUI(savedTheme);

    // Handle all elements with data-theme-toggle attribute
    document.querySelectorAll('[data-theme-toggle]').forEach(function (btn) {
      btn.addEventListener('click', function () {
        const currentTheme = document.documentElement.getAttribute('data-theme');
        const newTheme = currentTheme === 'dark' ? 'light' : 'dark';

        // Apply the new theme
        document.documentElement.setAttribute('data-theme', newTheme);
        localStorage.setItem('theme', newTheme);
        updateThemeUI(newTheme);

        // Save preference to server (non-blocking)
        fetch('/api/set-theme', {
          method: 'POST',
          headers: {
            'Content-Type': 'application/json',
            'X-CSRFToken': getCookie('csrf_token') ||
              (document.querySelector('meta[name="csrf-token"]') || {}).content || ''
          },
          body: JSON.stringify({ theme: newTheme })
        }).catch(function () {
          // Silent fail — localStorage preference still works
        });
      });
    });

    // Offer common mail apps before falling back to the device mail handler.
    document.querySelectorAll('.support-email-link').forEach(function (link) {
      link.addEventListener('click', function (event) {
        event.preventDefault();
        const email = link.dataset.supportEmail || 'neoskillzinfo@gmail.com';
        const encodedEmail = encodeURIComponent(email);
        const overlay = document.createElement('div');
        overlay.style.cssText = 'position:fixed;inset:0;z-index:2000;background:rgba(0,0,0,.55);display:flex;align-items:center;justify-content:center;padding:1rem;';
        overlay.innerHTML = '<div role="dialog" aria-modal="true" aria-label="Choose mail app" style="width:min(360px,100%);background:var(--bg-card);color:var(--text-primary);border:1px solid var(--border);border-radius:var(--radius-lg);padding:1.25rem;box-shadow:var(--shadow-lg);">' +
          '<h3 style="margin-bottom:.35rem;">Contact Support</h3>' +
          '<p style="color:var(--text-secondary);margin-bottom:1rem;">Choose a mail app for ' + email + '</p>' +
          '<div style="display:flex;flex-direction:column;gap:.5rem;">' +
          '<a class="btn btn-primary" href="https://mail.google.com/mail/?view=cm&fs=1&to=' + encodedEmail + '" target="_blank" rel="noopener"><i class="bi bi-google"></i> Gmail</a>' +
          '<a class="btn btn-outline" href="https://outlook.live.com/mail/0/deeplink/compose?to=' + encodedEmail + '" target="_blank" rel="noopener"><i class="bi bi-microsoft"></i> Outlook</a>' +
          '<a class="btn btn-outline" href="mailto:' + email + '"><i class="bi bi-envelope"></i> Default mail app</a>' +
          '<button type="button" class="btn btn-outline" data-close-mail-dialog>Cancel</button>' +
          '</div></div>';
        document.body.appendChild(overlay);
        overlay.querySelector('[data-close-mail-dialog]').addEventListener('click', function () {
          overlay.remove();
        });
        overlay.addEventListener('click', function (dialogEvent) {
          if (dialogEvent.target === overlay) overlay.remove();
        });
      });
    });

    // ── Profile Dropdown Toggle ──
    const avatarBtn = document.getElementById('avatarBtn');
    const profileDropdown = document.getElementById('profileDropdown');

    if (avatarBtn && profileDropdown) {
      avatarBtn.addEventListener('click', function (e) {
        e.stopPropagation();
        profileDropdown.classList.toggle('open');
      });

      // Close dropdown when clicking anywhere else
      document.addEventListener('click', function () {
        profileDropdown.classList.remove('open');
      });

      profileDropdown.addEventListener('click', function (e) {
        e.stopPropagation();
      });
    }

    // ── Auto-dismiss flash messages after 5 seconds ──
    document.querySelectorAll('.auto-dismiss').forEach(function (alert) {
      setTimeout(function () {
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(function () { alert.remove(); }, 300);
      }, 5000);
    });

    // ── Mobile Sidebar Toggle (Mentor) ──
    const sidebarToggle = document.getElementById('sidebarToggle');
    const mentorSidebar = document.getElementById('mentorSidebar');
    if (sidebarToggle && mentorSidebar) {
      sidebarToggle.addEventListener('click', function () {
        mentorSidebar.classList.toggle('open');
      });
    }

  });

  // ── Helper: Update UI elements to reflect current theme ──
  function updateThemeUI(theme) {
    const label = theme === 'dark' ? 'Switch to light theme' : 'Switch to dark theme';

    // Keep theme controls icon-only while preserving accessible labels.
    document.querySelectorAll('[data-theme-label]').forEach(function (el) {
      el.textContent = label;
    });
    document.querySelectorAll('[data-theme-icon]').forEach(function (el) {
      el.classList.toggle('bi-sun', theme === 'dark');
      el.classList.toggle('bi-moon-stars', theme !== 'dark');
      el.textContent = '';
      el.parentElement.setAttribute('aria-label', label);
      el.parentElement.setAttribute('title', label);
    });
  }

  // ── Helper: Get cookie by name (for CSRF token) ──
  function getCookie(name) {
    const match = document.cookie.match(new RegExp('(?:^|; )' + name + '=([^;]*)'));
    return match ? decodeURIComponent(match[1]) : null;
  }

})();
