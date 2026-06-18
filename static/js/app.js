/* MeetFlow front-end helpers: toasts, CSRF, AJAX для QR-сканера,
   живая проверка доступности комнаты, выход из комнаты без перезагрузки. */

(function () {
  'use strict';

  /* ---------- CSRF ---------- */

  function getCookie(name) {
    const value = `; ${document.cookie}`;
    const parts = value.split(`; ${name}=`);
    if (parts.length === 2) return decodeURIComponent(parts.pop().split(';').shift());
    return null;
  }

  function getCsrfToken() {
    const input = document.querySelector('input[name=csrfmiddlewaretoken]');
    if (input) return input.value;
    return getCookie('csrftoken');
  }

  /* ---------- Toasts ---------- */

  function ensureToastStack() {
    let stack = document.querySelector('.toast-stack');
    if (!stack) {
      stack = document.createElement('div');
      stack.className = 'toast-stack';
      document.body.appendChild(stack);
    }
    return stack;
  }

  function showToast(message, type) {
    const stack = ensureToastStack();
    const toast = document.createElement('div');
    toast.className = `app-toast toast-${type === 'error' ? 'error' : 'success'}`;

    const icon = document.createElement('span');
    icon.className = 'toast-icon';
    icon.innerHTML = type === 'error'
      ? '<i class="fas fa-circle-exclamation"></i>'
      : '<i class="fas fa-circle-check"></i>';

    const text = document.createElement('span');
    text.textContent = message;

    toast.appendChild(icon);
    toast.appendChild(text);
    stack.appendChild(toast);

    setTimeout(() => {
      toast.style.opacity = '0';
      toast.style.transition = 'opacity 0.25s ease';
      setTimeout(() => toast.remove(), 250);
    }, 4200);
  }

  window.MeetFlow = window.MeetFlow || {};
  window.MeetFlow.showToast = showToast;
  window.MeetFlow.getCsrfToken = getCsrfToken;

  /* ---------- Django messages -> toasts ---------- */

  document.addEventListener('DOMContentLoaded', () => {
    document.querySelectorAll('[data-django-message]').forEach((el) => {
      const level = el.getAttribute('data-django-message');
      showToast(el.textContent.trim(), level === 'error' ? 'error' : 'success');
    });
  });

  /* ---------- QR-сканер (AJAX) ---------- */

  function initQrScanner() {
    const form = document.querySelector('[data-qr-form]');
    if (!form) return;

    const input = form.querySelector('#qr_code');
    const submitBtn = form.querySelector('button[type=submit]');
    const resultBox = document.querySelector('[data-scanner-result]');

    function setResult(message, isSuccess) {
      if (!resultBox) return;
      resultBox.textContent = message;
      resultBox.classList.remove('is-success', 'is-error');
      resultBox.classList.add('is-visible', isSuccess ? 'is-success' : 'is-error');
    }

    form.addEventListener('submit', async (event) => {
      event.preventDefault();
      const qrCode = (input.value || '').trim();
      if (!qrCode) {
        setResult('Введите идентификатор QR-кода', false);
        return;
      }

      submitBtn.disabled = true;
      const originalLabel = submitBtn.textContent;
      submitBtn.textContent = 'Проверяем доступ…';

      try {
        const response = await fetch(form.action, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
          },
          body: new URLSearchParams({ qr_code: qrCode }),
        });
        const data = await response.json();

        if (data.success) {
          setResult(data.message, true);
          showToast(data.message, 'success');
          input.value = '';
          if (typeof window.MeetFlow.onEntryCreated === 'function') {
            window.MeetFlow.onEntryCreated(data);
          }
        } else {
          setResult(data.message || 'Не удалось подтвердить доступ', false);
          showToast(data.message || 'Не удалось подтвердить доступ', 'error');
        }
      } catch (err) {
        setResult('Ошибка соединения с сервером. Попробуйте снова.', false);
        showToast('Ошибка соединения с сервером', 'error');
      } finally {
        submitBtn.disabled = false;
        submitBtn.textContent = originalLabel;
      }
    });
  }

  /* ---------- Выход из комнаты без перезагрузки ---------- */

  function initExitButtons() {
    document.body.addEventListener('click', async (event) => {
      const btn = event.target.closest('[data-exit-entry]');
      if (!btn) return;

      event.preventDefault();
      const url = btn.getAttribute('data-exit-url');
      btn.disabled = true;
      const originalLabel = btn.textContent;
      btn.textContent = 'Выходим…';

      try {
        const response = await fetch(url, {
          method: 'POST',
          headers: {
            'X-CSRFToken': getCsrfToken(),
            'X-Requested-With': 'XMLHttpRequest',
          },
        });
        const data = await response.json();

        if (data.success) {
          showToast(data.message, 'success');
          const row = btn.closest('[data-entry-row]');
          if (row) {
            const statusEl = row.querySelector('[data-exit-status]');
            if (statusEl) statusEl.textContent = 'вышел';
            btn.remove();
          }
        } else {
          showToast(data.message || 'Не удалось зафиксировать выход', 'error');
          btn.disabled = false;
          btn.textContent = originalLabel;
        }
      } catch (err) {
        showToast('Ошибка соединения с сервером', 'error');
        btn.disabled = false;
        btn.textContent = originalLabel;
      }
    });
  }

  /* ---------- Подтверждение перед отменой бронирования ---------- */

  function initCancelConfirm() {
    document.querySelectorAll('[data-confirm]').forEach((form) => {
      form.addEventListener('submit', (event) => {
        const message = form.getAttribute('data-confirm');
        if (message && !window.confirm(message)) {
          event.preventDefault();
        }
      });
    });
  }

  /* ---------- Theme toggle ---------- */

  function initThemeToggle() {
    const html = document.documentElement;
    const toggle = document.querySelector('.theme-toggle');
    if (!toggle) return;

    const saved = localStorage.getItem('theme');
    if (saved === 'light') {
      html.setAttribute('data-theme', 'light');
    } else if (!saved && window.matchMedia('(prefers-color-scheme: light)').matches) {
      html.setAttribute('data-theme', 'light');
    }

    toggle.addEventListener('click', function(e) {
      e.preventDefault();
      const isLight = html.getAttribute('data-theme') === 'light';
      if (isLight) {
        html.removeAttribute('data-theme');
        localStorage.setItem('theme', 'dark');
      } else {
        html.setAttribute('data-theme', 'light');
        localStorage.setItem('theme', 'light');
      }
    });
  }

  /* ---------- Auto-dismiss alerts ---------- */

  function initAutoDismissAlerts() {
    document.querySelectorAll('.alert-card').forEach((alert) => {
      setTimeout(() => {
        alert.style.transition = 'opacity 0.4s ease, transform 0.4s ease';
        alert.style.opacity = '0';
        alert.style.transform = 'translateY(-10px)';
        setTimeout(() => alert.remove(), 400);
      }, 4500);
    });
  }

  document.addEventListener('DOMContentLoaded', () => {
    initQrScanner();
    initExitButtons();
    initCancelConfirm();
    initThemeToggle();
    initAutoDismissAlerts();
  });
})();
