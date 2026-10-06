(() => {
  document.addEventListener('DOMContentLoaded', () => {
    const button = document.querySelector('#send-notification-test');
    const status = document.querySelector('#notification-test-status');
    if (!button || !status) return;

    button.addEventListener('click', async () => {
      if (button.disabled) return;
      button.disabled = true;
      const original = '♧ Send Test Notification';
      button.textContent = 'Sending…';
      status.textContent = 'Sending a test notification…';
      try {
        const response = await fetch('/api/v1/notifications/test', {
          method: 'POST',
          credentials: 'same-origin',
          headers: { Accept: 'application/json' },
        });
        if (!response.ok) throw new Error('Test notification could not be sent.');
        status.textContent = '✅ Test notification sent. View it in the Notification Center.';
      } catch (_error) {
        status.textContent = '❌ Failed to send test notification.';
      } finally {
        button.disabled = false;
        button.textContent = original || '♧ Send Test Notification';
      }
    });
  });
})();
