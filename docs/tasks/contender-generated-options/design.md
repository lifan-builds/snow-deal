# Change boundary

The gap lives in shared Shopify variant ingestion and the independent catalog product.js audit. Add a small source-scoped predicate in the existing Shopify parser module, matching exact contenderbicycles.com (and its www form) and the observed generated marker in variant title/option fields. Do not infer identity by stripping text. Reuse the predicate for audit rejection. Keep USD decoding and selected identity checks intact. No schema, UI-label, global normalization or history rewrite.

Expected files: common/deal_common/parsers/shopify.py; common/deal_common/catalog/audit.py; focused parser/audit tests and minimal factual fixtures as needed; parser contracts and mirror. Root owns research/task docs, source capture/replay, scoped refresh, publication and deployment. Inactive Circle changes remain untouched. Fresh source replacement removes old generated records from current browsing while stored history remains unchanged.
