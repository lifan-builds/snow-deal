"use strict";
(() => {
  const button = document.getElementById("save-search");
  if (!button) return;
  const container = document.getElementById("saved-searches");
  const status = document.getElementById("save-status");
  const key = `deal-aggregator:${document.body.dataset.catalog}:searches`;
  const allowed = new Set(["q", "category", "brand", "store", "size", "format", "platform", "min_reference", "max_price", "min_discount", "stock"]);
  let saved = [];
  try {
    const parsed = JSON.parse(localStorage.getItem(key) || "[]");
    if (Array.isArray(parsed)) saved = parsed.filter(item => item && typeof item.query === "string" && typeof item.label === "string").slice(0, 8);
  } catch { /* Storage is optional; browsing remains available. */ }
  function safeQuery(query) {
    const params = new URLSearchParams(query);
    for (const name of [...params.keys()]) if (!allowed.has(name)) params.delete(name);
    return params.toString();
  }
  function persist() {
    try { localStorage.setItem(key, JSON.stringify(saved)); return true; }
    catch { status.textContent = "Browser storage is unavailable. This search will only stay here until you reload."; return false; }
  }
  function render() {
    container.replaceChildren();
    saved.forEach((item, index) => {
      const chip = document.createElement("span"); chip.className = "saved-item";
      const link = document.createElement("a");
      link.href = `/?${safeQuery(item.query)}#deals`; link.textContent = item.label;
      const remove = document.createElement("button"); remove.type = "button"; remove.textContent = "×";
      remove.setAttribute("aria-label", `Remove saved search: ${item.label}`);
      remove.addEventListener("click", () => { saved.splice(index, 1); persist(); render(); });
      chip.append(link, remove); container.append(chip);
    });
  }
  button.addEventListener("click", () => {
    const query = safeQuery(location.search);
    const params = new URLSearchParams(query);
    const label = [params.get("q"), params.get("category"), params.get("brand"), params.get("size"),
      params.get("format"), params.get("platform"), params.get("store"),
      Number(params.get("max_price")) > 0 ? `Up to $${params.get("max_price")}` : "",
      Number(params.get("min_discount")) > 0 ? `${params.get("min_discount")}%+ off` : "",
      params.get("stock") === "true" ? "In stock" : ""].filter(Boolean).join(" · ") || "My deal search";
    saved = [{query, label}, ...saved.filter(item => item.query !== query)].slice(0, 8);
    if (persist()) status.textContent = "Saved in this browser. No email alerts are sent.";
    render();
  });
  const filters = document.querySelector(".filter-panel");
  if (matchMedia("(max-width: 700px)").matches) filters.open = false;
  render();
})();
