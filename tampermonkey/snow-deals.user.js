// ==UserScript==
// @name         snow-deals — Discount Ranker
// @namespace    https://github.com/snow-deals
// @version      0.3.1
// @description  Adds discount % badges to product cards and lets you sort by best deal across ALL pages
// @match        *://www.bluezonesports.com/*
// @match        *://www.aspenskiandboard.com/collections/*
// @run-at       document-idle
// @grant        GM_addStyle
// @grant        GM_xmlhttpRequest
// @connect      www.bluezonesports.com
// @connect      www.aspenskiandboard.com
// ==/UserScript==

(function () {
  "use strict";

  // ---------------------------------------------------------------------------
  // Shared styles
  // ---------------------------------------------------------------------------

  GM_addStyle(`
    .deal-badge {
      position: absolute;
      top: 0.5rem;
      right: 0.5rem;
      padding: 0.2rem 0.55rem;
      border-radius: 0.25rem;
      font-size: 0.8rem;
      font-weight: 700;
      line-height: 1.3;
      color: #fff;
      z-index: 5;
      pointer-events: none;
      box-shadow: 0 1px 4px rgba(0,0,0,0.25);
    }
    .deal-badge--hot  { background: #dc3545; }
    .deal-badge--warm { background: #e67e22; }
    .deal-badge--mild { background: #c19b2e; }

    .deal-sort-btn {
      display: inline-flex;
      align-items: center;
      gap: 0.35rem;
      padding: 0.35rem 0.85rem;
      border: 2px solid #dc3545;
      border-radius: 0.35rem;
      background: #fff;
      color: #dc3545;
      font-size: 0.85rem;
      font-weight: 600;
      cursor: pointer;
      transition: background 0.15s, color 0.15s;
      white-space: nowrap;
    }
    .deal-sort-btn:hover,
    .deal-sort-btn--active {
      background: #dc3545;
      color: #fff;
    }
    .deal-sort-btn:disabled {
      opacity: 0.6;
      cursor: wait;
    }

    .deal-toolbar {
      display: inline-flex;
      align-items: center;
      padding: 0 0.5rem;
      margin-left: 0.5rem;
    }

    .deal-summary {
      font-size: 0.8rem;
      color: #666;
      margin-left: 0.6rem;
      white-space: nowrap;
    }
  `);

  // ---------------------------------------------------------------------------
  // Shared helpers
  // ---------------------------------------------------------------------------

  function parsePrice(text) {
    if (!text) return null;
    const m = text.match(/\$?\s?([\d,]+\.?\d*)/);
    return m ? parseFloat(m[1].replace(/,/g, "")) : null;
  }

  function calcDiscount(current, original) {
    if (original == null || original <= 0 || current >= original) return 0;
    return Math.round((1 - current / original) * 100);
  }

  function badgeClass(pct) {
    if (pct >= 30) return "deal-badge--hot";
    if (pct >= 15) return "deal-badge--warm";
    return "deal-badge--mild";
  }

  function injectBadge(card, pct, options) {
    const target = options?.onWrapper ? (card.closest("[class*='col-']") || card.parentElement) : card;
    if (!target || target.querySelector(".deal-badge")) return;
    card.dataset.discount = pct;
    target.style.position = target.style.position || "relative";
    if (pct > 0) {
      const badge = document.createElement("span");
      badge.className = `deal-badge ${badgeClass(pct)}`;
      badge.textContent = `-${pct}%`;
      target.appendChild(badge);
    }
  }

  function fetchPage(url) {
    return new Promise((resolve, reject) => {
      GM_xmlhttpRequest({
        method: "GET",
        url,
        onload: (resp) =>
          resp.status >= 200 && resp.status < 300
            ? resolve(resp.responseText)
            : reject(new Error(`HTTP ${resp.status} for ${url}`)),
        onerror: (err) => reject(err),
      });
    });
  }

  function collectStats(cards) {
    let onSale = 0, maxDiscount = 0, total = cards.length;
    cards.forEach((c) => {
      const d = parseInt(c.dataset.discount || "0", 10);
      if (d > 0) { onSale++; if (d > maxDiscount) maxDiscount = d; }
    });
    return { total, onSale, maxDiscount };
  }

  // ---------------------------------------------------------------------------
  // Site adapter: BlueZone Sports
  // ---------------------------------------------------------------------------

  const BlueZone = {
    getCards() {
      return [...document.querySelectorAll(".card.product-card")];
    },

    processCards() {
      this.getCards().forEach((card) => {
        const priceDiv = card.querySelector(".product-price");
        if (!priceDiv) { card.dataset.discount = 0; return; }
        let current = null, original = null;
        const accent = priceDiv.querySelector(".text-accent");
        if (accent) current = parsePrice(accent.textContent);
        const del = priceDiv.querySelector("del");
        if (del) original = parsePrice(del.textContent);
        if (current == null) {
          const prices = [];
          const walker = document.createTreeWalker(priceDiv, NodeFilter.SHOW_TEXT);
          let node;
          while ((node = walker.nextNode())) {
            const matches = node.textContent.match(/\$[\d,]+\.?\d*/g);
            if (!matches) continue;
            for (const m of matches) {
              const p = parsePrice(m);
              if (p !== null) prices.push({ p, struck: !!node.parentElement.closest("s,strike,del") });
            }
          }
          const struck = prices.filter((x) => x.struck).map((x) => x.p);
          const normal = prices.filter((x) => !x.struck).map((x) => x.p);
          if (struck.length && normal.length) { current = Math.min(...normal); original = Math.max(...struck); }
          else if (prices.length === 1) current = prices[0].p;
          else if (prices.length >= 2) { const s = prices.map((x) => x.p).sort((a, b) => a - b); current = s[0]; original = s[s.length - 1]; }
        }
        injectBadge(card, calcDiscount(current, original), { onWrapper: true });
      });
    },

    findGrid() {
      const first = document.querySelector(".card.product-card");
      if (!first) return null;
      let el = first.parentElement;
      while (el) {
        if (el.querySelectorAll(".card.product-card").length > 1) return el;
        el = el.parentElement;
      }
      return first.parentElement;
    },

    getWrapper(card) {
      return card.closest("[class*='col-']") || card.parentElement;
    },

    getNextPageUrl(doc) {
      const next = doc.querySelector('a[aria-label="Next"]');
      return next ? next.href || next.getAttribute("href") : null;
    },

    async fetchAllPages(updateStatus) {
      const allWrappers = [];
      let nextUrl = this.getNextPageUrl(document);
      let page = 1;
      while (nextUrl && page < 50) {
        page++;
        updateStatus(`Loading page ${page}…`);
        try {
          const html = await fetchPage(nextUrl);
          const parser = new DOMParser();
          const doc = parser.parseFromString(html, "text/html");
          doc.querySelectorAll(".card.product-card").forEach((card) => {
            const col = card.closest("[class*='col-']") || card.parentElement;
            allWrappers.push(col);
          });
          nextUrl = this.getNextPageUrl(doc);
        } catch (e) { console.error("[Deal Finder]", e); break; }
      }
      return allWrappers;
    },

    injectToolbarInto(toolbar) {
      const sortSelect = document.querySelector("#sort_select");
      if (sortSelect) {
        const bar = sortSelect.closest(".d-flex") || sortSelect.parentElement;
        bar.appendChild(toolbar);
        return true;
      }
      return false;
    },

    hidePagination() {
      document.querySelectorAll('nav[aria-label="Page navigation"], ul.pagination').forEach((el) => {
        const nav = el.closest("nav") || el;
        nav.classList.add("deal-hidden-pagination");
        nav.style.display = "none";
      });
    },

    showPagination() {
      document.querySelectorAll(".deal-hidden-pagination").forEach((el) => {
        el.style.display = "";
        el.classList.remove("deal-hidden-pagination");
      });
    },
  };

  // ---------------------------------------------------------------------------
  // Site adapter: Shopify stores (Aspen Ski and Board, etc.)
  // ---------------------------------------------------------------------------

  const Shopify = {
    _apiData: null, // { handle: { title, price, compare, discount } }
    _cardSelector: ".boost-sd__product-item",

    _getCollectionHandle() {
      const m = location.pathname.match(/\/collections\/([^/?#]+)/);
      return m ? m[1] : null;
    },

    async _loadApiData() {
      if (this._apiData) return this._apiData;
      const handle = this._getCollectionHandle();
      if (!handle) return {};

      const map = {};
      let page = 1;
      while (page <= 10) {
        const url = `${location.origin}/collections/${handle}/products.json?limit=250&page=${page}`;
        try {
          const text = await fetchPage(url);
          const data = JSON.parse(text);
          const products = data.products || [];
          if (products.length === 0) break;
          for (const p of products) {
            const v = p.variants?.[0];
            if (!v) continue;
            const price = parseFloat(v.price) || 0;
            const compare = v.compare_at_price ? parseFloat(v.compare_at_price) : null;
            map[p.handle] = {
              title: p.title,
              price,
              compare,
              discount: calcDiscount(price, compare),
            };
          }
          if (products.length < 250) break;
          page++;
        } catch (e) { console.error("[Deal Finder] API fetch error:", e); break; }
      }
      this._apiData = map;
      return map;
    },

    _getHandleFromCard(card) {
      const link = card.querySelector("a[href*='/products/']");
      if (!link) return null;
      const m = link.getAttribute("href").match(/\/products\/([^/?#]+)/);
      return m ? m[1] : null;
    },

    getCards() {
      return [...document.querySelectorAll(this._cardSelector)];
    },

    async processCards() {
      const data = await this._loadApiData();
      const cards = this.getCards();
      cards.forEach((card) => {
        const handle = this._getHandleFromCard(card);
        const info = handle ? data[handle] : null;
        const pct = info ? info.discount : 0;
        injectBadge(card, pct);
      });
    },

    findGrid() {
      const first = document.querySelector(this._cardSelector);
      if (!first) return null;
      let el = first.parentElement;
      while (el) {
        if (el.querySelectorAll(this._cardSelector).length > 1) return el;
        el = el.parentElement;
      }
      return first.parentElement;
    },

    getWrapper(card) {
      return card;
    },

    async fetchAllPages(updateStatus) {
      // Shopify's Boost Commerce loads products dynamically with infinite scroll
      // or pagination. We'll use the JSON API data to create virtual cards for
      // products not currently in the DOM.
      updateStatus("Loading all products via API…");
      const data = await this._loadApiData();
      const existingHandles = new Set();
      this.getCards().forEach((c) => {
        const h = this._getHandleFromCard(c);
        if (h) existingHandles.add(h);
      });

      const newCards = [];
      for (const [handle, info] of Object.entries(data)) {
        if (existingHandles.has(handle)) continue;
        // Create a minimal product card matching Boost Commerce structure
        const card = document.createElement("div");
        card.className = "boost-sd__product-item deal-virtual-card";
        card.style.cssText = "position:relative; border:1px solid #eee; border-radius:8px; padding:1rem; margin-bottom:1rem; background:#fff;";
        const priceHtml = info.compare
          ? `<span style="color:#c44; font-weight:600;">$${info.price.toFixed(2)}</span> <s style="color:#999; font-size:0.85em;">$${info.compare.toFixed(2)}</s>`
          : `<span style="font-weight:600;">$${info.price.toFixed(2)}</span>`;
        const productUrl = `${location.origin}/products/${handle}`;
        card.innerHTML = `
          <div style="position:relative; z-index:1; pointer-events:none;">
            <div style="font-weight:600; margin-bottom:0.4rem; font-size:0.9rem;">${info.title}</div>
            <div>${priceHtml}</div>
          </div>
          <a href="${productUrl}" style="position:absolute; inset:0; z-index:2; cursor:pointer;" aria-label="${info.title}"></a>`;
        newCards.push(card);
      }
      return newCards;
    },

    injectToolbarInto(toolbar) {
      // Boost Commerce sort button or toolbar
      const sortBtn = document.querySelector(".boost-sd__sorting-button");
      if (sortBtn) {
        sortBtn.parentElement.appendChild(toolbar);
        return true;
      }
      const boostToolbar = document.querySelector(
        ".boost-sd__toolbar-inner, .boost-sd__toolbar-top, .boost-sd__toolbar"
      );
      if (boostToolbar) {
        boostToolbar.appendChild(toolbar);
        return true;
      }
      return false;
    },

    hidePagination() {
      document.querySelectorAll(
        ".boost-sd__pagination, .boost-sd__load-more, [class*='boost-sd__pagination']"
      ).forEach((el) => {
        el.classList.add("deal-hidden-pagination");
        el.style.display = "none";
      });
    },

    showPagination() {
      document.querySelectorAll(".deal-hidden-pagination").forEach((el) => {
        el.style.display = "";
        el.classList.remove("deal-hidden-pagination");
      });
    },
  };

  // ---------------------------------------------------------------------------
  // Site detection
  // ---------------------------------------------------------------------------

  function detectSite() {
    const host = location.hostname.replace(/^www\./, "");
    if (host.includes("bluezonesports.com")) return BlueZone;
    if (host.includes("aspenskiandboard.com")) return Shopify;
    return null;
  }

  // ---------------------------------------------------------------------------
  // Sort + Toolbar (shared logic, delegates to site adapter)
  // ---------------------------------------------------------------------------

  let isSorted = false;
  let originalOrder = [];
  let injectedCards = [];
  let allLoaded = false;

  async function sortByDiscount(btn, summaryEl, site) {
    const container = site.findGrid();
    if (!container) return;

    if (isSorted) {
      injectedCards.forEach((c) => c.remove());
      originalOrder.forEach((el) => container.appendChild(el));
      isSorted = false;
      btn.classList.remove("deal-sort-btn--active");
      btn.innerHTML = "&#9660; Sort by Discount";
      site.showPagination();
      updateSummary(summaryEl, site, false);
      return;
    }

    const currentCards = site.getCards();
    originalOrder = currentCards.map((c) => site.getWrapper(c));

    if (!allLoaded) {
      btn.disabled = true;
      btn.innerHTML = "&#9660; Loading…";

      injectedCards = await site.fetchAllPages((msg) => {
        btn.innerHTML = `&#9660; ${msg}`;
      });

      for (const card of injectedCards) container.appendChild(card);
      if (site.processCards) await site.processCards();
      else {
        for (const card of injectedCards) {
          const handle = site._getHandleFromCard?.(card);
          const info = handle && site._apiData?.[handle];
          if (info) injectBadge(card, info.discount);
        }
      }
      allLoaded = true;
      btn.disabled = false;
    }

    const allCards = site.getCards();
    const wrappers = allCards.map((card) => ({
      el: site.getWrapper(card),
      discount: parseInt(card.dataset.discount || "0", 10),
    }));
    wrappers.sort((a, b) => b.discount - a.discount);
    wrappers.forEach((w) => container.appendChild(w.el));

    site.hidePagination();
    isSorted = true;
    btn.classList.add("deal-sort-btn--active");
    btn.innerHTML = "&#9660; Sorted by Discount ✓";
    updateSummary(summaryEl, site, true);
  }

  function updateSummary(el, site, showAll) {
    if (!el) return;
    const stats = collectStats(site.getCards());
    const scope = showAll ? " across all pages" : "";
    el.textContent = `${stats.onSale} of ${stats.total} on sale (up to ${stats.maxDiscount}% off)${scope}`;
  }

  function injectToolbar(stats, site) {
    const toolbar = document.createElement("div");
    toolbar.className = "deal-toolbar";

    const btn = document.createElement("button");
    btn.className = "deal-sort-btn";
    btn.title = "Loads all pages and sorts every product by discount %";
    btn.innerHTML = "&#9660; Sort by Discount";

    const summary = document.createElement("span");
    summary.className = "deal-summary";
    if (stats.onSale > 0) {
      summary.textContent = `${stats.onSale} of ${stats.total} on sale (up to ${stats.maxDiscount}% off)`;
    }

    btn.addEventListener("click", () => sortByDiscount(btn, summary, site));
    toolbar.appendChild(btn);
    toolbar.appendChild(summary);

    if (!site.injectToolbarInto(toolbar)) {
      const grid = site.findGrid();
      if (grid) grid.parentElement.insertBefore(toolbar, grid);
    }
  }

  // ---------------------------------------------------------------------------
  // Init
  // ---------------------------------------------------------------------------

  async function init() {
    const site = detectSite();
    if (!site) return;

    // For Shopify/Boost Commerce sites, wait for dynamic product cards to render
    if (site === Shopify) {
      await new Promise((resolve) => {
        const check = () => document.querySelector(site._cardSelector) ? resolve() : setTimeout(check, 300);
        check();
        setTimeout(resolve, 15000); // safety timeout
      });
    }

    const cards = site.getCards();
    if (cards.length === 0) return;

    await site.processCards();
    const stats = collectStats(site.getCards());
    injectToolbar(stats, site);
  }

  init();
})();
