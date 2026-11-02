/* Progressive enhancement; links and forms remain usable without JavaScript. */
const form = document.getElementById("filters");
function showToast(message) {
  const box = document.getElementById("toast-container");
  if (!box) return;
  const toast = document.createElement("div");
  toast.className = "toast";
  toast.textContent = message;
  box.replaceChildren(toast);
  setTimeout(() => toast.remove(), 3500);
}
function refreshDeals() {
  if (!form.reportValidity()) return;
  if (window.htmx) htmx.trigger(form, "submit");
  else form.requestSubmit();
}
function resetAllFilters() {
  if (!form) return;
  for (const el of form.elements) {
    if (el.type === "checkbox") el.checked = false;
    else if (el.tagName === "SELECT") el.selectedIndex = 0;
    else if (el.tagName === "INPUT") el.value = "";
  }
  for (const input of form.querySelectorAll('input')) input.setCustomValidity('');
  refreshDeals();
}
document.querySelectorAll('.site-header nav a').forEach(link => {
  const path = new URL(link.href).pathname;
  if (path === location.pathname) link.setAttribute('aria-current', 'page');
  else if ((path === '/products' && /^\/(products|brands)\//.test(location.pathname)) ||
           (path === '/' && location.pathname.startsWith('/gear/')))
    link.setAttribute('aria-current', 'location');
});
document.addEventListener('click', event => {
  if (form && event.target.closest('[data-reset-filters]')) {
    event.preventDefault();
    resetAllFilters();
  }
});
if (form) {
  const clothing = form.elements.include_clothing;
  const category = form.elements.category;
  form.addEventListener('change', event => {
    if (event.target === category && category.selectedOptions[0]?.dataset.clothing)
      clothing.checked = true;
    if (event.target === clothing && !clothing.checked && category.selectedOptions[0]?.dataset.clothing)
      category.value = '';
  }, true);
  function validateRanges() {
    for (const [min, max] of [['min_price', 'max_price'], ['size_min', 'size_max']]) {
      const lower = form.elements[min], upper = form.elements[max];
      const invalid = lower.value && upper.value && Number(upper.value) > 0 && Number(lower.value) > Number(upper.value);
      upper.setCustomValidity(invalid ? 'The maximum must be at least the minimum.' : '');
    }
  }
  form.addEventListener('input', validateRanges, true);
  form.addEventListener('change', validateRanges, true);
  form.addEventListener('submit', validateRanges, true);
  document.body.addEventListener('htmx:beforeRequest', event => {
    if (event.detail.target?.id === 'deal-grid' || event.detail.elt.closest('.load-more-wrap'))
      document.getElementById('deal-grid').setAttribute('aria-busy', 'true');
  });
  document.body.addEventListener('htmx:afterRequest', () => {
    document.getElementById('deal-grid').setAttribute('aria-busy', 'false');
  });
  document.body.addEventListener("htmx:configRequest", (event) => {
    if (
      !form.contains(event.detail.elt) &&
      !event.detail.elt.closest(".load-more-wrap")
    )
      return;
    for (const [key, value] of Object.entries(event.detail.parameters)) {
      if (value === "") delete event.detail.parameters[key];
    }
    if (
      !event.detail.parameters.currency &&
      (event.detail.parameters.min_price ||
        event.detail.parameters.max_price ||
        ["price_low", "price_high"].includes(event.detail.parameters.sort))
    ) {
      form.elements.currency.value = "USD";
      event.detail.parameters.currency = "USD";
    }
    document.getElementById("request-error").hidden = true;
  });
  document.body.addEventListener("htmx:afterSwap", (event) => {
    if (event.detail.target.id !== "deal-grid") return;
    const params = new URLSearchParams();
    for (const [key, value] of new FormData(form))
      if (value && value !== "0") params.set(key, value);
    history.replaceState(
      null,
      "",
      "/" + (params.size ? "?" + params.toString() : ""),
    );
    syncPresets();
  });
  for (const name of ["htmx:responseError", "htmx:sendError"])
    document.body.addEventListener(name, () => {
      document.getElementById("request-error").hidden = false;
    });
  document.querySelectorAll("[data-preset]").forEach((btn) =>
    btn.addEventListener("click", () => {
      const settings = JSON.parse(btn.dataset.preset);
      const active = btn.getAttribute('aria-pressed') === 'true';
      for (const [key, value] of Object.entries(settings)) {
        const input = form.elements[key];
        if (input.type === "checkbox") input.checked = !active && Boolean(value);
        else input.value = active ? (key === 'sort' ? 'discount_pct' : key === 'min_discount' ? '0' : '') : value;
      }
      validateRanges();
      refreshDeals();
    }),
  );
  function syncPresets() {
    document.querySelectorAll("[data-preset]").forEach((btn) => {
      const active = Object.entries(JSON.parse(btn.dataset.preset)).every(
        ([key, value]) =>
          form.elements[key].type === "checkbox"
            ? form.elements[key].checked
            : form.elements[key].value === value,
      );
      btn.classList.toggle("active", active);
      btn.setAttribute("aria-pressed", String(active));
    });
    syncFilterChips();
  }
  function syncFilterChips() {
    const container = document.getElementById('active-filters');
    if (!container) return;
    const focusedFilter = container.contains(document.activeElement)
      ? document.activeElement.dataset.filter : null;
    const labels = {
      q: 'Search', category: 'Gear', brand: 'Brand', store: 'Store',
      currency: 'Currency', min_discount: 'Minimum discount',
      min_price: 'Min price', max_price: 'Max price',
      size_min: 'Length from', size_max: 'Length to', reviewed: 'Expert review available',
      include_clothing: 'Clothing & accessories included',
    };
    container.replaceChildren();
    for (const [name, label] of Object.entries(labels)) {
      const input = form.elements[name];
      if (!input.value || input.value === '0' || (input.type === 'checkbox' && !input.checked)) continue;
      const chip = document.createElement('button');
      chip.type = 'button';
      chip.className = 'filter-chip';
      chip.dataset.filter = name;
      let value = input.tagName === 'SELECT' ? input.selectedOptions[0].textContent : input.value;
      if (name.startsWith('size_')) value += ' cm';
      if (name === 'min_price' || name === 'max_price') value += ' ' + (form.elements.currency.value || 'USD');
      const text = input.type === 'checkbox' ? label : `${label}: ${value}`;
      chip.setAttribute('aria-label', `Remove ${text}`);
      const caption = document.createElement('span');
      caption.textContent = text;
      const cross = document.createElementNS('http://www.w3.org/2000/svg', 'svg');
      cross.setAttribute('viewBox', '0 0 16 16');
      cross.setAttribute('aria-hidden', 'true');
      const path = document.createElementNS(cross.namespaceURI, 'path');
      path.setAttribute('d', 'm4 4 8 8M12 4l-8 8');
      cross.append(path);
      chip.append(caption, cross);
      chip.addEventListener('click', () => {
        if (input.type === 'checkbox') {
          input.checked = false;
          if (name === 'include_clothing' && category.selectedOptions[0]?.dataset.clothing) category.value = '';
        }
        else input.value = name === 'min_discount' ? '0' : '';
        validateRanges();
        syncPresets();
        // Removing a chip must not strand keyboard focus on the document body.
        (container.querySelector('button') || form.elements.q).focus({preventScroll: true});
        refreshDeals();
      });
      container.append(chip);
    }
    container.hidden = !container.childElementCount;
    document.getElementById('filter-summary').textContent = container.childElementCount
      ? `${container.childElementCount} selected` : '';
    if (focusedFilter) {
      const nextFocus = [...container.children].find(chip => chip.dataset.filter === focusedFilter);
      (nextFocus || container.querySelector('button') || form.elements.q).focus({preventScroll: true});
    }
  }
  syncPresets();
  const toggle = document.getElementById("view-toggle");
  toggle.addEventListener("click", () => {
    const compact = document
      .getElementById("deal-grid")
      .classList.toggle("compact-view");
    toggle.setAttribute("aria-pressed", String(compact));
    toggle.textContent = compact ? "Grid view" : "Compact view";
    try {
      localStorage.setItem("fp-view", compact ? "compact" : "grid");
    } catch (_) {}
  });
  try {
    if (localStorage.getItem("fp-view") === "compact") toggle.click();
  } catch (_) {}
}
document.addEventListener("click", async (event) => {
  const share = event.target.closest(".share-btn");
  if (share) {
    try {
      if (navigator.share)
        await navigator.share({
          title: share.dataset.name,
          url: share.dataset.url,
        });
      else {
        await navigator.clipboard.writeText(share.dataset.url);
        showToast("Deal link copied.");
      }
    } catch (error) {
      if (error.name !== "AbortError")
        showToast("Use the product link to share this find.");
    }
  }
  const link = event.target.closest(".product-link");
  if (link && new URL(link.href).origin !== location.origin) {
    const card = link.closest(".deal-card, .retailer-offer");
    if (!card) return;
    try {
      navigator.sendBeacon(
        "/api/event",
        new Blob(
          [
            JSON.stringify({
              event_type: "click",
              deal_url: card.dataset.href,
              deal_name: card.dataset.name,
              store: card.dataset.store,
              category: card.dataset.category,
            }),
          ],
          { type: "application/json" },
        ),
      );
    } catch (_) {}
  }
});
const waitlist = document.getElementById("waitlist-form");
if (waitlist)
  waitlist.addEventListener("submit", async (event) => {
    event.preventDefault();
    const button = waitlist.querySelector("button");
    const feedback = waitlist.querySelector(".form-feedback");
    button.disabled = true;
    feedback.textContent = "Saving your place…";
    try {
      const response = await fetch("/waitlist", {
        method: "POST",
        body: new FormData(waitlist),
      });
      const result = await response.json().catch(() => {
        throw new Error('We could not connect. Please try again in a moment.');
      });
      if (!response.ok || !result.ok)
        throw new Error(result.error || "Please try again.");
      feedback.textContent =
        "You’re on the list. We’ll let you know when a spot opens.";
      waitlist.reset();
    } catch (error) {
      feedback.textContent =
        error.message || "Could not connect. Please try again.";
    } finally {
      button.disabled = false;
    }
  });

for (const form of document.querySelectorAll(".alert-signup")) {
  form.addEventListener("submit", async (event) => {
    event.preventDefault();
    const feedback = form.querySelector(".form-feedback");
    const button = form.querySelector("button");
    button.disabled = true;
    feedback.textContent = "Saving your signup…";
    try {
      const response = await fetch(form.action, {
        method: "POST",
        body: new FormData(form),
        headers: { Accept: "application/json" },
      });
      const result = await response.json().catch(() => {
        throw new Error('We could not connect. Please try again in a moment.');
      });
      if (!response.ok || !result.ok)
        throw new Error(result.error || "Please try again.");
      feedback.textContent = result.message;
      if (result.removal_token) {
        const link = document.createElement("a");
        link.href =
          "/alerts/remove#" + encodeURIComponent(result.removal_token);
        link.textContent = " Save your private removal link.";
        feedback.append(link);
      }
      form.reset();
    } catch (error) {
      feedback.textContent =
        error.message || "Could not connect. Please try again.";
    } finally {
      button.disabled = false;
    }
  });
}
const removal = document.getElementById("removal-token");
if (removal && location.hash) {
  try { removal.value = decodeURIComponent(location.hash.slice(1)); }
  catch (_) { removal.value = ''; }
}
