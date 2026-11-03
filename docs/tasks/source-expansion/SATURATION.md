# Public-source saturation pass — November 2, 2026

Continued the earlier source expansion until the researched queue stopped yielding additional sources that could pass the existing public-feed admission process. This is a practical limit of this pass, not a claim that every retailer or possible improvement has been exhausted. All changes and snapshots remain local.

## Measured outcome

| Catalog | Contributing retailers | Eligible in-stock listings | Listings at least 40% off |
| --- | ---: | ---: | ---: |
| Big Ring | 7 → 16 | 956 → 1,142 | 73 → 87 |
| Bench Drop | 7 → 9 | 213 → 347 | 9 → 20 |

Measured at `2026-11-03T01:51:51.809922+00:00`. The baseline is the previous 7-source-per-catalog checkpoint. Both counts use the same USD1,000 cycling / USD200 tools retailer-reference floors, confirmed feed stock and percentage-off-first ranking. These are listings across storefronts, not unique models or independent suppliers; Colorado Cyclist and Planet Cyclery can overlap other stores. Shipping and tax are excluded, and compare-at prices are not proven historical selling prices. The final cycling refresh reapplied the stricter classifier to every configured source. Existing tools observations retained their original dates unless refreshed. Mike's Bikes gained two eligible listings and two deep discounts during its refresh; those changes are not attributed to new retailer coverage.

## Admitted and broadened sources

Tool Nut and Woodcraft were broadened while retaining every previously configured collection. All other rows below are new sources in this pass.

| Source | Eligible at final snapshot | At least 40% off | Separate product checks |
| --- | ---: | ---: | ---: |
| [INTENSE](https://intensecycles.com/collections/sale?currency=USD) | 4 | 0 | 3/3 |
| [Bike Mart](https://www.bikemart.com/collections/bikes?currency=USD) | 59 | 2 | 3/3 |
| [First Stop Board Barn](https://www.firststopboardbarn.com/collections/blazing-summer-bike-sale?currency=USD) | 1 | 0 | 1/1 |
| [Colorado Cyclist](https://coloradocyclist.com/collections/all-bikes?currency=USD) | 34 | 5 | 3/3 |
| [Planet Cyclery](https://planetcyclery.com/collections/mtb-bikes?currency=USD) | 24 | 3 | 3/3 |
| [Max Warehouse](https://www.maxwarehouse.com/collections/power-tools?currency=USD) | 21 | 0 | 3/3 |
| [Worldwide Cyclery](https://worldwidecyclery.com/collections/bikes-and-frames?currency=USD) | 4 | 1 | 3/3 |
| [State Bicycle Co.](https://www.statebicycle.com/collections/sale?currency=USD) | 1 | 0 | 1/1 |
| [The Path Bike Shop](https://www.thepathbikeshop.com/collections/bike-eligible-to-ship?currency=USD) | 33 | 1 | 3/3 |
| [Tool Nut](https://www.toolnut.com/collections/saws?currency=USD) | 134 | 3 | 3/3 |
| [Woodcraft](https://www.woodcraft.com/collections/clearance?currency=USD) | 72 | 4 | 3/3 |
| [OakTree Supply](https://www.oaktreesupply.com/collections/clearance?currency=USD) | 82 | 11 | 3/3 |
| [Fanatik Bike Co.](https://www.fanatikbike.com/collections/on-sale-complete-bikes?currency=USD) | 24 | 0 | 3/3 |

There were **48 distinct sampled offers with matching separate merchant data** across this pass, including all 11 OakTree listings at least 40% off and five newly discovered Tool Nut/Woodcraft listings. Price, reference, exact variant identity/options and reported stock matched. This is admission evidence, not a representative accuracy percentage, checkout test, or independent historical-price audit. Earlier incomplete/rejected probes remain in the JSON receipt.

Max Warehouse's earlier rate limit recovered; its 21 qualifying offers add no 40%-off deals, so it is a breadth gain rather than a deep-discount gain. Colorado Cyclist's previous 404 came from the wrong collection path; the observed live all-bikes collection works. OakTree supplies the largest new deep-discount gain.

## Quality improvements

- Reject bike socks/pants, mislabelled tires and seatpost clamps; preserve genuine fat-tire bikes and framesets.
- Recognize observed frame, e-commuter and brand-qualified State Bicycle taxonomy. SM/MD/LG match S/M/L in size filters without splitting compound sizes.
- Exclude returned, blemished, lightly ridden, open-box and showroom inventory, including condition facts carried only in tags.
- A negative shipping tag wins over positive shipping tags. Fanatik advertised some products with both `ship-usa` and `in-store-only`/`no-ship`. Product-page review caught this after the price checks passed; those products were removed before finalization. The earlier 36-listing Fanatik probe is superseded by the final restricted result above.
- Keep genuine jig saws while excluding woodworking jigs and standalone router-table systems. Digital-display machines remain eligible; showroom models do not.
- Select shipping-eligible Path Bike Shop inventory; keep Skirack's sampled pickup-only bikes out. Do not infer shipability from a retailer being valid for snow equipment.

## Where this pass stops

The existing complete-feed mechanism has been applied to the researched candidates. The remaining work is source-specific integration, access recovery, or a deliberate scope change; repeatedly adding URLs to the current parser will not close these gaps.

- **No usable qualifying feed results:** Tool Factory Outlet, Hartville, Kona, evo. This means the tested collections did not provide qualifying discounted variants, not that the retailer has no sale anywhere.
- **Shipping/condition mismatch:** Skirack, plus excluded individual showroom/blemished/used/pickup-only offers. Do not lower these gates to inflate coverage.
- **Access failures:** Acme, Northern Tool, Toolup, MyToolStore, US Tool and Fastener, Lehigh Valley Abrasives and Jenson returned HTTP403. CPO returned HTTP503 through bounded retries; Competitive Cyclist returned HTTP202 without usable storefront data. These are dated observations, not permanent-outage claims. No access controls were bypassed.
- **Different data integrations:** Taylor Toolworks, Rockler, Fasteners Inc, Woodworker Express, Oliver Machinery, Bike Closet, Canyon, Transition and BicycleBuys need additional validated stock/reference/variant handling. Taylor's sampled grinder bundle has a real-looking discount and explicit stock, but catalog/detail identifiers differ and selectable-SKU destinations/pagination are not validated. Rockler's tested public search request returned no products; that does not prove an empty catalog.

The best next supply work is a tested Taylor Toolworks adapter, then Rockler/Fasteners integrations or retailer-provided feeds for the inaccessible large tool sellers. These remain real coverage gaps. Some discovery leads were not retailers or did not establish the intended merchant (99spokes, guessed PowerToolSuperstore/Ari domains); they were not counted as sources.

## Verification and artifacts

**377 offline tests passed**, scoped Ruff passed, and `git diff --check` passed. Both local previews and standalone packages serve healthy snapshots with matching hashes. Paging remains unique and ordered by descending percentage off. The cycling refresh completed every configured source under the final shipping rules. Original observation dates and daily history were preserved; no operational database, deployment state or credentials were used.

- [Detailed evidence and candidate dispositions](../../benchmarks/2026-11-02-source-saturation.json)
- [Prior expansion checkpoint](IMPLEMENTATION.md)
- Local previews: [Big Ring](http://127.0.0.1:8766/) and [Bench Drop](http://127.0.0.1:8767/)

The standalone artifacts are reviewable local builds. Publishing is a separate release action and still needs fresh release-wide validation. This pass did not push or deploy.
