# Evaluation & Contracts

This document contains objective grading criteria and specific verification contracts for tasks defined in `PLANS.md`.

## Grading Criteria

- **Functionality**: Feature works as specified, handles edge cases, no regressions
- **Code Quality**: Type-annotated, no dead code, follows existing patterns
- **Testing**: `python -m pytest aggregator/tests/ -x -q` — all pass
- **Visual**: Renders correctly at 1440px, 768px, 480px viewports
- **Performance**: Page loads < 2s, htmx swaps < 500ms

## Active Sprint Contracts

### Phase 4: Viral Invite Loop
- **Verification Method**: Generate a code via admin, use it to sign up, verify 3 personal codes appear at `/my-codes`, use one of those codes in an incognito tab
- **Acceptance Threshold**: New user receives exactly 3 single-use invite codes upon signup. Used codes show as consumed. Referral chain tracked in auth DB.

### Phase 4: Affiliate Link Integration
- **Verification Method**: Click a deal card, verify the URL redirects through affiliate tracking parameter
- **Acceptance Threshold**: evo, Backcountry, REI links include affiliate tags. Non-affiliate stores use direct links. Click tracking still fires.

## Evaluation Log

- (2026-04-07) Phase 3: UI Polish & GTM Readiness — **Pass**
  - 71/71 tests pass
  - All features render correctly (presets, share buttons, featured card, scroll-to-top)
  - Click tracking fires via sendBeacon to /api/event
  - Search highlighting works with multi-word queries
  - Smart empty state shows context-aware messages
  - Committed and deployed to Render

- (2026-04-07) Data Quality Fixes — **Pass**
  - Used/demo gear excluded via EXCLUDE_KEYWORDS
  - Goggles no longer miscategorized as snowboards
  - Ride Hera/Cadence correctly categorized as snowboard boots
  - NOT_HARDGOODS_KEYWORDS expanded to catch accessories
