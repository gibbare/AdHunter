const WORKER_URL = 'https://aurora-push.gibbare.workers.dev';

self.addEventListener('push', event => {
  event.waitUntil((async () => {
    let title = '📦 Ny annons', body = 'Öppna för att se annonsen.', tag = 'ad', url = '/';
    try {
      const res = await fetch(WORKER_URL + '/latest-ad');
      if (res.ok) { const d = await res.json(); title=d.title||title; body=d.body||body; tag=d.tag||tag; url=d.url||url; }
    } catch {}
    await self.registration.showNotification(title, { body, tag, renotify: true, data: { url } });
  })());
});

self.addEventListener('notificationclick', event => {
  event.notification.close();
  const url = event.notification.data?.url || '/';
  event.waitUntil(clients.openWindow(url));
});
