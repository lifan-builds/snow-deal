/* Minimal first-party measurements. No search text, full referrer, or email. */
(() => {
  const path = location.pathname;
  const privatePage = /^\/(admin|invite|alerts\/remove|api)(\/|$)/.test(path);
  const params = new URLSearchParams(location.search);
  if (privatePage || params.has('admin_key') || navigator.doNotTrack === '1' || navigator.globalPrivacyControl) return;
  const knownSources = new Set(['google', 'bing', 'x', 'portfolio', 'club', 'youtube', 'reddit']);
  let source = 'direct';
  let campaign = '';
  try {
    const incoming = params.get('utm_source');
    const tag = params.get('utm_campaign');
    const knownCampaigns = new Set(['2026_winter', '2026_launch', 'club_pilot']);
    if (incoming) source = knownSources.has(incoming) ? incoming : 'other';
    else if (document.referrer) {
      const host = new URL(document.referrer).hostname;
      if (host === location.hostname) source = sessionStorage.getItem('fp-source') || 'direct';
      else if (host === 'clifan.com') source = 'portfolio';
      else if (host === 'www.google.com' || host === 'google.com') source = 'google';
      else if (host === 'www.bing.com' || host === 'bing.com') source = 'bing';
      else if (['x.com', 't.co', 'twitter.com'].includes(host)) source = 'x';
      else source = 'other';
    }
    campaign = knownCampaigns.has(tag) ? tag : (sessionStorage.getItem('fp-campaign') || '');
    sessionStorage.setItem('fp-source', source);
    sessionStorage.setItem('fp-campaign', campaign);
  } catch (_) { /* Storage disabled: continue without persistent attribution. */ }
  let queue = Promise.resolve();
  window.fpTrack = (event_type, fields = {}) => {
    const metadata = {page: location.pathname, source, campaign};
    const current = new URLSearchParams(location.search);
    for (const name of ['currency', 'size']) if (current.has(name)) metadata[name] = current.get(name);
    // Sequence the first page view before clicks so the short-session cookie exists.
    queue = queue.then(() => fetch('/api/event', {
      method: 'POST', headers: {'Content-Type': 'application/json'},
      credentials: 'same-origin', keepalive: true,
      body: JSON.stringify({...fields, event_type, metadata: JSON.stringify(metadata)}),
    })).catch(() => {});
    return queue;
  };
  window.fpTrack('page_view');
  document.body.addEventListener('htmx:afterSwap', event => {
    if (event.detail.target?.id === 'deal-grid') window.fpTrack('filter');
  });
  document.querySelector('.comparison-filters')?.addEventListener('submit', () => window.fpTrack('filter'));
})();
