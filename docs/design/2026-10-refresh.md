# FreshPowder refresh — October 31, 2026

## Design

An alpine field guide with ivory paper, forest green, orange accents, accessible product links, explicit currency, and a compact mobile filter panel. Server-rendered FastAPI/Jinja2 and htmx remain the application architecture.

Original artwork was generated with the built-in imagegen tool and compressed to JPEG for serving. Source PNGs remain in the local image generation output directory. Project assets:

- `aggregator/aggregator/web/static/img/alpine-hero.jpg`
- `aggregator/aggregator/web/static/img/alpine-gear.jpg`

### Generation prompts

Hero: Original wide landscape illustration for FreshPowder, a ski and snowboard gear deal website. Vintage alpine travel poster illustration, no lettering or logos. Sweeping snowy mountain bowl with dramatic jagged peaks, dark evergreen trees in the foreground, tiny warm orange ski lift cabin on a fine cable, winding ski tracks. Screenprinted gouache / cut paper texture. Deep forest green, pale icy mint, warm ivory snow, burnt orange. Mountains detailed on right and center, quiet left sky. Crisp shapes, tactile grain, independent outdoor magazine feeling. No UI elements.

Gear: Original small editorial illustration for the empty state and gear guide. Forest-green skis and an orange snowboard propped against a rustic ski trail sign, small pine tree and snow mound, warm ivory background. Vintage alpine travel poster / screenprinted gouache cut-paper style, forest green, sage, ivory, burnt orange, tactile grain. No people, lettering, logos or watermark. Landscape composition with generous margins.

## Operational changes

- Daily scrape at 05:17 UTC. Restore the previous public deal snapshot before scraping so price observations, first-seen dates and reviews survive.
- Request pacing, bounded concurrency and bounded retries for rate limits and transient errors. Track partial collection failures separately from store availability.
- Reject empty output, fewer than 20 reporting stores, a greater than 50% count collapse, or more than 10% uncategorized output in the publication workflow.
- Upload quality metrics as an Actions artifact and summary. Replace the release asset without deleting the release.
- Trigger a project-scoped Vercel deploy hook held only in GitHub secrets. Verify `/healthz` serves the expected snapshot before declaring success.
- Refresh reviews weekly or on explicit workflow input. Recompute matches after price refreshes.
- Exact offer price and corresponding size variants for Shopify; vendor-based brands, numeric ski lengths, false-product exclusions, currency-specific price queries, previous-price annotations and a 72-hour listing age limit.
- Public store coverage and non-sensitive snapshot health; invite gating for the full deal browser remains enabled.

## Verification so far

86 offline tests pass, JavaScript syntax and whitespace checks pass. Desktop and 390px landing layouts inspected; custom art loads with no horizontal overflow. Budget preset verified to select USD and return filtered cards.

MEC and Level Nine Sports returned access-blocked responses during direct checks. Their availability must remain explicit; this change does not bypass retailer access restrictions. Alpine Shop VT migrated to Shopify and its collection URLs were updated from its own navigation.

Deployment and a complete fresh scheduled-workflow run still require verification before the change is considered operationally complete.
