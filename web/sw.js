self.addEventListener('push', event => {
  let payload = { title: 'TradeBot AI', body: 'Neues Signal', url: '/' };
  try { payload = event.data ? event.data.json() : payload; } catch (_) {}
  event.waitUntil(self.registration.showNotification(payload.title || 'TradeBot AI', {
    body: payload.body || 'Neues Trading-Signal',
    icon: '/icon-192.svg',
    badge: '/icon-192.svg',
    tag: 'tradebot-alert',
    data: { url: payload.url || '/' },
    requireInteraction: false
  }));
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const target = event.notification.data?.url || '/';
  event.waitUntil(clients.matchAll({ type: 'window', includeUncontrolled: true }).then(list => {
    for (const client of list) {
      if ('focus' in client) return client.navigate(target).then(() => client.focus());
    }
    return clients.openWindow(target);
  }));
});
