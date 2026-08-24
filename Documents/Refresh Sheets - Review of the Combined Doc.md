# Review: combined refresh-sheet doc, all seven clients

Reviewed August 24, 2026 against the live sites, each page's Search Console
queries, and a sitemap scope check on every proposed title.

---

## 1. Arsenal has no sheet. Its section holds Snow's content.

Everything under the Arsenal heading is Snow Teeth Whitening's four product
pages: whitening strips, whitening kit, toothpaste collection, whitening pen.
The section does not mention arsenalhealth.com once.

**What Arsenal's sheet should say instead:** its five target pages are the
JavaScript-rendered pages that serve roughly 8 words of raw HTML each. Until
the server-rendering fix in the developer workbook ships, no title or copy
change can be verified as live, because the raw page does not carry them.
Arsenal's refresh work is genuinely blocked, and its sheet should say that in
one short section rather than repeating another client's pages.

---

## 2. SameDay's AC repair page carries the leak detection page's title

The URL is https://samedayutah.com/emergency-services/air-conditioner-repair/
and the proposed title is "Water Leak Detection & Repair Services in Salt
Lake City, UT". That belongs to the leak detection page further down the same
sheet.

**And the page cannot be worked on at all right now.** That URL answers every
request with a Rank Math redirect pointing at itself, endlessly, so visitors
and Google both dead-end. It is one of the five refresh targets and it grew
from 1 click to 23 year over year, which makes the loop expensive in AC
season. The fix is in SameDay's technical queue as row 6: delete the Rank
Math rule whose source and destination are the same URL. Nothing else on that
page is worth doing until it loads.

---

## 3. The Superior and Beehive sections predate the scope corrections

Both sections contain titles that take a service word another page on the
same site already owns. Five instances:

| Page | In the doc | Owned by |
|---|---|---|
| Superior water treatment | "Water Softeners in Utah" | Narrows a category page. The page covers softeners, reverse osmosis, filtration, and UV. |
| Superior furnace repair | "Furnace Repair & Heating Services" | Heating is the /hvac/ parent category |
| Beehive water heater install | "Water Heater Repair & Installation" | /water-heater-repair-utah/ |
| Beehive drain cleaning | "Snaking & Jetting" | /hydro-jetting-drain-cleaning-utah/ |
| Superior water treatment H1 | "Water Softener Installation & Service" | Same narrowing as the title |

Corrected versions are in the two client folders:
Clients/Superior/monthly_plan/ and Clients/Beehive/monthly_plan/. Replace
those two sections of the doc with the corrected sheets.

---

## 4. Comfort's emergency services title, worth a decision

Proposed: "24/7 Emergency Heating & AC Repair Services on the Wasatch Front"
for /services/emergency-services/.

The scope check flags "heating" because
/services/hvac-systems/residential-heating/ exists. My read is that this one
is defensible: the page is the emergency hub, and "24/7 Emergency" scopes it
away from the standard heating page, in the same way Superior's emergency
plumbing page coexists with its plumbing pages. Flagging it so the call is
made deliberately rather than by default.

---

## What checked out clean

- **SameDay's "$69" furnace tune-up price is real.** Verified on the live
  page, which lists a $69 standard tune-up, $99 ultimate, $169 ultimate with
  cleaning, and a $100 full price that is seasonally discounted. Putting the
  price in the title is the strongest differentiator in the whole document.
- **Cudio's five service-page titles are correctly scoped.** Each names its
  own service and adds features rather than a sibling's service.
- **Snow's four product titles are correctly scoped.** Product pages with
  feature modifiers, no cannibalization exposure.
- **EW's five sections are current** and match the corrected sheet.

---

## The check that now runs automatically

    python scripts/check_title_cannibalization.py <sitemap_url> "<title>" <url>

Pulls the client's sitemap and reports any sibling page that already owns a
service word in the proposed title, plus any word naming the page's parent
category. Validated against all four rejected titles (it catches every one)
and all six corrected titles (it clears every one). Run it before any title
goes into a sheet.
