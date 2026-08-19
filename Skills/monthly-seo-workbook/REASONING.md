# No mechanical output. Ever.

> Read this before any task in this workbook. It outranks every task recipe.
> Owner's instruction, 2026-08-17, after three judgment columns on 1.5 were
> filled by rule instead of by reading the data.

## What these tasks are for

Every tab in this workbook exists to produce a **reasoned decision** that shapes
the client's implementation roadmap. The data fetch is the input. The judgment
is the deliverable. A tab filled correctly but thoughtlessly has produced
nothing, because a human then has to redo the thinking that was supposed to have
been done here, and they have to do it while distrusting everything else on the
tab.

That is the bottleneck. It is worse than an empty cell, because an empty cell
announces itself and a defaulted one does not.

## The rule

**Never write a value into a judgment field from a lookup table, a default, or a
rule of thumb.** If the field calls for a decision, make the decision by reading
the fetched data for that specific row, and put the reasoning in the sheet where
the next person can check it.

Judgment fields include, and are not limited to: business value, priority,
severity, effort, selected/not selected, expected outcome, recommendation text,
and every "why" or "rationale" column.

## Three failures that produced this rule

All on Education Walkthrough's 1.5 tab, all in one pass:

**"Selected in 1.8?" set to N on all ten rows.** No row had been assessed. N is a
claim that a candidate was considered and rejected. The truthful state was
undecided, which the blank cell expresses and the dropdown allows. Meanwhile
`/t-tess-rubric` sat there at 25,864 impressions, position 6.0, clicks down 45%
and marked "not selected" by a machine that had not looked at it.

**Business value assigned by page type.** Money page High, post Medium, a
two-line lookup. It graded `/what-to-look-for-during-classroom-walkthroughs`,
which is literally the product EW sells, the same as
`/10-creative-principal-for-the-day-ideas`, a school-spirit event listicle. Both
are posts. They are not worth the same, and no amount of correct arithmetic on
top of that grading recovers the distinction.

**Effort set by a multiplier keyed to the detector.** CTR anomaly 1.5, decay 1.0.
That is a guess wearing a number, and it then multiplied into a score presented
as a ranking.

## How to fill a judgment field

1. **Read the row's own data.** Position, impressions, trend, what the page is
   about, who searches for it, whether the client sells to those people.
2. **Decide, and be able to state why in one sentence** that references
   something specific to that row.
3. **Write the reasoning into the sheet**, not just the verdict. The rationale
   column is not decoration; it is what makes the verdict auditable.
4. **If the data does not support a decision, leave it blank and say so.**
   "Diagnose before refreshing: 77% fall suggests the query set moved rather
   than the page declining" is a real output. `Medium` is not.

## What may still be mechanical

Fetching, parsing, deduplicating, formatting, scope filtering, threshold
arithmetic and layout. Anything where the same input must always give the same
output. **The moment a field expresses an opinion about a client's business, it
stops being mechanical.**

A useful test before writing any cell: *could I defend this specific value, for
this specific row, to Roger, using something I actually read?* If the honest
answer is "it came out of the table", do not write it.

---

# Verify before you claim. No exceptions.

> Added 2026-08-17 after a fabricated projection reached a live client tab.

## The failure

Written into EW's 1.5 tab, rank 2:

> "Moving 6.0 to 4 recovers most of the lost 235 clicks."

Every part of that is unsupported. The page has **never ranked at position 4**
in the twelve months of history available, so there is no click figure for
position 4 to recover to. Its position has been flat at 5.9-6.7 all year and
actually *improved* between the two windows. The click fall was driven by
impressions dropping 42,366 to 25,864, which is Texas evaluation season, not a
ranking decline.

The number came from a generic CTR curve carried in the model's head and was
written as if it came from the client's data. One `searchanalytics` call by page
and month would have shown all of it. The data was already available.

That claim, unchallenged, would have justified a content refresh aimed at a
position gain that was never the problem, and the roadmap would have been built
on it.

## The gate

**Before any sentence that states or implies a fact about a client, run the
query that confirms it.** Not "it is probably true", not "this is the usual
pattern". Run it.

This applies with most force to:

- **Counterfactual projections.** "Moving to position N recovers X clicks"
  requires historical data showing the page HAS been at position N and what it
  earned there. No such history, no projection. State the current position and
  volume and stop.
- **Causal attributions.** "Clicks fell because rankings dropped" requires
  position data for both windows. Clicks can fall on flat rankings when demand
  falls, and that is a different problem with a different fix.
- **Any number that did not come out of a tool call in this session.**
- **Comparisons across time.** Seasonal businesses need the same months compared
  year over year before "decay" means anything. This applies to education as
  much as to HVAC: school calendars are seasons too, and EW's April impressions
  were double its July.

## How to write a claim

Every factual sentence in a deliverable must be traceable to a query run in this
session. If it cannot be, one of three things happens: run the query, remove the
sentence, or mark it explicitly as unverified with the reason.

**Say what the data shows, then stop.** "25,864 impressions at position 6.0,
clicks down 45% against a window containing the April evaluation-season peak" is
supportable and useful. Adding "and fixing it will recover 235 clicks" adds
nothing except risk, because nobody can check it and it will be believed.

When the data is genuinely ambiguous, say that. "Position is flat, so the fall
is demand-side, and without 2025 data I cannot separate seasonality from a real
decline" is a better output than a confident wrong number, and it tells the
reader exactly which query would settle it.
