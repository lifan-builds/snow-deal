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

## Verified results

- [Full refresh run 41249727608](https://github.com/lifan-builds/snow-deal/actions/runs/41249727608) completed successfully on October 31 at 23:04 UTC, including snapshot publication, deploy-hook execution and production timestamp verification.
- Production `/healthz` returned `ok`, snapshot `2026-10-31T23:03:22.493515`, with 26 stores reporting deals. The live landing page and store report both show 11,299 listings.
- The preceding baseline contained 5,586 raw listings across 25 stores. The new run contains 11,299 listings across 26 stores. Size coverage improved from about 29% to 63%; image coverage from 91% to 96%. This is a comparison between runs, not a controlled inventory experiment.
- Alpine Shop VT is restored with 110 listings. MEC and Level Nine remain unavailable. Ski Pro AZ, Skiis & Biikes, The House and Ski Essentials are explicitly marked partial. Two HTTP failures were retailer rate limits; bounded retries retain useful results without hiding incomplete coverage.
- 90 offline tests pass, including matching prices to available sizes, pagination through filtered pages, rate-limit retries, price history, currency filters, input parsing, auth gating and waitlist failure handling. JavaScript syntax and whitespace checks pass.
- Desktop and 390px mobile layouts inspected with no horizontal overflow. Search, the USD budget preset, empty-state reset and pagination from 60 to 120 cards were exercised on the isolated local catalog. Production landing artwork and store report were verified after deployment.
- Final visual inspection caught review scores being inherited from related but different product variants. Matching now requires the normalized model and gender variant to agree, retaining model numbers and suffixes. Reconciliation on an isolated copy of the published snapshot produced 89 matches and removed the incorrect Lange flex matches. Builds reconcile matches as well, so existing published snapshots receive the correction immediately.

Screenshots: [desktop landing](screenshots/landing-desktop.png), [mobile landing](screenshots/landing-mobile.png), [store report](screenshots/store-report.png).

Retailer restrictions, omitted variant information and transient failures remain visible limitations. No retailer access controls were bypassed. Full catalog access remains invite-only.
