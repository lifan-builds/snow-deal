# Restore snow snapshot deployment headroom

The November 5 snow refresh uploaded validated data but production never served it. The subsequent tools PR preview reproduces a 225.49 MB function against this project's 225 MB limit. Prior compaction alone leaves the growing snapshot at 147,640,320 bytes. The active snow site still serves the prior 04:19 observation; the prepared public snapshot is checked at 13:40.

Compress the exact validated build database and explicitly exclude its uncompressed packaging copy. Before database defaults are imported, reconstruct a digest-verified local temporary copy, atomically, and keep SQLite reads read-only. Preserve explicit DATABASE_PATH behavior, local development and skip-download source bytes. No runtime downloads, migrations, new services, history deletion or source-policy changes.

Required gates: independent review, meaningful corruption/concurrency/startup tests, full offline suite and CI; exact round-trip of the current public prepared snapshot; preservation of all offer/price-history and source-run rows; successful Vercel preview and production; exact live checked_at, selected variant and price/ranking checks. Then update tools PR23 with the repaired main branch and complete its separate audited cycling/tools rollout. Existing standing publication approval applies.

Rollback to the previous ready production deployment if startup fails. A plain revert alone cannot resolve the existing size failure; retain the older ready deployment while investigating. Keep the full public data asset and all historical rows unchanged. No blind redeploy of the oversized bundle.

Status: independent review passed 776 offline tests, including 22 snapshot cases. Final helper round-trip and full-data integrity passed; CI and deployment remain pending. The separately downloaded public source and prepared copies are task-owned, with before/after row digests under .local/release/snow-42033643607/. No production change yet.

Current full public-snapshot evidence: the prepared 147,640,320 bytes compress to 18,230,396 bytes (about 88% smaller). Reconstruction exactly matches SHA256 68261da4c07b900c1a76e5818bcc83be0bc097d508f9cc3dda3031339d441df0, retains checked_at 2026-11-05T13:40:12.920989 and passes SQLite integrity. Complete row digests for 190,839 price-history rows, 250,212 offer observations, 27,734 selected-offer records, 32 source runs and existing reviews/matches are unchanged by preparation. Local extraction timing is not a deployed performance benchmark. See docs/tasks/snow-compressed-snapshot/research/.
