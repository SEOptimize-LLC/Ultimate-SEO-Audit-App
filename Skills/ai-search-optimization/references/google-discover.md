# Google Discover — Visibility & Eligibility Reference

> Google Discover is a personalized content feed (the swipe-right feed on Android, plus the Google app and mobile homepage) — a way for users to find content **outside a query**. It is a distinct traffic channel from Search, with its own GSC Performance report and its own eligibility model, and the Ultimate SEO Auditor otherwise has no coverage of it. This reference defines what Discover rewards, how to read the Discover report, and an auditable eligibility checklist. It backs the `discover_auditor.py` module and Cluster 20 (Discover Visibility) of `../technical-seo-agent/references/ranking-factors-checklist-2026.md`.

## Read this first: Discover has no deterministic inclusion levers

Unlike indexation or ranking, **there are no hard rules that force a page into Discover — only eligibility signals that raise or lower probability.** Google's own guidance is guideline-based, and Daniel Foley Carter states the same plainly ("no hard and fixed ways of getting included, only general guidelines"). Everything below is therefore a **best-practice eligibility checklist and a testable hypothesis**, never a pass/fail ranking rule. Ship Discover recommendations as "raises Discover probability," not "will rank." Do not promote any item here to a deterministic rule.

## Why it matters

- Discover can be a very large traffic source in the right niches (news, lifestyle, how-to, product-adjacent editorial) — often exceeding Search traffic for content sites — and it is **invisible to a standard technical/on-page audit** because it's a feed, not a SERP.
- It's mostly a **content/blog opportunity, not a commercial-page one**: Discover overwhelmingly surfaces informational, article-style content (e.g. a retailer's "best coats for winter this year," not a product or category page). A client with a healthy blog and zero Discover strategy is leaving a channel unopened.

## The Discover Performance report (how to read it)

GSC → Performance → **Discover** (the tab only appears once a property has received Discover impressions). It carries far less data than Search:
- **Filters:** date range, specific URLs that appeared, and **appearance type** (e.g. "Web Stories," video).
- **Metrics:** clicks, impressions, CTR by page and country — but **no query data** (Discover isn't query-triggered).
- **What to look for:** which content types/topics earn Discover impressions (double down on those); high-impression / low-CTR Discover pages (a thumbnail, title, or freshness problem); sudden drops (Discover traffic is volatile by nature — confirm against a longer window before diagnosing).

If a property has **no Discover tab at all**, that is itself the finding: the site has never been surfaced in Discover, and the eligibility checklist below is the opportunity.

## Eligibility checklist (auditable)

Each item is a testable eligibility signal. The `discover_auditor.py` module scores the deterministic ones from the crawl (content-type, dates, author markers, mobile, images, title format); the judgment ones (is the title clickbait? is the content genuinely informational and current?) are LLM-judgment / manual.

**Content type**
- Is the page **informational / article content** rather than commercial (product, category, service)? Commercial pages rarely appear in Discover. *Test:* page type = blog/article, not product/category/service.

**Title**
- Is the title **non-clickbait, non-shock, and does it match the content**? A misleading or shock title (title promises X, content delivers Y) reduces Discover eligibility and is associated with spam. *Test:* title accurately reflects body; no shock/curiosity-gap phrasing.

**Format & experience**
- **Mobile-first & fast:** Discover is a mobile feed. The page must be responsive, load quickly, and pass Core Web Vitals (route to the `core-web-vitals` skill / `mobile_first_auditor.py`).
- **Consumable layout:** ample spacing, correct heading hierarchy, strong imagery, video where it fits — content that's easy to skim on a phone.
- **High-quality lead image:** Discover cards are image-led. A large, high-resolution, non-clickbait image materially affects whether a card is served and clicked. (Google supports `max-image-preview:large` — confirm the meta robots tag isn't restricting image preview.)

**E-E-A-T / authorship**
- Is there **clear author attribution** — named author, bio, picture, and ideally social/entity links — by someone who genuinely knows the topic (a topical expert, not a generalist byline)? Discover leans on experience/expertise signals. *Test:* author markup / visible byline present; author is topically credible.

**Timeliness**
- Does the topic have **active demand and a current/trending angle**? Discover favors fresh, up-to-date, trending content. Validate with Google Trends (active trend data) + a keyword tool (real search demand), ideally with a news element. Distinguish an evergreen comparison ("best electric scooters 2026") from a genuine news angle ("new e-scooter laws in Utah") — the latter skews more Discover-eligible.
- Is the content genuinely **current** (recently published or a real, substantive update — not a cosmetic date bump)? Cross-check with `date_freshness_auditor.py` so a Discover "freshness" recommendation isn't undermined by an unreliable date signal.

**Web Stories (optional booster)**
- Consider **Google Web Stories** (a tappable, visual, video/image/animation format; available as a WordPress plugin, pairs well with a page builder like RankMath). Web Stories are a distinct Discover appearance type and can add an eligibility surface, especially in visual niches.

## What NOT to do

- Don't expect **commercial pages** (products, categories, service pages) to earn Discover — steer clients to editorial/blog content for this channel.
- Don't use **clickbait or shock titles** to chase Discover — it's disfavored, associated with spam, and risks the whole property's Discover eligibility.
- Don't treat Discover volatility as a ranking regression — traffic swings are inherent to a feed; confirm against a longer window and the wider Discover trend before diagnosing a "drop."
- Don't present any of this as a guarantee. Frame every recommendation as raising eligibility probability.

## How this maps into an audit

- **Auditor coverage:** `discover_auditor.py` scores the deterministic eligibility signals (content type, dates, author markers, mobile parity, image presence, title format) across article/blog URLs and, when a GSC Discover Performance export is provided, reports current Discover-earning pages and high-impression/low-CTR opportunities. Judgment items (clickbait, informational-vs-commercial, topical authority) are flagged for LLM/manual review.
- **Checklist:** the itemized, severity-tagged version is Cluster 20 (Discover Visibility) in `../technical-seo-agent/references/ranking-factors-checklist-2026.md`.
- **Expected-outcome tagging:** Discover eligibility work is a **Ranking Lever for a separate channel** where a content library exists but earns no Discover traffic; it is **not** applicable to purely transactional sites with no editorial content — say so rather than manufacturing a finding. Because inclusion is non-deterministic, pair every Discover recommendation with the "raises probability, not guaranteed" caveat and a validation method (monitor the Discover Performance report for the URL over the following weeks).

## Source

Daniel Foley Carter, "GSC Lesson 3 — Google Discover, what is it" (knowledge-base transcript), cross-referenced against Google Search Central's Discover documentation (which Foley cites directly). Framed as guideline-based eligibility per Google's and Foley's own "no hard rules" statement. Added 2026-07.
