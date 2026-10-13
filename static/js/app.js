(() => {
  'use strict';

  const $ = (selector, root = document) => root.querySelector(selector);
  const $$ = (selector, root = document) => Array.from(root.querySelectorAll(selector));
  const providerNames = {
    ubuntu: 'Ubuntu', almalinux: 'AlmaLinux', fedora: 'Fedora',
    rockylinux: 'Rocky Linux', debian: 'Debian', archlinux: 'Arch Linux', centos: 'CentOS Stream'
  };
  let sessionLogoutStarted = false;

  async function expireBrowserSession() {
    if (sessionLogoutStarted) return;
    sessionLogoutStarted = true;
    try {
      await fetch('/logout', { method: 'POST', credentials: 'same-origin', redirect: 'manual' });
    } catch (error) {
      console.warn('WatchTower could not clear the expired browser session.', error);
    }
    window.location.assign('/login?expired=1');
  }

  function initializeSessionExpiration() {
    const expiresAt = Number(document.body.dataset.sessionExpiresAt) * 1000;
    if (!Number.isFinite(expiresAt) || expiresAt <= 0) return;
    const check = () => {
      const remaining = expiresAt - Date.now();
      if (remaining <= 0) {
        expireBrowserSession();
        return;
      }
      window.setTimeout(check, Math.min(remaining, 2147483647));
    };
    check();
    document.addEventListener('visibilitychange', () => {
      if (!document.hidden && Date.now() >= expiresAt) expireBrowserSession();
    });
    window.addEventListener('focus', () => {
      if (Date.now() >= expiresAt) expireBrowserSession();
    });
  }

  function escapeHtml(value) {
    return String(value ?? '').replace(/[&<>"']/g, char => ({
      '&': '&amp;', '<': '&lt;', '>': '&gt;', '"': '&quot;', "'": '&#39;'
    })[char]);
  }

  async function api(path, options = {}) {
    const response = await fetch(path, { credentials: 'same-origin', ...options });
    if (response.status === 401) {
      expireBrowserSession();
      throw new Error('Your session has expired. Please log in again.');
    }
    const contentType = response.headers.get('content-type') || '';
    const body = contentType.includes('application/json') ? await response.json() : null;
    if (!response.ok) throw new Error(body?.detail || body?.error || `Request failed (${response.status})`);
    return body;
  }

  function dateText(value) {
    if (!value) return '—';
    const date = parseApiDate(value);
    return Number.isNaN(date.valueOf()) ? String(value) : new Intl.DateTimeFormat(undefined, {
      year: 'numeric', month: 'short', day: 'numeric', hour: 'numeric', minute: '2-digit'
    }).format(date);
  }

  function relativeTime(value) {
    if (!value) return '—';
    const date = parseApiDate(value);
    if (Number.isNaN(date.valueOf())) return '—';
    const seconds = Math.max(0, Math.floor((Date.now() - date.valueOf()) / 1000));
    if (seconds < 60) return 'just now';
    if (seconds < 3600) return `${Math.floor(seconds / 60)} min ago`;
    if (seconds < 86400) return `${Math.floor(seconds / 3600)} hr ago`;
    return `${Math.floor(seconds / 86400)} days ago`;
  }

  function parseApiDate(value) {
    if (value instanceof Date) return value;
    const normalized = typeof value === 'string' && !/(Z|[+-]\d{2}:?\d{2})$/i.test(value)
      ? `${value}Z`
      : value;
    return new Date(normalized);
  }

  function relativeUntil(value) {
    if (!value) return '—';
    const date = parseApiDate(value);
    if (Number.isNaN(date.valueOf())) return '—';
    const minutes = Math.ceil((date.valueOf() - Date.now()) / 60000);
    if (minutes <= 0) return 'Due now';
    if (minutes < 60) return `In ${minutes} min`;
    const hours = Math.floor(minutes / 60);
    const remainder = minutes % 60;
    return remainder ? `In ${hours} hr ${remainder} min` : `In ${hours} hr`;
  }

  function typeLabel(value) {
    if (!value) return 'Unknown';
    if (value === 'rolling') return 'Rolling';
    return value.charAt(0).toUpperCase() + value.slice(1);
  }

  function toast(message) {
    const region = $('#toast-region');
    if (!region) return;
    const item = document.createElement('div');
    item.className = 'toast';
    item.textContent = message;
    region.append(item);
    window.setTimeout(() => item.remove(), 4500);
  }

  function initializeTheme() {
    try {
      const saved = window.localStorage.getItem('os-tracker-theme');
      if (saved === 'dark' || saved === 'light') document.documentElement.dataset.theme = saved;
    } catch (error) {
      console.warn('WatchTower could not read the saved theme preference.', error);
    }
    $$('#theme-toggle').forEach(button => button.addEventListener('click', () => {
      const next = document.documentElement.dataset.theme === 'dark' ? 'light' : 'dark';
      document.documentElement.dataset.theme = next;
      try {
        window.localStorage.setItem('os-tracker-theme', next);
      } catch (error) {
        console.warn('WatchTower could not save the theme preference.', error);
      }
    }));
  }

  function initializeMobileMenu() {
    const button = $('#menu-toggle');
    const scrim = $('#mobile-scrim');
    if (!button || !scrim) return;
    const close = () => {
      document.body.classList.remove('menu-open');
      button.setAttribute('aria-expanded', 'false');
    };
    button.addEventListener('click', () => {
      const open = document.body.classList.toggle('menu-open');
      button.setAttribute('aria-expanded', String(open));
    });
    scrim.addEventListener('click', close);
    $$('.nav-link').forEach(link => link.addEventListener('click', close));
  }

  function initializeLogin() {
    const form = $('#login-form');
    if (!form) return;
    const errorBox = $('#login-error');
    const button = $('#login-submit');
    form.addEventListener('submit', async event => {
      event.preventDefault();
      errorBox.hidden = true;
      button.disabled = true;
      button.querySelector('span').textContent = 'Signing in…';
      try {
        const body = new URLSearchParams({
          username: $('#username').value,
          password: $('#password').value
        });
        const response = await fetch('/api/v1/auth/token', {
          method: 'POST', credentials: 'same-origin',
          headers: { 'Content-Type': 'application/x-www-form-urlencoded' }, body
        });
        const payload = await readLoginResponse(response, 'sign-in');
        if (!payload.access_token || typeof payload.access_token !== 'string') {
          throw new Error('WatchTower returned an invalid sign-in response. Please try again.');
        }
        const session = await fetch('/web/session', {
          method: 'POST', credentials: 'same-origin',
          headers: { 'Content-Type': 'application/json' },
          body: JSON.stringify({ access_token: payload.access_token })
        });
        const sessionPayload = await readLoginResponse(session, 'session');
        if (sessionPayload.ok !== true) {
          throw new Error('WatchTower could not establish a browser session. Please try again.');
        }
        window.location.assign('/dashboard');
      } catch (error) {
        console.error('WatchTower sign-in failed.', error);
        errorBox.textContent = error instanceof TypeError
          ? 'Cannot connect to WatchTower. Check the server address and try again.'
          : (error.message || 'Sign in failed. Please try again.');
        errorBox.hidden = false;
      } finally {
        button.disabled = false;
        button.querySelector('span').textContent = 'Sign in';
      }
    });
  }

  async function readLoginResponse(response, stage) {
    const contentType = response.headers.get('content-type') || '';
    let payload = null;
    if (contentType.includes('application/json')) {
      try { payload = await response.json(); }
      catch (error) {
        console.error(`WatchTower ${stage} endpoint returned invalid JSON.`, error);
        throw new Error('WatchTower returned an invalid response. Please try again.');
      }
    }
    if (!response.ok) {
      if (response.status === 401) throw new Error('Invalid username or password.');
      if (response.status >= 500) throw new Error('WatchTower could not complete sign-in because of a server error.');
      throw new Error(payload?.detail || `WatchTower sign-in failed (${response.status}).`);
    }
    if (!payload || typeof payload !== 'object') {
      throw new Error('WatchTower returned an unexpected response. Please try again.');
    }
    return payload;
  }

  function renderStatus(label, kind) {
    const classes = { good: 'status-good', error: 'status-error', major: 'status-major', unknown: 'status-unknown' };
    return `<span class="status-badge ${classes[kind] || classes.unknown}">${escapeHtml(label)}</span>`;
  }

  function renderOsRows(osRows, providerSlugs, statusData) {
    const body = $('#os-table-body');
    if (!body) return;
    const bySlug = new Map(osRows.map(row => [row.slug, row]));
    const errors = new Map((statusData.errors || []).map(item => [item.slug, item.error]));
    const checked = new Set((statusData.results || []).map(item => item.slug));
    const slugs = [...new Set([...providerSlugs, ...osRows.map(row => row.slug)])];
    if (!slugs.length) {
      body.innerHTML = '<tr><td colspan="6" class="empty-state">No providers are configured.</td></tr>';
      return;
    }
    body.innerHTML = slugs.map(slug => {
      const row = bySlug.get(slug);
      const name = row?.name || providerNames[slug] || slug;
      const error = errors.get(slug);
      let status;
      let detail = '';
      if (error) { status = renderStatus('Error', 'error'); detail = `<span class="provider-error-detail">${escapeHtml(error)}</span>`; }
      else if (statusData.checked !== null && statusData.checked !== undefined) {
        status = checked.has(slug) ? renderStatus('Up to date', 'good') : renderStatus('Not checked', 'unknown');
      } else if (!row || !row.checked_at) status = renderStatus('Never checked', 'unknown');
      else status = renderStatus('Status unavailable', 'unknown');
      const version = row ? escapeHtml(row.version) : '—';
      const major = row?.is_rolling ? 'Rolling' : escapeHtml(row?.major_version || '—');
      const type = row?.is_rolling ? 'rolling' : row?.release_type;
      const lastChecked = row?.last_checked ?? row?.checked_at;
      const checkedAt = relativeTime(lastChecked);
      return `<tr>
        <td><a class="os-name row-link" href="/os/${encodeURIComponent(slug)}"><span class="os-logo">${escapeHtml(name.slice(0, 2))}</span>${escapeHtml(name)}</a></td>
        <td><a class="row-link" href="/os/${encodeURIComponent(slug)}">${version}</a></td>
        <td>${major}</td><td><span class="release-type type-${escapeHtml(type || 'unknown')}">${escapeHtml(typeLabel(type))}</span></td>
        <td title="${escapeHtml(dateText(lastChecked))}">${escapeHtml(checkedAt)}</td><td>${status}${detail}</td>
      </tr>`;
    }).join('');
  }

  function renderMajorAlerts(events) {
    const container = $('#major-alerts');
    if (!container) return;
    container.innerHTML = events.length ? events.map(event => `<article class="release-alert">
      <span class="alert-icon" aria-hidden="true">↗</span><div class="alert-copy">
      <strong>New Major Release · ${escapeHtml(event.name)}</strong>
      <span>${escapeHtml(event.previous_version || 'Unknown')} → ${escapeHtml(event.new_version)}</span></div>
      <a class="button button-subtle" href="/os/${encodeURIComponent(event.os)}">View details</a></article>`).join('') : '';
  }

  function renderCheckSummary(result) {
    const box = $('#check-summary');
    if (!box) return;
    const errors = result.errors || [];
    box.hidden = false;
    box.innerHTML = `<h3>Provider check complete</h3><div class="check-counts">
      <span>Checked <strong>${Number(result.checked) || 0}</strong></span>
      <span>Failed <strong>${Number(result.failed) || 0}</strong></span>
      <span>Changed <strong>${Number(result.changed) || 0}</strong></span>
      <span>Major releases <strong>${Number(result.major_releases) || 0}</strong></span></div>
      ${errors.length ? `<ul class="error-list">${errors.map(item => `<li><strong>${escapeHtml(providerNames[item.slug] || item.slug)}:</strong> ${escapeHtml(item.error)}</li>`).join('')}</ul>` : ''}`;
  }

  let releaseChart;
  async function renderReleaseChart() {
    const canvas = $('#release-chart');
    const fallback = $('#chart-fallback');
    if (!canvas) return;
    try {
      const page = await api('/api/v1/releases?limit=100&offset=0');
      const rows = page.items || [];
      const counts = new Map();
      rows.forEach(row => counts.set(row.name, (counts.get(row.name) || 0) + 1));
      if (!window.Chart) throw new Error('Chart.js unavailable');
      const labels = Array.from(counts.keys());
      releaseChart?.destroy();
      releaseChart = new window.Chart(canvas, {
        type: 'bar',
        data: { labels, datasets: [{ label: 'Stored releases', data: labels.map(label => counts.get(label)), backgroundColor: '#537bd8', borderRadius: 5, maxBarThickness: 35 }] },
        options: { responsive: true, maintainAspectRatio: false, plugins: { legend: { display: false } }, scales: { x: { grid: { display: false }, ticks: { color: getComputedStyle(document.documentElement).getPropertyValue('--muted') } }, y: { beginAtZero: true, ticks: { precision: 0 }, grid: { color: getComputedStyle(document.documentElement).getPropertyValue('--line') } } } }
      });
      if (!rows.length) fallback.hidden = false;
    } catch (_) {
      fallback.hidden = false;
    }
  }

  async function loadDashboard({ throwOnError = false } = {}) {
    const isOsIndex = document.body.dataset.osIndex === 'true';
    try {
      const [osRows, providerData, statusData] = await Promise.all([
        api('/api/v1/os'), api('/api/v1/providers'), api('/api/v1/status')
      ]);
      renderOsRows(osRows, providerData.providers || [], statusData);
      if (!isOsIndex) {
        try { renderMajorAlerts((await api('/api/v1/events?event_type=new_major_release')).slice(0, 5)); } catch (_) {}
      }
      if (isOsIndex) return;
      $('#summary-tracked').textContent = statusData.tracked_os ?? '—';
      $('#summary-healthy').textContent = statusData.checked == null ? '—' : statusData.checked;
      $('#summary-errors').textContent = statusData.provider_errors == null ? '—' : statusData.provider_errors;
      $('#summary-majors').textContent = statusData.major_releases ?? '—';
      $('#summary-last-check').textContent = relativeTime(statusData.scheduler.last_check);
      $('#summary-next-check').textContent = relativeUntil(statusData.scheduler.next_check);
      const jobState = statusData.scheduler.job_state || (statusData.scheduler.running ? 'scheduled' : 'stopped');
      const jobHealthy = jobState === 'scheduled';
      $('#scheduler-label').textContent = jobHealthy ? 'Check job scheduled' : `Check job ${jobState}`;
      const state = $('#scheduler-state');
      state.classList.toggle('scheduler-error', !jobHealthy);
      const jobStateLabel = jobState.charAt(0).toUpperCase() + jobState.slice(1);
      state.innerHTML = `<span class="status-dot"></span><strong>${escapeHtml(jobStateLabel)}</strong>`;
      $('#scheduler-interval').textContent = statusData.scheduler.schedule || '—';
      $('#scheduler-last').textContent = dateText(statusData.scheduler.last_check);
      $('#scheduler-next').textContent = dateText(statusData.scheduler.next_check);
      const button = $('#check-now');
      if (button) button.onclick = async () => {
        button.disabled = true;
        button.querySelector('span:last-child').textContent = 'Checking…';
        try {
          const result = await api('/api/v1/check', { method: 'POST' });
          renderCheckSummary(result);
          await loadDashboard({ throwOnError: true });
          if (result.failed) toast(`${result.failed} provider check(s) failed. See the check summary.`);
          else toast('Provider check completed successfully.');
        } catch (error) { toast(error.message); }
        finally { button.disabled = false; button.querySelector('span:last-child').textContent = 'Check now'; }
      };
      if (!window.__osTrackerRefreshBound) {
        window.__osTrackerRefreshBound = true;
        window.setInterval(() => loadDashboard().catch(error => toast(`Dashboard refresh failed: ${error.message}`)), 30000);
      }
      renderReleaseChart();
    } catch (error) {
      if (throwOnError) throw error;
      const body = $('#os-table-body');
      if (body) body.innerHTML = `<tr><td colspan="6" class="empty-state">${escapeHtml(error.message)}</td></tr>`;
    }
  }

  async function loadOsDetail() {
    const container = $('#os-detail');
    if (!container) return;
    const slug = container.dataset.slug;
    try {
      const [os, history, status] = await Promise.all([
        api(`/api/v1/os/${encodeURIComponent(slug)}`),
        api(`/api/v1/releases/${encodeURIComponent(slug)}`),
        api('/api/v1/status')
      ]);
      $('#detail-name').textContent = os.name;
      $('#detail-subtitle').textContent = os.is_rolling ? 'Rolling release · ISO publication tracking' : `Current ${typeLabel(os.release_type).toLowerCase()} release`;
      $('#detail-version').textContent = os.version;
      $('#detail-major').textContent = os.is_rolling ? 'Rolling' : os.major_version;
      $('#detail-type').textContent = os.is_rolling ? 'Rolling' : typeLabel(os.release_type);
      $('#detail-checked').textContent = dateText(os.last_checked || os.checked_at);
      const source = $('#detail-source');
      if (os.source_url) { source.href = os.source_url; source.textContent = 'Open official release source ↗'; }
      const error = (status.errors || []).find(item => item.slug === slug);
      const hasLatestCheck = status.checked !== null && status.checked !== undefined;
      $('#detail-status').outerHTML = error ? renderStatus('Provider error', 'error') : (hasLatestCheck ? renderStatus('Up to date', 'good') : renderStatus('Status unavailable', 'unknown'));
      $('#detail-provider-status').textContent = error ? error.error : (hasLatestCheck ? 'The provider returned successfully during the latest check.' : 'No current provider check status is available.');
      const body = $('#detail-history');
      body.innerHTML = history.length ? history.map(item => `<tr><td><strong>${escapeHtml(item.version)}</strong></td><td>${os.is_rolling ? 'Rolling' : escapeHtml(item.major_version)}</td><td><span class="release-type type-${escapeHtml(item.release_type)}">${escapeHtml(typeLabel(item.release_type))}</span></td><td>${escapeHtml(item.release_date || '—')}</td><td title="${escapeHtml(dateText(item.detected_at))}">${escapeHtml(relativeTime(item.detected_at))}</td></tr>`).join('') : '<tr><td colspan="5" class="empty-state">No release history is available.</td></tr>';
    } catch (error) {
      $('#detail-name').textContent = 'Operating system unavailable';
      $('#detail-subtitle').textContent = error.message;
      $('#detail-history').innerHTML = '<tr><td colspan="5" class="empty-state">Unable to load release history.</td></tr>';
    }
  }

  function queryValue(params, key) { return params.get(key) || ''; }
  function updateQuery(params) {
    const search = params.toString();
    window.history.replaceState({}, '', `${window.location.pathname}${search ? `?${search}` : ''}`);
  }

  async function fillOsFilter(select) {
    const rows = await api('/api/v1/os');
    rows.forEach(row => {
      const option = document.createElement('option');
      option.value = row.slug;
      option.textContent = row.name;
      select.append(option);
    });
  }

  async function loadReleases(offset) {
    const params = new URLSearchParams(window.location.search);
    params.set('limit', '50');
    params.set('offset', String(offset));
    const query = new URLSearchParams();
    for (const key of ['os', 'type', 'date', 'limit', 'offset']) if (params.has(key)) query.set(key, params.get(key));
    try {
      const result = await api(`/api/v1/releases?${query.toString()}`);
      $('#release-table').innerHTML = result.items.length ? result.items.map(row => `<tr><td><a class="row-link" href="/os/${encodeURIComponent(row.os)}">${escapeHtml(row.name)}</a></td><td><strong>${escapeHtml(row.version)}</strong></td><td>${escapeHtml(row.major_version)}</td><td><span class="release-type type-${escapeHtml(row.release_type)}">${escapeHtml(typeLabel(row.release_type))}</span></td><td>${escapeHtml(row.release_date || '—')}</td><td title="${escapeHtml(dateText(row.detected_at))}">${escapeHtml(relativeTime(row.detected_at))}</td></tr>`).join('') : '<tr><td colspan="6" class="empty-state">No releases match these filters.</td></tr>';
      $('#release-count').textContent = `${result.total} release${result.total === 1 ? '' : 's'} found`;
      const page = Math.floor(result.offset / result.limit) + 1;
      const pages = Math.max(1, Math.ceil(result.total / result.limit));
      $('#page-label').textContent = `Page ${page} of ${pages}`;
      $('#page-previous').disabled = result.offset <= 0;
      $('#page-next').disabled = result.offset + result.limit >= result.total;
      $('#page-previous').onclick = () => loadReleases(Math.max(0, result.offset - result.limit));
      $('#page-next').onclick = () => loadReleases(result.offset + result.limit);
    } catch (error) { $('#release-table').innerHTML = `<tr><td colspan="6" class="empty-state">${escapeHtml(error.message)}</td></tr>`; }
  }

  async function initializeReleases() {
    const params = new URLSearchParams(window.location.search);
    const osFilter = $('#filter-os');
    try { await fillOsFilter(osFilter); } catch (_) {}
    osFilter.value = queryValue(params, 'os');
    $('#filter-type').value = queryValue(params, 'type');
    $('#filter-date').value = queryValue(params, 'date');
    $('#release-filters').addEventListener('submit', event => {
      event.preventDefault();
      const next = new URLSearchParams();
      if (osFilter.value) next.set('os', osFilter.value);
      if ($('#filter-type').value) next.set('type', $('#filter-type').value);
      if ($('#filter-date').value) next.set('date', $('#filter-date').value);
      updateQuery(next);
      loadReleases(0);
    });
    loadReleases(Number(params.get('offset')) || 0);
  }

  async function loadEvents() {
    const params = new URLSearchParams(window.location.search);
    const query = new URLSearchParams();
    if (params.has('os')) query.set('os', params.get('os'));
    if (params.has('event_type')) query.set('event_type', params.get('event_type'));
    try {
      const items = await api(`/api/v1/events${query.size ? `?${query}` : ''}`);
      const body = $('#event-table');
      body.innerHTML = items.length ? items.map(item => {
        const isMajor = item.event_type === 'new_major_release';
        const isRolling = item.event_type === 'new_rolling_release';
        const label = isMajor ? 'New major release' : (isRolling ? 'New rolling release' : (item.event_type === 'new_minor_release' ? 'New minor release' : typeLabel(item.event_type)));
        const kind = isMajor ? 'major' : 'unknown';
        return `<tr><td>${renderStatus(label, kind)}</td><td><a class="row-link" href="/os/${encodeURIComponent(item.os)}">${escapeHtml(item.name)}</a></td><td>${escapeHtml(item.previous_version || '—')} → <strong>${escapeHtml(item.new_version)}</strong></td><td title="${escapeHtml(dateText(item.detected_at))}">${escapeHtml(relativeTime(item.detected_at))}</td><td>${item.notification_sent ? renderStatus('Sent', 'good') : renderStatus('Pending', 'unknown')}</td></tr>`;
      }).join('') : '<tr><td colspan="5" class="empty-state">No recorded release events match these filters.</td></tr>';
    } catch (error) { $('#event-table').innerHTML = `<tr><td colspan="5" class="empty-state">${escapeHtml(error.message)}</td></tr>`; }
  }

  async function initializeEvents() {
    const params = new URLSearchParams(window.location.search);
    const osFilter = $('#event-os');
    try { await fillOsFilter(osFilter); } catch (_) {}
    osFilter.value = queryValue(params, 'os');
    $('#event-type').value = queryValue(params, 'event_type');
    $('#event-filters').addEventListener('submit', event => {
      event.preventDefault();
      const next = new URLSearchParams();
      if (osFilter.value) next.set('os', osFilter.value);
      if ($('#event-type').value) next.set('event_type', $('#event-type').value);
      updateQuery(next);
      loadEvents();
    });
    loadEvents();
  }

  async function initializeSettings() {
    try {
      const [status, providers] = await Promise.all([api('/api/v1/status'), api('/api/v1/providers')]);
      $('#settings-interval').textContent = status.scheduler.schedule || '—';
      const jobState = status.scheduler.job_state || (status.scheduler.running ? 'scheduled' : 'stopped');
      $('#settings-scheduler').textContent = jobState.charAt(0).toUpperCase() + jobState.slice(1);
      $('#settings-discord').outerHTML = renderStatus(status.notifications.discord_enabled ? 'Enabled' : 'Disabled', status.notifications.discord_enabled ? 'good' : 'unknown');
      $('#settings-telegram').outerHTML = renderStatus(status.notifications.telegram_enabled ? 'Enabled' : 'Disabled', status.notifications.telegram_enabled ? 'good' : 'unknown');
      $('#settings-telegram-chat').outerHTML = renderStatus(status.notifications.telegram_chat_configured ? 'Configured' : 'Not configured', status.notifications.telegram_chat_configured ? 'good' : 'unknown');
      $('#settings-support-sales-telegram').innerHTML = renderStatus(status.notifications.support_sales_telegram_enabled ? 'Enabled' : 'Disabled', status.notifications.support_sales_telegram_enabled ? 'good' : 'unknown');
      $('#settings-support-sales-telegram-chat').innerHTML = renderStatus(status.notifications.support_sales_telegram_configured ? 'Configured' : 'Not configured', status.notifications.support_sales_telegram_configured ? 'good' : 'unknown');
      $('#settings-providers').innerHTML = providers.providers.map(slug => `<div class="provider-item"><strong>${escapeHtml(providerNames[slug] || slug)}</strong>${renderStatus('Enabled', 'good')}</div>`).join('');
    } catch (error) { $('#settings-providers').textContent = error.message; }

    const button = $('#telegram-test-button');
    const statusText = $('#telegram-test-status');
    if (button && statusText) button.addEventListener('click', async () => {
      button.disabled = true;
      button.textContent = 'Sending test…';
      statusText.textContent = 'Sending test message…';
      try {
        const result = await api('/api/v1/notifications/test/telegram', { method: 'POST' });
        statusText.textContent = result.message || 'Telegram test message sent.';
        toast('Telegram test sent successfully.');
      } catch (error) {
        statusText.textContent = `Telegram test failed: ${error.message}`;
        toast(`Telegram test failed: ${error.message}`);
      } finally {
        button.disabled = false;
        button.textContent = 'Test Telegram Notifications';
      }
    });

    const supportSalesButton = $('#support-sales-telegram-test-button');
    const supportSalesStatus = $('#support-sales-telegram-test-status');
    if (supportSalesButton && supportSalesStatus) supportSalesButton.addEventListener('click', async () => {
      supportSalesButton.disabled = true;
      supportSalesButton.textContent = 'Sending test…';
      supportSalesStatus.textContent = 'Sending test message to Support-Sales…';
      try {
        const result = await api('/api/v1/notifications/test/support-sales', { method: 'POST' });
        supportSalesStatus.textContent = result.message || 'Support-Sales Telegram test message sent.';
        toast('Support-Sales Telegram test sent successfully.');
      } catch (error) {
        supportSalesStatus.textContent = `Support-Sales Telegram test failed: ${error.message}`;
        toast(`Support-Sales Telegram test failed: ${error.message}`);
      } finally {
        supportSalesButton.disabled = false;
        supportSalesButton.textContent = 'Test Support-Sales Telegram';
      }
    });
  }

  async function loadUsers() {
    const body = $('#users-table-body');
    if (!body) return;
    try {
      const users = await api('/api/v1/users');
      body.innerHTML = users.length ? users.map(user => `<tr>
        <td><strong>${escapeHtml(user.username)}</strong></td>
        <td>${escapeHtml(user.role === 'admin' ? 'Admin' : 'User')}</td>
        <td>${renderStatus(user.is_active ? 'Active' : 'Disabled', user.is_active ? 'good' : 'unknown')}</td>
        <td title="${escapeHtml(dateText(user.created_at))}">${escapeHtml(user.created_at ? relativeTime(user.created_at) : '—')}</td>
        <td title="${escapeHtml(dateText(user.last_login_at))}">${escapeHtml(user.last_login_at ? relativeTime(user.last_login_at) : 'Never')}</td>
        <td><div class="user-actions">
          <button type="button" class="button button-quiet" data-user-action="edit" data-user-id="${Number(user.id)}">Edit</button>
          <button type="button" class="button button-quiet" data-user-action="toggle" data-user-id="${Number(user.id)}" data-active="${user.is_active ? 'true' : 'false'}">${user.is_active ? 'Disable' : 'Enable'}</button>
          <button type="button" class="button button-quiet" data-user-action="reset" data-user-id="${Number(user.id)}">Reset password</button>
          <button type="button" class="button button-quiet user-delete" data-user-action="delete" data-user-id="${Number(user.id)}">Delete</button>
        </div></td></tr>`).join('') : '<tr><td colspan="6" class="empty-state">No users are configured.</td></tr>';
      body.querySelectorAll('[data-user-action]').forEach(button => button.addEventListener('click', () => handleUserAction(button, users)));
    } catch (error) {
      body.innerHTML = `<tr><td colspan="6" class="empty-state">${escapeHtml(error.message)}</td></tr>`;
    }
  }

  function initializeUserManagement() {
    const dialog = $('#user-dialog');
    const form = $('#user-form');
    const error = $('#user-form-error');
    if (!dialog || !form) return;
    const passwords = $('#new-user-passwords');
    const passwordInputs = [$('#managed-password'), $('#managed-confirm-password')];
    const showError = (box, message) => { box.textContent = message; box.hidden = !message; };
    const close = () => dialog.close();
    $('#add-user').addEventListener('click', () => {
      form.reset();
      $('#edit-user-id').value = '';
      $('#managed-active').checked = true;
      $('#user-dialog-title').textContent = 'Add user';
      $('#user-dialog-help').textContent = 'Create a WatchTower account.';
      $('#user-form-submit').textContent = 'Create user';
      $('#managed-username').disabled = false;
      passwords.hidden = false;
      passwordInputs.forEach(input => { input.required = true; input.disabled = false; });
      showError(error, '');
      dialog.showModal();
    });
    $('#user-dialog-close').addEventListener('click', close);
    $('#user-dialog-cancel').addEventListener('click', close);
    form.addEventListener('submit', async event => {
      event.preventDefault();
      showError(error, '');
      const userId = $('#edit-user-id').value;
      const username = $('#managed-username').value.trim();
      const role = $('#managed-role').value;
      const is_active = $('#managed-active').checked;
      try {
        if (userId) {
          await api(`/api/v1/users/${userId}`, { method: 'PATCH', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, role, is_active }) });
        } else {
          const password = $('#managed-password').value;
          const confirm_password = $('#managed-confirm-password').value;
          if (password !== confirm_password) throw new Error('Password confirmation does not match.');
          await api('/api/v1/users', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ username, password, confirm_password, role, is_active }) });
        }
        close();
        form.reset();
        toast(userId ? 'User updated.' : 'User created.');
        await loadUsers();
      } catch (requestError) { showError(error, requestError.message); }
    });

    const resetDialog = $('#reset-password-dialog');
    const resetForm = $('#reset-password-form');
    const resetError = $('#reset-password-error');
    const closeReset = () => resetDialog.close();
    $('#reset-dialog-close').addEventListener('click', closeReset);
    $('#reset-dialog-cancel').addEventListener('click', closeReset);
    resetForm.addEventListener('submit', async event => {
      event.preventDefault();
      showError(resetError, '');
      const id = $('#reset-user-id').value;
      const new_password = $('#reset-new-password').value;
      const confirm_password = $('#reset-confirm-password').value;
      if (new_password !== confirm_password) { showError(resetError, 'Password confirmation does not match.'); return; }
      try {
        await api(`/api/v1/users/${id}/reset-password`, { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ new_password, confirm_password }) });
        resetForm.reset();
        closeReset();
        toast('Password reset successfully.');
      } catch (requestError) { showError(resetError, requestError.message); }
    });
  }

  async function handleUserAction(button, users) {
    const id = button.dataset.userId;
    const user = users.find(item => String(item.id) === String(id));
    if (!user) return;
    const dialog = $('#user-dialog');
    if (button.dataset.userAction === 'edit') {
      const form = $('#user-form');
      form.reset();
      $('#edit-user-id').value = id;
      $('#managed-username').value = user.username;
      $('#managed-username').disabled = false;
      $('#managed-role').value = user.role;
      $('#managed-active').checked = user.is_active;
      $('#new-user-passwords').hidden = true;
      [$('#managed-password'), $('#managed-confirm-password')].forEach(input => { input.required = false; input.disabled = true; });
      $('#user-dialog-title').textContent = `Edit ${user.username}`;
      $('#user-dialog-help').textContent = 'Update the username, role, or account status.';
      $('#user-form-submit').textContent = 'Save changes';
      $('#user-form-error').hidden = true;
      dialog.showModal();
      return;
    }
    if (button.dataset.userAction === 'toggle') {
      const enable = button.dataset.active !== 'true';
      try {
        await api(`/api/v1/users/${id}/${enable ? 'enable' : 'disable'}`, { method: 'POST' });
        toast(enable ? 'User enabled.' : 'User disabled.');
        await loadUsers();
      } catch (error) { toast(error.message); }
      return;
    }
    if (button.dataset.userAction === 'reset') {
      $('#reset-password-form').reset();
      $('#reset-user-id').value = id;
      $('#reset-password-title').textContent = `Reset ${user.username}'s password`;
      $('#reset-password-error').hidden = true;
      $('#reset-password-dialog').showModal();
      return;
    }
    if (button.dataset.userAction === 'delete' && window.confirm(`Delete the account “${user.username}”? This cannot be undone.`)) {
      try {
        await api(`/api/v1/users/${id}`, { method: 'DELETE' });
        toast('User deleted.');
        await loadUsers();
      } catch (error) { toast(error.message); }
    }
  }

  const notificationIcons = { openclaw: '🤖', human_agent: '👤', watchtower: '🗼', system: '⚙' };

  function notificationSourceLabel(source) {
    return { openclaw: 'OpenClaw', human_agent: 'Human Agent', watchtower: 'WatchTower', system: 'System' }[source] || typeLabel(source);
  }

  function notificationSeverityLabel(severity) {
    return (severity || 'info').charAt(0).toUpperCase() + (severity || 'info').slice(1);
  }

  function notificationApprovalLabel(status) {
    return ({ pending: 'Pending approval', approved: 'Approved', denied: 'Denied', expired: 'Expired', not_required: 'No approval required' }[status] || 'Unknown');
  }

  function renderMarkdownInline(value) {
    const source = String(value ?? '');
    const pattern = /\[([^\]]+)\]\(([^\s)]+)(?:\s+"([^"]*)")?\)|(\*\*|__)(.+?)\4|(?<!\*)\*([^*\n]+)\*(?!\*)|(?<!_)_([^_\n]+)_(?!_)/g;
    let output = '';
    let cursor = 0;
    let match;
    while ((match = pattern.exec(source))) {
      output += escapeHtml(source.slice(cursor, match.index));
      if (match[1] !== undefined) {
        const href = match[2];
        const safeHref = /^(https?:|mailto:)/i.test(href) || /^(\/|\#|\?)/.test(href) && !/^\/\//.test(href);
        const label = renderMarkdownInline(match[1]);
        output += safeHref
          ? `<a href="${escapeHtml(href)}"${match[3] ? ` title="${escapeHtml(match[3])}"` : ''} target="_blank" rel="noopener noreferrer">${label}</a>`
          : escapeHtml(match[0]);
      } else if (match[4]) {
        output += `<strong>${renderMarkdownInline(match[5])}</strong>`;
      } else if (match[6] !== undefined) {
        output += `<em>${renderMarkdownInline(match[6])}</em>`;
      } else {
        output += `<em>${renderMarkdownInline(match[7])}</em>`;
      }
      cursor = pattern.lastIndex;
    }
    return output + escapeHtml(source.slice(cursor));
  }

  function splitMarkdownTableRow(line) {
    let row = line.trim();
    if (row.startsWith('|')) row = row.slice(1);
    if (row.endsWith('|')) row = row.slice(0, -1);
    return row.split(/(?<!\\)\|/).map(cell => cell.replace(/\\\|/g, '|').trim());
  }

  function isMarkdownTableSeparator(line) {
    const cells = splitMarkdownTableRow(line);
    return cells.length > 0 && cells.every(cell => /^:?-{3,}:?$/.test(cell));
  }

  function renderMarkdownTable(lines) {
    const headers = splitMarkdownTableRow(lines[0]);
    const alignments = splitMarkdownTableRow(lines[1]).map(cell => cell.startsWith(':') && cell.endsWith(':') ? 'center' : cell.endsWith(':') ? 'right' : cell.startsWith(':') ? 'left' : '');
    const rows = lines.slice(2).map(splitMarkdownTableRow);
    const cell = (value, index, tag) => `<${tag}${alignments[index] ? ` style="text-align:${alignments[index]}"` : ''}>${renderMarkdownInline(value || '')}</${tag}>`;
    return `<div class="notification-table-wrap" role="region" aria-label="Notification table" tabindex="0"><table class="notification-table"><thead><tr>${headers.map((value, index) => cell(value, index, 'th')).join('')}</tr></thead><tbody>${rows.map(row => `<tr>${headers.map((_, index) => cell(row[index], index, 'td')).join('')}</tr>`).join('')}</tbody></table></div>`;
  }

  function renderMarkdown(value) {
    const lines = String(value ?? '').replace(/\r\n?/g, '\n').split('\n');
    const blocks = [];
    let index = 0;
    while (index < lines.length) {
      if (!lines[index].trim()) { index += 1; continue; }
      if (index + 1 < lines.length && lines[index].includes('|') && isMarkdownTableSeparator(lines[index + 1])) {
        const table = [lines[index], lines[index + 1]];
        index += 2;
        while (index < lines.length && lines[index].trim() && lines[index].includes('|')) table.push(lines[index++]);
        blocks.push(renderMarkdownTable(table));
        continue;
      }
      const heading = lines[index].match(/^\s{0,3}(#{1,6})\s+(.+?)\s*#*\s*$/);
      if (heading) {
        const level = heading[1].length;
        blocks.push(`<h${level}>${renderMarkdownInline(heading[2])}</h${level}>`);
        index += 1;
        continue;
      }
      const listMatch = lines[index].match(/^\s{0,3}([-+*]|\d+[.)])\s+(.+)$/);
      if (listMatch) {
        const ordered = /^\d/.test(listMatch[1]);
        const tag = ordered ? 'ol' : 'ul';
        const items = [];
        while (index < lines.length) {
          const item = lines[index].match(/^\s{0,3}([-+*]|\d+[.)])\s+(.+)$/);
          if (!item || /^\d/.test(item[1]) !== ordered) break;
          items.push(`<li>${renderMarkdownInline(item[2])}</li>`);
          index += 1;
        }
        blocks.push(`<${tag}>${items.join('')}</${tag}>`);
        continue;
      }
      const paragraph = [];
      while (index < lines.length && lines[index].trim()) paragraph.push(lines[index++]);
      blocks.push(`<p>${paragraph.map(renderMarkdownInline).join('<br>')}</p>`);
    }
    return blocks.join('');
  }

  function renderNotification(notification) {
    const metadata = notification.metadata && typeof notification.metadata === 'object' ? notification.metadata : {};
    const task = notification.task_spec && typeof notification.task_spec === 'object'
      ? notification.task_spec
      : notification.task_specification && typeof notification.task_specification === 'object'
        ? notification.task_specification : null;
    const taskBound = Boolean(task && task.task_type === 'public_website_inspection');
    const chips = [];
    if (!taskBound && notification.task_name) chips.push(`<span class="notification-chip">Task: ${escapeHtml(notification.task_name)}</span>`);
    if (!taskBound && notification.task_id) chips.push(`<span class="notification-chip">Task ID: ${escapeHtml(notification.task_id)}</span>`);
    chips.push(`<span class="notification-chip">${escapeHtml(notificationSeverityLabel(notification.severity))}</span>`);
    chips.push(`<span class="notification-chip">${escapeHtml(notification.status || 'new')}</span>`);
    if (notification.requires_approval) chips.push(`<span class="notification-chip notification-approval-${escapeHtml(notification.approval_status || 'pending')}">${escapeHtml(notificationApprovalLabel(notification.approval_status))}</span>`);
    if (metadata.test === true) chips.push('<span class="notification-chip">Test</span>');

    const approvalActions = notification.requires_approval && notification.approval_status === 'pending'
      ? `<div class="notification-approval-actions">
          <button class="button button-primary notification-approve" type="button" data-notification-id="${notification.id}">✓ Approve</button>
          <button class="button button-danger notification-deny" type="button" data-notification-id="${notification.id}">✕ Deny</button>
        </div>`
      : notification.requires_approval
        ? `<div class="notification-decision"><strong>${escapeHtml(notificationApprovalLabel(notification.approval_status))}</strong>${notification.approved_by ? ` by ${escapeHtml(notification.approved_by)}` : ''}${notification.denial_reason ? ` — ${escapeHtml(notification.denial_reason)}` : ''}</div>`
        : '';
    const taskDetails = taskBound ? `<section class="notification-task-details" aria-label="Website inspection target">
      <span class="notification-target-label">Target website</span>
      <a class="notification-target-link" href="${escapeHtml(task.url)}" target="_blank" rel="noopener noreferrer">${escapeHtml(task.url)}</a>
    </section>` : '';

    return `<article class="notification-card severity-${escapeHtml(notification.severity || 'info')} ${notification.requires_approval && notification.approval_status === 'pending' ? 'requires-approval' : ''}">
      <div class="notification-card-header">
        <div><div class="notification-source"><span class="notification-icon" aria-hidden="true">${notificationIcons[notification.source] || '•'}</span>${escapeHtml(notificationSourceLabel(notification.source))}</div>
        <h2>${metadata.test === true ? '🧪 ' : ''}${escapeHtml(notification.title)}</h2></div>
        <span class="muted small" title="${escapeHtml(dateText(notification.created_at))}">${escapeHtml(relativeTime(notification.created_at))}</span>
      </div>
      <div class="notification-message">${renderMarkdown(notification.message)}</div>
      ${taskDetails}
      ${chips.length ? `<div class="notification-meta">${chips.join('')}</div>` : ''}
      ${approvalActions}
      <div class="notification-card-footer"><span>${escapeHtml(dateText(notification.created_at))}</span>${notification.external_url ? `<a href="${escapeHtml(notification.external_url)}" target="_blank" rel="noopener noreferrer">View report ↗</a>` : ''}</div>
    </article>`;
  }

  async function initializeNotificationCenter() {
    const feed = $('#notification-feed');
    if (!feed) return;
    const source = $('#notification-source');
    const severity = $('#notification-severity');
    const status = $('#notification-status');
    const approval = $('#notification-approval');
    const refreshButton = $('#notification-refresh');
    const refreshStatus = $('#notification-refresh-status');
    const pagination = $('#notification-pagination');
    const unreadCount = $('#notification-unread-count');
    const testButton = $('#send-notification-test');
    const testStatus = $('#notification-test-status');
    let offset = 0;
    const limit = 25;
    let pollTimer;
    let knownNotificationIds = null;
    let notificationAudioContext = null;

    function prepareNotificationSound() {
      try {
        const AudioContextClass = window.AudioContext || window.webkitAudioContext;
        if (!AudioContextClass) return null;
        if (!notificationAudioContext) notificationAudioContext = new AudioContextClass();
        if (notificationAudioContext.state === 'suspended') {
          notificationAudioContext.resume().catch(() => {});
        }
        return notificationAudioContext;
      } catch (_) {
        return null;
      }
    }

    function playNotificationAlert() {
      const ctx = prepareNotificationSound();
      if (!ctx) return;
      const emit = () => {
        try {
          const now = ctx.currentTime;
          const master = ctx.createGain();
          master.gain.setValueAtTime(0.0001, now);
          master.gain.exponentialRampToValueAtTime(0.98, now + 0.015);
          master.gain.exponentialRampToValueAtTime(0.0001, now + 1.85);
          master.connect(ctx.destination);

          // Loud, attention-grabbing triple double-beep alert.
          [0, 0.30, 0.60].forEach((start, index) => {
            const first = ctx.createOscillator();
            const second = ctx.createOscillator();
            first.type = 'square';
            second.type = 'square';
            first.frequency.setValueAtTime(index % 2 ? 920 : 1040, now + start);
            second.frequency.setValueAtTime(index % 2 ? 690 : 780, now + start + 0.12);
            first.connect(master);
            second.connect(master);
            first.start(now + start);
            first.stop(now + start + 0.105);
            second.start(now + start + 0.12);
            second.stop(now + start + 0.225);
          });
          if (navigator.vibrate) navigator.vibrate([220, 90, 220, 90, 360]);
        } catch (_) {
          // The notification remains visible if browser audio is unavailable.
        }
      };
      if (ctx.state === 'running') emit();
      else ctx.resume().then(emit).catch(() => {});
    }

    async function decideNotification(id, decision) {
      const action = decision === 'approved' ? 'approve' : 'deny';
      let body;
      if (decision === 'denied') {
        const reason = window.prompt('Optional reason for denying this task:');
        if (reason === null) return;
        body = JSON.stringify({ reason });
      }
      try {
        await api(`/api/v1/notifications/${id}/${action}`, {
          method: 'POST',
          headers: { 'Content-Type': 'application/json' },
          ...(body ? { body } : {}),
        });
        toast(decision === 'approved' ? 'Task approved.' : 'Task denied.');
        await loadNotifications({ silent: true });
      } catch (error) {
        toast(`Unable to update notification: ${error.message}`);
      }
    }

    async function loadNotifications({ silent = false } = {}) {
      const params = new URLSearchParams({ limit: String(limit), offset: String(offset) });
      if (source?.value) params.set('source', source.value);
      if (severity?.value) params.set('severity', severity.value);
      if (status?.value) params.set('status', status.value);
      if (approval?.value) params.set('approval_status', approval.value);
      if (!silent) feed.innerHTML = '<div class="notification-empty">Loading notifications…</div>';
      try {
        const result = await api(`/api/v1/notifications?${params.toString()}`);
        const items = result.items || [];
        if (unreadCount) unreadCount.textContent = `Unread: ${Number(result.unread_count) || 0}`;
        const currentIds = new Set(items.map(item => Number(item.id)));
        let newItemsCount = 0;
        if (knownNotificationIds === null) {
          knownNotificationIds = currentIds;
        } else if (items.length) {
          const newItems = items.filter(item => !knownNotificationIds.has(Number(item.id)));
          if (newItems.length) {
            playNotificationAlert();
            newItemsCount = newItems.length;
          }
          knownNotificationIds = new Set([...knownNotificationIds, ...currentIds]);
        }
        feed.innerHTML = items.length ? items.map(renderNotification).join('') : '<div class="notification-empty">No notifications match the selected filters.</div>';
        $$('.notification-approve', feed).forEach(button => button.addEventListener('click', () => decideNotification(button.dataset.notificationId, 'approved')));
        $$('.notification-deny', feed).forEach(button => button.addEventListener('click', () => decideNotification(button.dataset.notificationId, 'denied')));
        const total = Number(result.total) || 0;
        const first = total ? offset + 1 : 0;
        const last = Math.min(offset + items.length, total);
        pagination.innerHTML = `<span>${first}–${last} of ${total}</span><div><button class="button button-quiet" id="notification-prev" type="button" ${offset <= 0 ? 'disabled' : ''}>Previous</button><button class="button button-quiet" id="notification-next" type="button" ${offset + items.length >= total ? 'disabled' : ''}>Next</button></div>`;
        $('#notification-prev')?.addEventListener('click', () => { offset = Math.max(0, offset - limit); loadNotifications(); });
        $('#notification-next')?.addEventListener('click', () => { offset += limit; loadNotifications(); });
        if (refreshStatus) refreshStatus.textContent = newItemsCount
          ? `🔊 ${newItemsCount} new notification${newItemsCount === 1 ? '' : 's'}`
          : `Updated ${relativeTime(new Date())}`;
        return true;
      } catch (error) {
        feed.innerHTML = `<div class="notification-empty">Unable to load notifications: ${escapeHtml(error.message)}</div>`;
        return false;
      }
    }

    const filterChanged = () => { offset = 0; loadNotifications(); };
    source?.addEventListener('change', filterChanged);
    severity?.addEventListener('change', filterChanged);
    status?.addEventListener('change', filterChanged);
    approval?.addEventListener('change', filterChanged);
    refreshButton?.addEventListener('click', () => loadNotifications());
    testButton?.addEventListener('click', async () => {
      testButton.disabled = true;
      const label = testButton.querySelectorAll('span')[1];
      if (label) label.textContent = 'Sending…';
      if (testStatus) testStatus.textContent = 'Creating a test notification…';
      try {
        const result = await api('/api/v1/notifications/test', { method: 'POST' });
        offset = 0;
        [source, severity, status, approval].forEach(filter => { if (filter) filter.value = ''; });
        const feedUpdated = await loadNotifications({ silent: true });
        if (testStatus) testStatus.textContent = feedUpdated
          ? `Notification #${result.id} appeared in the feed.`
          : `Notification #${result.id} was created, but the feed could not refresh.`;
        toast(feedUpdated ? 'Test notification added to Notification Center.' : 'Test notification created; feed refresh failed.');
      } catch (error) {
        if (testStatus) testStatus.textContent = `Test notification failed: ${error.message}`;
        toast(`Test notification failed: ${error.message}`);
      } finally {
        testButton.disabled = false;
        if (label) label.textContent = 'Send Test Notification';
      }
    });
    // Prepare audio silently. Browsers may suspend it until the user has
    // interacted with the site; interaction only unlocks the mandatory alert
    // channel and there is intentionally no mute/disable control.
    prepareNotificationSound();
    ['pointerdown', 'keydown', 'touchstart'].forEach(eventName => {
      document.addEventListener(eventName, prepareNotificationSound, { passive: true });
    });
    if (testButton) testButton.disabled = true;
    await loadNotifications();
    if (testButton) testButton.disabled = false;
    pollTimer = window.setInterval(() => loadNotifications({ silent: true }), 5000);
    window.addEventListener('beforeunload', () => window.clearInterval(pollTimer), { once: true });
  }

  async function initializeAccount() {
    try {
      const user = await api('/api/v1/account');
      $('#account-username').textContent = user.username;
      $('#account-role').textContent = user.role === 'admin' ? 'Admin' : 'User';
      $('#account-status').textContent = user.is_active ? 'Active' : 'Disabled';
      $('#account-created').textContent = user.created_at ? dateText(user.created_at) : 'Managed by server configuration';
      $('#account-last-login').textContent = user.last_login_at ? dateText(user.last_login_at) : 'Not recorded';
    } catch (error) { toast(error.message); }
    const form = $('#account-password-form');
    form.addEventListener('submit', async event => {
      event.preventDefault();
      const box = $('#account-password-error');
      box.hidden = true;
      const current_password = $('#current-password').value;
      const new_password = $('#account-new-password').value;
      const confirm_password = $('#account-confirm-password').value;
      if (new_password !== confirm_password) { box.textContent = 'Password confirmation does not match.'; box.hidden = false; return; }
      try {
        await api('/api/v1/account/change-password', { method: 'POST', headers: { 'Content-Type': 'application/json' }, body: JSON.stringify({ current_password, new_password, confirm_password }) });
        form.reset();
        toast('Password changed successfully.');
      } catch (error) { box.textContent = error.message; box.hidden = false; }
    });
  }

  async function initializeTasks() {
    const list = $('#task-list'); if (!list) return;
    let view = 'my'; let board = false; let people = []; let rows = []; let offset = 0; const pageSize = 25; let total = 0;
    const dialog = $('#task-dialog');
    const message = text => { $('#task-message').textContent = text || ''; };
    const selected = select => Array.from(select.selectedOptions).map(option => Number(option.value));
    const esc = escapeHtml;
    const statusName = value => ({todo:'To Do',in_progress:'In Progress',on_hold:'On Hold',completed:'Completed',cancelled:'Cancelled'})[value] || value;
    const isOverdue = task => task.due_at && new Date(task.due_at) < new Date() && !['completed','cancelled'].includes(task.status);
    async function load() {
      list.innerHTML = '<div class="loading-state">Loading tasks…</div>';
      try {
        const params = new URLSearchParams({view, limit:String(pageSize), offset:String(offset)});
        const [sort,direction]=$('#task-sort').value.split(':');params.set('sort',sort);params.set('direction',direction);
        if ($('#task-search').value.trim()) params.set('q', $('#task-search').value.trim());
        if ($('#task-status-filter').value) params.set('status', $('#task-status-filter').value);
        if ($('#task-assignee-filter').value) params.set('assignee_id', $('#task-assignee-filter').value);
        if ($('#task-creator-filter').value) params.set('creator_id', $('#task-creator-filter').value);
        if ($('#task-priority-filter').value) params.set('priority', $('#task-priority-filter').value);
        if ($('#task-due-filter').value) params.set('due', $('#task-due-filter').value);
        const result = await api(`/api/v1/tasks?${params}`); rows = result.items; total = result.total;
        const stats = await api('/api/v1/tasks/summary');
        const done = stats.completed;
        $('#task-stats').innerHTML = `<article><strong>${stats.active}</strong><span>Active tasks</span></article><article><strong>${stats.my_pending}</strong><span>My pending</span></article><article><strong>${stats.in_progress}</strong><span>In progress</span></article><article><strong>${stats.overdue}</strong><span>Overdue</span></article><article><strong>${done}</strong><span>Completed</span></article><div class="task-progress"><span>${done} of ${stats.total} complete</span><progress max="${Math.max(stats.total,1)}" value="${done}"></progress></div>`;
        if (!rows.length) { list.innerHTML = '<div class="empty-state">No tasks here yet. Create a task to get started.</div>'; $('#task-pagination').innerHTML=''; return; }
        if (board) renderBoard(); else renderList();
        $('#task-pagination').innerHTML=`<span>Showing ${offset+1}–${Math.min(offset+rows.length,total)} of ${total}</span><div><button class="button button-secondary" id="task-prev" ${offset===0?'disabled':''}>Previous</button><button class="button button-secondary" id="task-next" ${offset+pageSize>=total?'disabled':''}>Next</button></div>`;
        $('#task-prev').addEventListener('click',()=>{offset=Math.max(0,offset-pageSize);load();});$('#task-next').addEventListener('click',()=>{offset+=pageSize;load();});
      } catch (error) { list.innerHTML = `<div class="empty-state">Could not load tasks: ${esc(error.message)}</div>`; }
    }
    function taskCard(task) {
      const late = isOverdue(task);
      return `<article class="task-card ${late?'task-overdue':''}" data-id="${task.id}" draggable="${board}"><button class="task-open" data-open="${task.id}"><span class="task-priority priority-${esc(task.priority)}"></span><strong>${esc(task.title)}</strong></button><span class="status-badge">${esc(statusName(task.status))}</span><div class="task-assignees">${task.assignees.map(a=>`<span class="avatar" title="${esc(a.username)}">${esc(a.username.slice(0,1).toUpperCase())}</span>`).join('')||'<span class="muted">Unassigned</span>'}</div><span class="task-deadline ${late?'late':''}">${late?'Overdue · ':''}${dateText(task.due_at)}</span><span class="muted small">by ${esc(task.creator?.username||'Unknown')}</span><select class="quick-status" data-status="${task.id}" aria-label="Change status">${['todo','in_progress','on_hold','completed','cancelled'].map(s=>`<option value="${s}" ${task.status===s?'selected':''}>${esc(statusName(s))}</option>`).join('')}</select></article>`;
    }
    function bindCards() {
      $$('[data-open]', list).forEach(button=>button.addEventListener('click',()=>openTask(Number(button.dataset.open))));
      $$('.quick-status', list).forEach(select=>select.addEventListener('change',async()=>{try{await api(`/api/v1/tasks/${select.dataset.status}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:select.value})});await load();}catch(e){toast(e.message);}}));
      if(board) $$('.task-card',list).forEach(card=>{card.addEventListener('dragstart',e=>e.dataTransfer.setData('text/plain',card.dataset.id));});
      if(board) $$('.task-column',list).forEach(column=>{column.addEventListener('dragover',e=>e.preventDefault());column.addEventListener('drop',async e=>{e.preventDefault();const id=e.dataTransfer.getData('text/plain');try{await api(`/api/v1/tasks/${id}`,{method:'PATCH',headers:{'Content-Type':'application/json'},body:JSON.stringify({status:column.dataset.status})});await load();}catch(err){toast(err.message);}});});
    }
    function renderList(){list.className='task-list';const header='<div class="task-table-head"><span>Task</span><span>Status</span><span>Assignees</span><span>Due date</span><span>Creator</span><span></span></div>';if(view==='my'){const overdue=rows.filter(isOverdue),completed=rows.filter(t=>t.status==='completed'),upcoming=rows.filter(t=>!isOverdue(t)&&t.status!=='completed');list.innerHTML=header+[['Overdue',overdue],['Upcoming',upcoming],['Completed',completed]].map(([label,items])=>`<h2 class="task-group-heading">${label}<span>${items.length}</span></h2>${items.map(taskCard).join('')||`<p class="muted small task-group-empty">No ${label.toLowerCase()} tasks.</p>`}`).join('');}else list.innerHTML=header+rows.map(taskCard).join('');bindCards();}
    function renderBoard(){list.className='task-board';list.innerHTML=['todo','in_progress','on_hold','completed','cancelled'].map(s=>`<section class="task-column" data-status="${s}"><h3>${esc(statusName(s))}<span>${rows.filter(t=>t.status===s).length}</span></h3>${rows.filter(t=>t.status===s).map(taskCard).join('')}</section>`).join('');bindCards();}
    async function openTask(id=null) {
      $('#task-form').reset(); $('#task-id').value=id||''; $('#task-detail-extra').innerHTML='';
      const edit = id ? await api(`/api/v1/tasks/${id}`) : null;
      dialog.dataset.canEdit=edit?String(edit.can_edit):'true';
      $('#task-dialog-title').textContent=edit?'Task details':'Create task';
      for(const input of ['task-title','task-description','task-priority','task-due']) $('#'+input).disabled=Boolean(edit && !edit.can_edit);
      $('#task-state').disabled=Boolean(edit && !edit.can_edit && !edit.assignees.some(a=>a.id===Number(document.body.dataset.userId)));
      if(edit){$('#task-title').value=edit.title;$('#task-description').value=edit.description;$('#task-priority').value=edit.priority;$('#task-state').value=edit.status;$('#task-due').value=edit.due_at?new Date(edit.due_at).toISOString().slice(0,16):'';for(const o of $('#task-assignees').options)o.selected=edit.assignees.some(a=>a.id===Number(o.value));}
      $('#task-assignees').disabled=Boolean(edit && !edit.can_edit); $('#task-delete').hidden=!edit || !edit.can_edit;
      if(edit){$('#task-detail-extra').innerHTML=`<p class="muted small">Created ${dateText(edit.created_at)} · ${edit.completed_at?'Completed '+dateText(edit.completed_at):'Not completed'}</p><h3>Comments</h3><div class="task-comments">${edit.comments.map(c=>`<p><strong>${esc(c.user)}</strong> · ${dateText(c.created_at)}<br>${esc(c.body)}</p>`).join('')||'<p class="muted">No comments yet.</p>'}</div><form id="task-comment-form"><input id="task-comment" maxlength="10000" placeholder="Write a comment…" required><button class="button button-secondary">Comment</button></form><h3>Activity</h3><ul class="task-activity">${edit.activity.map(a=>`<li><strong>${esc(a.user)}</strong> ${esc(a.action)} ${esc(a.detail)} <small>${dateText(a.created_at)}</small></li>`).join('')}</ul>`;$('#task-comment-form').addEventListener('submit',async e=>{e.preventDefault();try{await api(`/api/v1/tasks/${id}/comments`,{method:'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify({body:$('#task-comment').value})});await openTask(id);toast('Comment added.');}catch(err){toast(err.message);}});}
      dialog.showModal();
    }
    try { people=await api('/api/v1/tasks/users'); $('#task-assignees').innerHTML=people.map(p=>`<option value="${p.id}">${esc(p.username)}</option>`).join('');const options=people.map(p=>`<option value="${p.id}">${esc(p.username)}</option>`).join('');$('#task-assignee-filter').insertAdjacentHTML('beforeend',options);$('#task-creator-filter').insertAdjacentHTML('beforeend',options); } catch(e){toast(e.message);}
    for(const tab of $$('.task-tab')){try{const count=await api(`/api/v1/tasks?view=${tab.dataset.view}&limit=1`);tab.innerHTML=`${esc(tab.textContent)} <span class="task-tab-count">${count.total}</span>`;}catch(_){}tab.addEventListener('click',()=>{$$('.task-tab').forEach(t=>t.classList.toggle('active',t===tab));view=tab.dataset.view;offset=0;load();});}
    $('#task-search').addEventListener('input',()=>{offset=0;clearTimeout(window.taskSearchTimer);window.taskSearchTimer=setTimeout(load,250);});['#task-status-filter','#task-assignee-filter','#task-creator-filter','#task-priority-filter','#task-due-filter','#task-sort'].forEach(sel=>$(sel).addEventListener('change',()=>{offset=0;load();}));
    $('#task-layout').addEventListener('click',()=>{board=!board;$('#task-layout').textContent=board?'List View':'Board View';load();});
    $('#task-create').addEventListener('click',()=>openTask()); $('#task-cancel').addEventListener('click',()=>dialog.close());
    $('#task-form').addEventListener('submit',async e=>{e.preventDefault();const id=$('#task-id').value;const full={title:$('#task-title').value,description:$('#task-description').value,assignee_ids:selected($('#task-assignees')),priority:$('#task-priority').value,status:$('#task-state').value,due_at:$('#task-due').value?new Date($('#task-due').value).toISOString():null};const payload=id&&dialog.dataset.canEdit!=='true'?{status:full.status}:full;try{await api(id?`/api/v1/tasks/${id}`:'/api/v1/tasks',{method:id?'PATCH':'POST',headers:{'Content-Type':'application/json'},body:JSON.stringify(payload)});dialog.close();message('Task saved.');await load();}catch(err){toast(err.message);}});
    $('#task-delete').addEventListener('click',async()=>{const id=$('#task-id').value;if(id&&window.confirm('Delete this task and its comments?'))try{await api(`/api/v1/tasks/${id}`,{method:'DELETE'});dialog.close();await load();toast('Task deleted.');}catch(e){toast(e.message);}});
    await load();
  }

  document.addEventListener('DOMContentLoaded', () => {
    initializeSessionExpiration();
    initializeTheme();
    initializeMobileMenu();
    initializeLogin();
    if ($('#os-table-body')) loadDashboard();
    if ($('#os-detail')) loadOsDetail();
    if ($('#release-filters')) initializeReleases();
    if ($('#event-filters')) initializeEvents();
    if ($('#settings-providers')) initializeSettings();
    if ($('#users-table-body')) { initializeUserManagement(); loadUsers(); }
    if ($('#account-password-form')) initializeAccount();
    if ($('#notification-feed')) initializeNotificationCenter();
    if ($('#task-list')) initializeTasks();
  });

  window.addEventListener('load', () => {
    if (window.Chart && $('#release-chart')) renderReleaseChart();
  }, { once: true });
})();
