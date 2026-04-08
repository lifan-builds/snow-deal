# FreshPowder — Go-To-Market Strategy

## Product Summary

FreshPowder is a ski & snowboard deal aggregator that tracks prices across 15+ North American retailers every 6 hours, matches expert review scores, and surfaces the best deals through a fast, filterable interface. It is invite-gated to create exclusivity and control growth.

**Live at:** https://snow-deals.onrender.com

---

## Target Audience

### Phase 1: Chinese Diaspora Skiers in North America (Seed)
- Active in WeChat ski groups, Rednote (小红书), USCardForum (USCF)
- Price-sensitive, deal-oriented, often buy gear online
- Strong word-of-mouth culture within tight community groups
- Many are intermediate skiers upgrading gear = high purchase intent

### Phase 2: Broader North American Ski Community (Scale)
- Reddit r/skiing, r/snowboarding, r/skideals
- Facebook ski groups (regional: "Colorado Ski Deals", "PNW Ski Swap", etc.)
- Ski forums: TGR (TetonsGravityResearch), EpicSki, SkiTalk
- Deal-hunting communities: Slickdeals, FatWallet

### Phase 3: International (Future)
- Add European retailers (Blue Tomato, Snowinn, Bergfreunde)
- Add Japanese retailers for the Japan ski market

---

## Repo Visibility

**Status: Private** (changed 2026-04-07)

Rationale: Scraper configs, store-specific selectors, categorization rules, and keyword lists are competitive advantages. Keeping the repo private prevents cloning. GitHub Actions and Render deployment work identically on private repos.

---

## Revenue Model

### Stage 1: Free + Affiliate Links (Now → 1,000 users)
- Replace direct retailer links with affiliate links where available
- Major programs to join:
  - **evo** — AvantLink affiliate program (8-12% commission)
  - **Backcountry/Steep & Cheap** — AvantLink (5-7%)
  - **REI** — AvantLink (5%)
  - **Moosejaw** — AvantLink (7-10%)
  - **The House** — AvantLink / ShareASale
  - **Altitude Sports** — direct affiliate program
  - **Amazon** — Amazon Associates (4-8% on sporting goods)
- Estimated revenue: ~$2-5 per click-through-purchase at average $300 cart = $1-3 per conversion
- At 1% conversion rate on 100 daily clicks = $1-3/day = **$30-90/month early stage**

### Stage 2: Freemium Features (1,000+ users)
Keep core deal browsing free. Add paid tier ("FreshPowder Pro", ~$5-8/month or $49/year):
- **Price alerts** — Get notified when a specific product drops below your target price
- **Price history charts** — See 30/60/90-day price trends per product
- **Size watchlist** — Track your sizes across brands, get notified when your size is in stock + on sale
- **Early access** — See deals 1 hour before free users (scrape results held briefly)
- **No ads** — If we ever add sponsor placements

### Stage 3: Non-Intrusive Ads (2,000+ users)

Guiding principle: ads should feel like content, not interruptions. The clean UI is a competitive advantage — protect it.

**Tier 1: Sponsored Deal Cards (2,000+ users)**
- A single card in the deal grid labeled "Sponsored" — same visual format as organic deals
- Sold directly to retailers (evo, Backcountry, etc.) as a premium placement
- Limited to 1 per page load to avoid feed pollution
- Pricing: flat fee per week or CPM, negotiate directly

**Tier 2: Category Sponsorships (3,000+ users)**
- Small "Powered by [Brand]" logo/link at the top of a category section
- Example: "Skis powered by evo" — subtle, relevant, non-disruptive
- Good fit for brands wanting category association

**Tier 3: Newsletter Sponsor Slot (when email list exists)**
- Single sponsor block in the weekly "Best Deals" email
- Format: one featured deal from the sponsor, clearly labeled
- High open rates in deal-focused emails = good value for advertisers

**Tier 4: Display Ads — Pro Removal Lever Only (5,000+ users)**
- Only consider traditional display ads (e.g. a single sidebar unit) if needed as a "Pro removes ads" incentive
- Never: pop-ups, interstitials, autoplay video, or banner ads in the deal grid
- If implemented, limit to one static unit outside the main content area

**What we will NOT do:**
- Google AdSense / programmatic ads — low CPM at our scale, ugly, signals "cheap"
- Any ad that delays page load or blocks interaction
- Ads before 2,000 users — the revenue is negligible and the UX cost is real

### Revenue Projection (Conservative)
| Stage | Users | Monthly Revenue | Source |
|-------|-------|----------------|--------|
| Seed | 100 | $0 | Free, no affiliate yet |
| Early | 500 | $50-150 | Affiliate links |
| Growth | 2,000 | $300-800 | Affiliate + early Pro subs + sponsored cards |
| Scale | 10,000 | $2,000-5,000 | Affiliate + Pro + sponsored cards + category sponsors + newsletter |

---

## Invitation Model

### Design Principles
- No user accounts at this stage — invite code sets a session cookie, that's it
- The invite gate is a **short-term launch tactic** (weeks, not permanent) to gather feedback and create buzz
- Don't over-engineer virality before 50 people have tried the product
- More users = more affiliate clicks = more revenue, so remove the gate as soon as feedback is solid

### How It Works
1. Admin creates codes via `/admin/codes` (random or custom) or CLI (`snow-deals-agg add-code`)
2. User enters a code at `/invite` → gets a JWT session cookie → full access
3. No signup, no email, no account — zero friction
4. Waitlist captures emails from users who don't have a code (for future outreach)

### Stage 1: Batch Code Drop (Now)
- **Seed code:** `FRESHPOWDER2026` — 100 uses, shared across all seed channels
- One memorable code is easier to spread in group chats than many unique codes
- When it's used up, natural scarcity kicks in — creates urgency for latecomers to join waitlist

### Stage 2: Referral Tracking (When ready)
- After entering a code, show users a share link: `snow-deals.onrender.com/invite?ref=FRESHPOWDER2026`
- Track which code/link brought in traffic — gives referral data without needing accounts
- ~10 lines of code, no user registration required

### Stage 3: Optional Email Capture (When ready)
- Add a banner on the main deals page: "Get weekly deal alerts"
- Collects emails from engaged users who are already in, not as a gate
- Builds the email list needed for future newsletter and Pro tier

### Stage 4: Open Registration (When ready)
- Remove invite gate entirely (`PUBLIC_MODE=true`)
- Keep referral tracking infrastructure for future reward programs
- Build real user accounts only when needed for Pro features (saved searches, price alerts)

### Code Distribution Strategy
| Channel | Code | Format |
|---------|------|--------|
| WeChat groups (personal) | `FRESHPOWDER2026` | Post with screenshot + code |
| Rednote post | `FRESHPOWDER2026` | "Comment to get a code" (engagement bait) |
| USCardForum thread | `FRESHPOWDER2026` | Forum post with the code |
| Reddit r/skideals | `FRESHPOWDER2026` | Comment drop |
| Friends & ski buddies | `FRESHPOWDER2026` | Direct message |

**Total capacity: 100 uses → covers seed phase, then waitlist takes over**

---

## Channel Strategy

### Tier 1: Owned / Direct (Week 1-2)

**WeChat Ski Groups**
- Post a screenshot of the UI showing a great deal (high discount, known brand)
- Include 3-5 invite codes directly in the message
- Message template: "Built a tool that tracks ski deals across 15+ stores every 6 hours. Found [Brand X] at 60% off yesterday. Here are a few invite codes if you want to try: [codes]. Let me know if you want more."
- Follow up with periodic "deal of the day" screenshots to keep engagement

**Rednote (小红书)**
- Create a post: "我做了一个滑雪装备比价网站" (I built a ski gear price comparison site)
- Include screenshots of the landing page and deal grid
- Drop 5-10 invite codes in comments to first responders
- Use hashtags: #滑雪 #滑雪装备 #省钱 #北美滑雪 #ski
- Post weekly "best deals this week" content to build following

**USCardForum**
- Create a thread in the deals/lifestyle section
- Position as: "Free tool for tracking ski/snowboard deals — invite-only beta"
- USCF users are deal-savvy, will appreciate the discount % focus
- Drop codes, ask for feedback

### Tier 2: Community Seeding (Week 2-4)

**Reddit**
- r/skideals — Most directly relevant. Post when you find an exceptional deal, mention "found via my deal tracker" with link
- r/skiing and r/snowboarding — Participate genuinely, mention FreshPowder when relevant (don't spam)
- r/SkiGear — Gear discussion, mention price tracking when someone asks "is this a good price?"
- Key: Be a helpful community member first, promoter second. Reddit hates self-promotion.

**Facebook Ski Groups**
- Regional groups: "Colorado Ski & Ride Deals", "PNW Ski Deals", "Northeast Ski Deals"
- Same approach: share genuine deals, mention the tool
- Many of these groups have thousands of members

**Ski Forums**
- TetonsGravityResearch (TGR) forums — Gear Talk section
- Newschoolers — Park/freestyle audience, younger demographic
- EpicSki — Older/more affluent skier demographic

### Tier 3: Content & SEO (Month 2+)

**Blog / Content Strategy**
- "Best Ski Deals This Week" — Weekly roundup post
- "When to Buy Ski Gear" — Seasonal buying guide (evergreen SEO)
- "Best Budget Skis 2025-2026" — Buyer's guide linking to tracked deals
- Host on a subdomain or `/blog` route

**SEO for Landing Page**
- Landing page (`/invite`) is already indexable
- Add OG image for social sharing
- Target keywords: "ski deals", "snowboard deals", "ski gear sale", "best ski prices"

### Tier 4: Partnerships (Month 3+)
- Ski clubs and university ski teams — Offer bulk invite codes
- Ski podcasts — Sponsor a segment or offer codes to listeners
- Ski influencers on Instagram/YouTube — "Built by a skier, for skiers" angle

---

## Launch Timeline

### Week 1: Soft Launch
- [ ] Join affiliate programs (evo, Backcountry, REI via AvantLink)
- [ ] Generate 60 invite codes
- [ ] Seed WeChat groups (20 codes)
- [ ] Post on Rednote (10 codes)
- [ ] Post on USCardForum (10 codes)
- [ ] Share with friends/ski buddies (10 codes)
- [ ] Monitor analytics dashboard for click-through and usage

### Week 2: Gather Feedback
- [ ] Check admin stats: which stores get most clicks? Which filters used?
- [ ] Collect user feedback via WeChat / DM
- [ ] Fix any reported bugs or UX issues
- [ ] Implement viral invite loop (auto-generate codes on signup)

### Week 3-4: Expand
- [ ] Set up affiliate link replacement in card URLs (evo, Backcountry, REI via AvantLink)
- [ ] Track affiliate conversions
- [ ] Post on Reddit r/skideals
- [ ] Join Facebook ski deal groups
- [ ] Create weekly "best deals" content for Rednote

### Month 2: Content & Growth
- [ ] Build email list from waitlist signups
- [ ] Send first "Weekly Deals" email
- [ ] Start blog content for SEO
- [ ] Implement price history tracking (Pro feature foundation)
- [ ] Evaluate user numbers and viral coefficient

### Month 3+: Monetize
- [ ] Launch Pro tier if user base > 1,000
- [ ] Approach retailers for sponsored placements
- [ ] Expand to European retailers if demand exists

---

## Key Metrics to Track

| Metric | Tool | Target (Month 1) |
|--------|------|-------------------|
| Registered users | Admin dashboard | 200 |
| Daily active users | Event analytics | 30 |
| Deal clicks/day | `/admin/stats` | 100 |
| Invite code conversion | Auth DB queries | 60% of codes used |
| Viral coefficient (K) | Referral tracking | > 1.0 |
| Affiliate revenue | AvantLink dashboard | First $ earned |
| Waitlist signups | Admin waitlist tab | 50 |

---

## Risks & Mitigations

| Risk | Impact | Mitigation |
|------|--------|------------|
| Retailers block scraper | No deals to show | Rotate user agents, respect rate limits, have backup selectors |
| Low viral coefficient | Slow growth | Increase invite codes per user, add sharing incentives |
| Seasonality (summer slump) | Usage drops May-Oct | Add off-season deals (hiking, camping gear), or accept seasonal nature |
| Competitor launches similar tool | Market share split | First-mover advantage, community building, unique features (reviews integration) |
| Free tier too generous | No Pro conversion | Gate advanced features (alerts, history) early, even before charging |

---

## Open Decisions

- [ ] **Affiliate program applications** — Need to apply to AvantLink, Amazon Associates. Some require existing traffic numbers.
- [ ] **Email infrastructure** — Need a transactional email provider for waitlist/alerts (Resend, Postmark, or SendGrid free tier)
- [ ] **Custom domain** — Consider `freshpowder.deals` or `getfreshpowder.com` instead of `snow-deals.onrender.com`
- [ ] **Bilingual support** — Should the landing page / UI have a Chinese language option for Phase 1 audience?
- [ ] **Mobile app** — PWA (Progressive Web App) could be a quick win for mobile users without building native apps
