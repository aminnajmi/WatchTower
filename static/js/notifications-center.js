(() => {
  const allowed = {
    source: new Set(['openclaw', 'human_agent', 'watchtower', 'system']),
    severity: new Set(['info', 'success', 'warning', 'error', 'critical']),
    status: new Set(['new', 'read', 'reviewed', 'resolved']),
  };
  const labels = { openclaw: 'OpenClaw', human_agent: 'Human Agent', watchtower: 'WatchTower', system: 'System' };
  const icons = { openclaw: '🤖', human_agent: '👤', watchtower: '🧪', system: '⚙' };
  const severityIcons = { info: 'ℹ', success: '✓', warning: '⚠', error: '✕', critical: '!' };
  const pageSize = 20;

  document.addEventListener('DOMContentLoaded', () => {
    const feed = document.querySelector('#notification-feed');
    if (!feed) return;
    const sourceFilter = document.querySelector('#notification-source');
    const severityFilter = document.querySelector('#notification-severity');
    const statusFilter = document.querySelector('#notification-status');
    const previous = document.querySelector('#notification-previous');
    const next = document.querySelector('#notification-next');
    const pageInfo = document.querySelector('#notification-page-info');
    const liveState = document.querySelector('#notification-live-state');
    let offset = 0;
    let total = 0;
    let currentItems = [];
    let newestSeen = '';
    let isInitialLoad = true;

    const element = (tag, className, text) => {
      const node = document.createElement(tag);
      if (className) node.className = className;
      if (text !== undefined) node.textContent = text;
      return node;
    };

    const normalized = (kind, value) => allowed[kind].has(value) ? value : (kind === 'source' ? 'system' : 'info');

    const relativeTime = value => {
      const date = new Date(value);
      const seconds = Math.round((date.getTime() - Date.now()) / 1000);
      const absolute = Math.abs(seconds);
      const [unit, size] = absolute < 60 ? ['second', 1]
        : absolute < 3600 ? ['minute', 60]
          : absolute < 86400 ? ['hour', 3600]
            : ['day', 86400];
      return new Intl.RelativeTimeFormat(undefined, { numeric: 'auto' }).format(Math.round(seconds / size), unit);
    };

    const metadataValue = value => {
      if (value === null || value === undefined) return '—';
      if (typeof value === 'object') return JSON.stringify(value);
      return String(value);
    };

    function renderCard(item) {
      const source = normalized('source', item.source);
      const severity = normalized('severity', item.severity);
      const status = normalized('status', item.status);
      const requiresReview = Boolean(item.requires_review) || (status === 'new' && ['critical', 'error'].includes(severity));
      const card = element('article', `panel notification-card severity-${severity}${requiresReview ? ' requires-review' : ''}`);
      const header = element('div', 'notification-card-header');
      const sourceLabel = element('div', 'notification-source');
      sourceLabel.append(element('span', 'notification-source-icon', icons[source]));
      sourceLabel.append(element('span', '', labels[source]));
      header.append(sourceLabel);
      if (item.metadata && item.metadata.test === true) {
        header.append(element('span', 'notification-badge', '🧪 Test'));
      }
      card.append(header);
      card.append(element('h2', '', String(item.title || 'Notification')));
      card.append(element('p', 'notification-message', String(item.message || '')));

      const badges = element('div', 'notification-badges');
      badges.append(element('span', `notification-badge severity-${severity}`, `${severityIcons[severity]} ${severity}`));
      badges.append(element('span', 'notification-badge', status));
      if (requiresReview) badges.append(element('span', 'notification-badge requires-review', '⚠ Requires review'));
      if (item.task_name) badges.append(element('span', 'notification-badge', `Task · ${String(item.task_name)}`));
      card.append(badges);

      const metadata = item.metadata && typeof item.metadata === 'object' && !Array.isArray(item.metadata) ? item.metadata : {};
      const entries = Object.entries(metadata).filter(([key]) => key !== 'test' && key !== 'source');
      if (entries.length) {
        const list = element('dl', 'notification-meta');
        for (const [key, value] of entries) {
          const row = element('div');
          const term = element('dt', '', key.replace(/[_-]+/g, ' '));
          const detail = element('dd', '', metadataValue(value));
          row.append(term, detail);
          list.append(row);
        }
        card.append(list);
      }

      const footer = element('div', 'notification-card-footer');
      const time = element('time', '', relativeTime(item.created_at));
      time.dateTime = item.created_at;
      time.title = new Date(item.created_at).toLocaleString();
      footer.append(time);
      if (item.external_url) {
        try {
          const url = new URL(item.external_url, window.location.origin);
          if (['http:', 'https:'].includes(url.protocol) && !url.username && !url.password) {
            const link = element('a', 'notification-external-link', 'View full report ↗');
            link.href = url.href;
            link.target = '_blank';
            link.rel = 'noopener noreferrer';
            footer.append(link);
          }
        } catch (_error) { /* Invalid links are omitted from the public feed. */ }
      }
      card.append(footer);
      return card;
    }

    function updatePagination() {
      pageInfo.textContent = total ? `Showing ${offset + 1}–${Math.min(offset + currentItems.length, total)} of ${total}` : 'No notifications';
      previous.disabled = offset <= 0;
      next.disabled = offset + pageSize >= total;
    }

    function render() {
      feed.replaceChildren();
      if (!currentItems.length) {
        feed.append(element('article', 'panel notification-empty', 'No notifications match these filters.'));
      } else {
        for (const item of currentItems) feed.append(renderCard(item));
      }
      feed.setAttribute('aria-busy', 'false');
      updatePagination();
    }

    function queryUrl({ polling = false } = {}) {
      const query = new URLSearchParams({ limit: String(pageSize), offset: String(polling ? 0 : offset) });
      if (sourceFilter.value) query.set('source', sourceFilter.value);
      if (severityFilter.value) query.set('severity', severityFilter.value);
      if (statusFilter.value) query.set('status', statusFilter.value);
      if (polling && newestSeen) query.set('since', newestSeen);
      return `/api/v1/notifications?${query.toString()}`;
    }

    async function requestItems(options) {
      const response = await fetch(queryUrl(options), { headers: { Accept: 'application/json' }, cache: 'no-store' });
      if (!response.ok) throw new Error('Unable to load notifications.');
      return response.json();
    }

    async function loadPage() {
      feed.setAttribute('aria-busy', 'true');
      try {
        const result = await requestItems();
        currentItems = result.items || [];
        total = Number(result.total) || 0;
        if (!newestSeen && currentItems.length) newestSeen = currentItems[0].created_at;
        isInitialLoad = false;
        render();
        liveState.textContent = 'Refreshing every 12 seconds';
      } catch (_error) {
        feed.replaceChildren(element('article', 'panel notification-empty', 'Notifications are temporarily unavailable.'));
        feed.setAttribute('aria-busy', 'false');
        liveState.textContent = 'Refresh unavailable';
      }
    }

    async function poll() {
      if (isInitialLoad) return;
      try {
        const result = await requestItems({ polling: true });
        const incoming = result.items || [];
        if (!incoming.length) return;
        for (const item of incoming) {
          if (!newestSeen || new Date(item.created_at) > new Date(newestSeen)) newestSeen = item.created_at;
        }
        if (offset === 0) {
          const known = new Set(currentItems.map(item => item.id));
          const added = incoming.filter(item => !known.has(item.id));
          if (added.length) {
            currentItems = [...added, ...currentItems].slice(0, pageSize);
            total += added.length;
            render();
            liveState.textContent = `${added.length} new notification${added.length === 1 ? '' : 's'} received`;
            window.setTimeout(() => { liveState.textContent = 'Refreshing every 12 seconds'; }, 4500);
          }
        } else {
          liveState.textContent = 'New notifications are available on the first page';
          window.setTimeout(() => { liveState.textContent = 'Refreshing every 12 seconds'; }, 4500);
        }
      } catch (_error) {
        liveState.textContent = 'Refresh unavailable';
      }
    }

    for (const filter of [sourceFilter, severityFilter, statusFilter]) {
      filter.addEventListener('change', () => { offset = 0; loadPage(); });
    }
    previous.addEventListener('click', () => { offset = Math.max(0, offset - pageSize); loadPage(); });
    next.addEventListener('click', () => { if (offset + pageSize < total) { offset += pageSize; loadPage(); } });

    loadPage();
    window.setInterval(poll, 12000);
    window.setInterval(() => {
      feed.querySelectorAll('time[datetime]').forEach(time => {
        time.textContent = relativeTime(time.dateTime);
        time.title = new Date(time.dateTime).toLocaleString();
      });
    }, 30000);
  });
})();
