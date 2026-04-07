# Findings

Research results, discoveries, and external content collected during project work.

> **Security note:** External content (web searches, API responses, copied docs) goes
> here — never directly into PLANS.md. This separation prevents untrusted content from
> polluting the trusted execution plan.

## Research & References

### Affiliate Programs (2026-04-07)
- **AvantLink** — Primary affiliate network for outdoor retail. Hosts programs for evo (8-12%), Backcountry/Steep & Cheap (5-7%), REI (5%), Moosejaw (7-10%)
- **Amazon Associates** — 4-8% on sporting goods category
- **Altitude Sports** — Direct affiliate program (Canadian retailer)
- Revenue estimate at 1% conversion on 100 daily clicks: $30-90/month early stage

### Competitor Landscape
- **Skis.com deal page** — Manual curation, not aggregated
- **Slickdeals** — General deal site, ski gear is a small niche within it
- **r/skideals** — Community-driven, no automated tracking
- No direct competitor doing multi-store automated ski deal aggregation with review matching

## Discoveries

- (2026-03-13) BlueZone Sports pagination misleading: shows "1 / 5" but has 9 actual pages. `aria-label="Next"` for nav, not `rel="next"`.
- (2026-04-07) Exclusion keyword design: space-padded `" used "` prevents matching "unused"/"refused". Prepend space to search string so keywords match at start: `f" {name} {url}".lower()`.
- (2026-04-07) Model name ambiguity: "hera" is both a Ride snowboard and a Ride boot. "frontier" is both a Jones snowboard and Dragon goggles. Single-word names must be brand-qualified or placed in the correct category-specific set.
- (2026-04-07) NOT_HARDGOODS_KEYWORDS was too narrow — "cable lock", "boxer", "mattress", "bed", "pillow" etc. were passing through brand fallback and getting categorized as hardgoods.
- (2026-04-07) htmx load-more pattern: `hx-target="this"` on the button leaves the wrapper div in place, nesting new cards as grandchildren. Fix: `hx-target="closest .load-more-wrap"` + `hx-swap="outerHTML"`.

## Error Log

| Error | Context | Resolution | Date |
|-------|---------|------------|------|
| "Used K2 Mindbender" not excluded | `" used "` didn't match at start of string | Prepend space: `f" {name} {url}".lower()` | 2026-04-07 |
| Load-more breaks grid layout | `hx-target="this"` leaves wrapper div | Changed to `hx-target="closest .load-more-wrap"` | 2026-04-07 |
| Dragon goggles categorized as snowboards | "Lil D" matched SNOWBOARD multi-word names | Moved to `("lil d", "goggles")` in MULTI_WORD_MODEL_NAMES | 2026-04-07 |
| Ride Hera boots categorized as snowboards | "hera" in SNOWBOARD_MODEL_NAMES | Moved to SNOWBOARD_BOOT_MODEL_NAMES | 2026-04-07 |
