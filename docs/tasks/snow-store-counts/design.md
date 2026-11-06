# Boundary

The bug lives in snow web routes: store_counts is derived from store_status ingestion rows rather than query_deals visible selected offers. Implement a SQL grouped-count path sharing the existing query selection and filters; do not duplicate eligibility predicates or issue one full database query per retailer. Exclude the current store facet while applying other current query arguments, count before pagination, and retain zero entries through existing configured-store rendering. Preserve store_status for health/source reports. Small local query construction refactor is allowed only with result equivalence tests. Shared common catalog and new Circle parser are out of scope.

Expected files: snow db.py, web/routes.py, meaningful query/HTTP tests, mirrored web/deployment contract and these task records. No template or styling changes unless needed for correct labels. Separate worktree and release from the Circle deployment currently running. No commit/push until review.

The index-only boundary was insufficient because normal filtering uses `/deals` htmx responses. The parent approved a shared retailer-options partial and an out-of-band innerHTML update to the existing select on normal filter requests. Load-more leaves options untouched. Unknown selected stores are appended to the escaped option list.

Native browser review found that an innerHTML OOB swap retained the requested selected attribute but moved the live selection to Boardom. The parent approved replacing the whole select with a stable id/name and selected option. Use outerHTML and verify the live selection plus the following submitted request.
