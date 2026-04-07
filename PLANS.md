# FreshPowder — GTM Launch & Growth

This ExecPlan is a living document. The sections Progress, Surprises & Discoveries,
Decision Log, and Outcomes & Retrospective must stay up to date as work proceeds.

## Purpose / Big Picture

FreshPowder is ready for go-to-market launch. The product tracks deals across 15+ ski/snowboard retailers, has a polished UI with filtering/presets/search, invite-gated access, a marketing landing page, and click analytics. The focus now shifts from building to growing: seeding users, enabling virality, and preparing for monetization.

## Current State (as of 2026-04-07)

The web app is live at https://snow-deals.onrender.com with:
- Deal aggregation across 15+ stores, scraped every 6h via GitHub Actions
- Expert review score matching (OutdoorGearLab, GoodRide)
- 10 filter types + 5 quick filter presets + search with highlighting
- Featured hero card, gradient card borders, share buttons, click tracking
- Invite-gated access with human-readable codes, public landing page with waitlist
- Admin panel for code generation, analytics dashboard, waitlist management
- Custom branded assets (favicon, hero background, empty state illustration)
- Repo set to **private**

## Progress

### Phase 1: Core Product (Complete)
- [x] (2026-03-13) Initial CLI + Tampermonkey userscript for BlueZone Sports
- [x] (2026-03) Multi-store aggregator with FastAPI web app
- [x] (2026-03) SQLite DB, Turso auth, Docker deployment on Render
- [x] (2026-03) Category/brand filtering, sorting, pagination
- [x] (2026-03) Review score integration (OutdoorGearLab, GoodRide)

### Phase 2: Auth & Landing (Complete)
- [x] (2026-04) JWT invite code system with rate limiting
- [x] (2026-04) Human-readable invite codes (POWDER-SUMMIT-42 format)
- [x] (2026-04) Marketing landing page with stats, deal preview, waitlist
- [x] (2026-04) Admin panel for code management and analytics

### Phase 3: UI Polish & GTM Readiness (Complete)
- [x] (2026-04-07) Data quality: filter used/demo gear, fix miscategorization
- [x] (2026-04-07) Visual polish: glassmorphism, animations, gradient borders, card entrance effects
- [x] (2026-04-07) Custom assets: favicon, hero background, empty state illustration
- [x] (2026-04-07) Quick filter presets (Under $100, Top Reviewed, 50%+ Off, Tax Free, New Arrivals)
- [x] (2026-04-07) Deal click tracking via sendBeacon to /api/event
- [x] (2026-04-07) Share button on cards (native share / clipboard copy + toast)
- [x] (2026-04-07) Search term highlighting, smart empty states, reset filters button
- [x] (2026-04-07) Featured hero card, scroll-to-top, skeleton pulse loading
- [x] (2026-04-07) GTM strategy document (GTM.md)
- [x] (2026-04-07) Repo set to private

### Phase 4: Launch & Growth (Next)
- [ ] Implement viral invite loop (auto-generate 3 codes on signup, /my-codes page)
- [ ] Join affiliate programs (AvantLink for evo, Backcountry, REI)
- [ ] Replace direct retailer links with affiliate links
- [ ] Seed initial users via WeChat groups (20 codes)
- [ ] Post on Rednote with invite codes
- [ ] Post on USCardForum
- [ ] Monitor analytics and gather feedback
- [ ] Weekly "best deals" content for social channels

### Phase 5: Monetization Foundation (Future)
- [ ] Price history tracking (store historical prices per product)
- [ ] Price alert system (notify when product drops below target)
- [ ] Size watchlist feature
- [ ] Email infrastructure (Resend/Postmark) for alerts and waitlist
- [ ] Pro tier ($5-8/mo) gating premium features
- [ ] Custom domain (freshpowder.deals or similar)

## Surprises & Discoveries

- BlueZone Sports pagination shows "1 / 5" but actually has 9 pages (2026-03-13)
- `" used "` keyword with space padding avoids matching "unused"/"refused" — critical for exclusion keywords (2026-04-07)
- Single-word model names like "frontier", "ultra", "hera" are too ambiguous — conflict across product categories. Must use brand-qualified multi-word entries (2026-04-07)
- Brand fallback categorization catches accessories as hardgoods — NOT_HARDGOODS_KEYWORDS must be aggressively expanded (2026-04-07)
- htmx `hx-target="this"` on load-more button breaks grid layout because the wrapper div stays — must use `hx-target="closest .load-more-wrap"` with `hx-swap="outerHTML"` (2026-04-07)

## Decision Log

- Decision: Invite-gated access with public landing page
  Rationale: Controls growth, creates exclusivity, landing page enables SEO/marketing. Deal content requires authentication.
  Date: 2026-04

- Decision: Repo set to private
  Rationale: Scraper configs, store selectors, categorization rules are competitive advantages. GitHub Actions and Render work identically on private repos.
  Date: 2026-04-07

- Decision: Keyword-based categorization over ML
  Rationale: Fast, deterministic, debuggable. False positives fixed by expanding keyword lists. ML would be overkill for ~15 stores with known product patterns.
  Date: 2026-03

- Decision: SQLite for deals + Turso for auth
  Rationale: Deals are scraped and rebuilt every 6h — local SQLite is fast and ephemeral. Auth data (sessions, invite codes) must persist across deploys — Turso cloud DB handles this.
  Date: 2026-03

- Decision: htmx over React/SPA
  Rationale: Server-rendered templates with htmx partials give fast interactivity without JS framework complexity. Simpler to maintain, faster initial load, better SEO.
  Date: 2026-03

## Outcomes & Retrospective

Phases 1-3 complete. Product is polished and ready for user testing. GTM strategy defined in GTM.md. Next milestone: seed 100 users and measure viral coefficient.
