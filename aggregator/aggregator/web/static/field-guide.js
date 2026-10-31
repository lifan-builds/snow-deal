/* Progressive enhancement; links and forms remain usable without JavaScript. */
const form = document.getElementById('filters');
function showToast(message) {
  const box = document.getElementById('toast-container');
  if (!box) return;
  const toast = document.createElement('div'); toast.className = 'toast'; toast.textContent = message;
  box.replaceChildren(toast); setTimeout(() => toast.remove(), 3500);
}
function refreshDeals() {
  if (window.htmx) htmx.trigger(form, 'submit'); else form.requestSubmit();
}
function resetAllFilters() {
  if (!form) return;
  for (const el of form.elements) {
    if (el.type === 'checkbox') el.checked = false;
    else if (el.tagName === 'SELECT') el.selectedIndex = 0;
    else if (el.tagName === 'INPUT') el.value = '';
  }
  refreshDeals();
}
if (form) {
  document.body.addEventListener('htmx:configRequest', event => {
    if (!form.contains(event.detail.elt) && !event.detail.elt.closest('.load-more-wrap')) return;
    for (const [key, value] of Object.entries(event.detail.parameters)) {
      if (value === '') delete event.detail.parameters[key];
    }
    if (!event.detail.parameters.currency && (event.detail.parameters.min_price || event.detail.parameters.max_price || ['price_low','price_high'].includes(event.detail.parameters.sort))) {
      form.elements.currency.value = 'USD'; event.detail.parameters.currency = 'USD';
    }
    document.getElementById('request-error').hidden = true;
  });
  document.body.addEventListener('htmx:afterSwap', event => {
    if (event.detail.target.id !== 'deal-grid') return;
    const params = new URLSearchParams();
    for (const [key, value] of new FormData(form)) if (value && value !== '0') params.set(key, value);
    history.replaceState(null, '', '/' + (params.size ? '?' + params.toString() : ''));
    syncPresets();
  });
  for (const name of ['htmx:responseError', 'htmx:sendError']) document.body.addEventListener(name, () => {document.getElementById('request-error').hidden = false;});
  document.querySelectorAll('[data-preset]').forEach(btn => btn.addEventListener('click', () => {
    const settings = JSON.parse(btn.dataset.preset);
    for (const [key, value] of Object.entries(settings)) {
      const input = form.elements[key];
      if (input.type === 'checkbox') input.checked = Boolean(value); else input.value = value;
    }
    refreshDeals();
  }));
  function syncPresets() {
    document.querySelectorAll('[data-preset]').forEach(btn => {
      const active = Object.entries(JSON.parse(btn.dataset.preset)).every(([key,value]) => form.elements[key].type === 'checkbox' ? form.elements[key].checked : form.elements[key].value === value);
      btn.classList.toggle('active', active); btn.setAttribute('aria-pressed', String(active));
    });
  }
  syncPresets();
  const toggle = document.getElementById('view-toggle');
  toggle.addEventListener('click', () => {
    const compact = document.getElementById('deal-grid').classList.toggle('compact-view');
    toggle.setAttribute('aria-pressed', String(compact)); toggle.textContent = compact ? 'Grid view' : 'Compact view';
    try {localStorage.setItem('fp-view', compact ? 'compact' : 'grid');} catch (_) {}
  });
  try {if (localStorage.getItem('fp-view') === 'compact') toggle.click();} catch (_) {}
  if (matchMedia('(max-width:700px)').matches) document.querySelector('.filter-panel').open = false;
}
document.addEventListener('click', async event => {
  const share = event.target.closest('.share-btn');
  if (share) {
    try {
      if (navigator.share) await navigator.share({title:share.dataset.name,url:share.dataset.url});
      else {await navigator.clipboard.writeText(share.dataset.url); showToast('Deal link copied.');}
    } catch (error) {if (error.name !== 'AbortError') showToast('Use the product link to share this find.');}
  }
  const link = event.target.closest('.product-link');
  if (link) {
    const card = link.closest('.deal-card');
    try {navigator.sendBeacon('/api/event', new Blob([JSON.stringify({event_type:'click',deal_url:card.dataset.href,deal_name:card.dataset.name,store:card.dataset.store,category:card.dataset.category})], {type:'application/json'}));} catch (_) {}
  }
});
const waitlist = document.getElementById('waitlist-form');
if (waitlist) waitlist.addEventListener('submit', async event => {
  event.preventDefault(); const button = waitlist.querySelector('button'); const feedback = waitlist.querySelector('.form-feedback');
  button.disabled = true; feedback.textContent = 'Saving your place…';
  try {
    const response = await fetch('/waitlist', {method:'POST', body:new FormData(waitlist)}); const result = await response.json();
    if (!response.ok || !result.ok) throw new Error(result.error || 'Please try again.');
    feedback.textContent = 'You’re on the list. We’ll let you know when a spot opens.'; waitlist.reset();
  } catch (error) {feedback.textContent = error.message || 'Could not connect. Please try again.';}
  finally {button.disabled = false;}
});
