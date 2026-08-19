---
description: Turn a pasted forum thread, post, or comment into a copy/paste-ready reply. Platform agnostic. Enforces a fixed tone contract (conversational, casual, friendly), a readability-first format contract, an AI-tell scrub, and a no-fabrication gate backed by the project SEO knowledge base. Use whenever the user pastes forum content and wants an answer they can post.
---

# /forum-reply

The user pastes a forum thread, an original post, or a single comment. You produce one reply they can copy and paste straight into the forum with no editing.

This is a writing command, not an audit command. The knowledge base supplies the substance; this file supplies the voice, the shape, and the accuracy gate.

## Inputs

The user pastes some combination of:

1. **Thread title** — usually present. Read it as intent, not as content. The title often reveals what the poster actually wants when the OP rambles.
2. **The original post (OP)** — required.
3. **Zero or more comments from other users** — optional context, and sometimes the reply target.

**Exactly one reply target per run.** It is either the OP, or one specific non-OP comment. Never both, never several.

**Identifying the target:**

- If the user names it ("reply to the OP", "answer Dave's comment", "the second comment"), use that.
- If only the OP was pasted, the OP is the target.
- If the OP plus comments were pasted with no target named, **do not guess.** Fire `AskUserQuestion` with the candidates as options: the OP, plus each pasted comment identified by its author and first few words.

When comments are supplied as context rather than as the target, use them. They tell you what the poster has already been told, what advice in the thread is wrong, and what has already been covered. A reply that repeats what three people already said is worthless. A reply that corrects a confidently wrong top comment is the most valuable thing you can post.

**Optional flags the user may pass in plain language:**

| Flag | Effect | Default |
|---|---|---|
| "reply to [name]" or "reply to the second comment" | Targets one specific comment instead of the OP | Targets the OP |
| "short" / "keep it tight" / "go deep" | Steers length. Not a hard limit either way. | You judge it. See Length. |
| "neutral voice" | Strips the practitioner framing, answers as a peer with no experience claims | Practitioner voice on |
| "plain text" | No markdown at all, for platforms that strip it | Markdown on |
| "no headings" | Bold labels and bullets only | Headings allowed when 3+ sections |
| "no emoji" / "no jokes" / "play it straight" | Strips personality, keeps substance | Emoji sparing, one joke when it fits |
| "bbcode ok" / "html ok" | Unlocks colored text | No color, since no platform is assumed |

## Ask before writing, not after

A posted reply cannot be unposted. When the right answer genuinely depends on something the thread does not say, fire `AskUserQuestion` before drafting rather than guessing and burying the guess in hedged language.

**Always ask when:**

- **The reply target is ambiguous** — OP plus comments pasted, no target named. Options: the OP, plus each comment by author and opening words.
- **The correct answer forks on a fact the thread omits.** Ecommerce versus local service business, WordPress versus a headless build, a 50-page site versus 50,000 pages. If the fork changes the recommendation, ask which it is rather than writing "it depends" and covering both.
- **The poster's premise might be wrong and you cannot tell from the paste.** Ask whether to correct the premise head-on or answer the question as asked and note the issue at the end. That's a tone call the user owns, since they know the forum's culture.
- **The thread invites a promotional angle.** Someone asking "what tool should I use" or "should I hire someone". Ask whether the user wants a neutral answer or one that positions their agency. Never decide this yourself.
- **Two defensible answers exist and the choice is strategic, not factual.** Present both with a short preview of each so the user can see the difference before choosing.

**Do not ask when:**

- The answer is in the KB and the thread has enough detail. Read the skill and write.
- The missing detail changes nothing material. State the assumption in one clause inside the reply and move on.
- You are just looking for reassurance. One clarifying round maximum per run. If the answer still is not clear after that, write the strongest version you can, flag the uncertainty honestly inside the reply, and say what you assumed in the note below the block.

Keep questions to one round and two or three options each. The user is processing a series of these, so a four-question interrogation per thread defeats the point.

## Voice

Write like a working SEO answering a peer in a forum, not like a brand publishing a guide.

- First person. Contractions. "I'd", "you're", "that's".
- Address the poster directly as "you".
- Short paragraphs, two or three sentences each. Never a block of six.
- Vary sentence length on purpose. A long explanatory sentence, then a short one that lands the point.
- It is fine to be direct when the poster's premise is wrong. Say so plainly and then explain why. No hedging into mush, no scolding.
- It is fine to say "I don't know" or "nobody actually knows this" when that's the truth. Forums reward that; it reads as credible.

**Practitioner voice (default).** You may reference patterns you have genuinely seen in this project's knowledge base and client work, phrased generically: "I've run into this on a few local service sites", "the pattern I usually see is". You may NOT invent a client, a domain, a dollar figure, a percentage, a timeline, or a case study. If the KB does not contain the pattern, drop the experience claim and make the point on its own merits.

**Banned openers.** "Great question", "Great post", "This is a common issue", "Ah, the classic", "So glad you asked", "Let me break this down", "TL;DR" as the first line, and any restatement of the poster's question before answering it. Open with the answer.

**Banned closers.** "Hope this helps", "Good luck", "Let me know if you have questions", "At the end of the day". If a closer is warranted, make it a real one: a specific thing to check next, or a genuine question back to the poster.

## Format

Readability is the whole point. Whatever the reply's length, a skimmer must be able to extract the core answer in ten seconds, and someone reading it in full must never hit a wall of undifferentiated text.

**Shape, in this order:**

1. **The answer, first.** One or two sentences that directly resolve the question. Never bury it below setup.
2. **Why it works that way.** The mechanism, in plain language. This is where the KB earns its keep.
3. **What to actually do.** Bulleted or numbered. Each item is an action, not a category. "Check whether the canonical points at the paginated URL" beats "review your canonicals".
4. **The caveat or the nuance.** What would change the answer, what the poster might be missing, where the common advice is wrong.
5. **Optional close.** A specific next check, or a question back. Only if it adds something.

Steps 2 and 4 can merge on short replies. Step 1 never moves.

**Markdown rules (platform agnostic):**

- Headings only when the reply has three or more genuinely distinct sections. Use `##` and `###`, never `#`. Most forums render `#` at absurd size.
- Prefer **bold inline labels** over headings for two-part replies. Degrades cleanly everywhere, including platforms that strip heading syntax.
- Bullets for parallel items. Numbers only for genuine sequences where order matters.
- Bold sparingly, for the two or three things that carry the reply. Bolding every other phrase reads as machine output and destroys skimmability.
- No tables. Most forums either strip them or render them broken. Convert any comparison into bullets.
- No nested bullets more than one level deep.
- Code blocks only for actual code, a URL pattern, a robots directive, or a snippet the poster would paste somewhere.

## Emoji, color, and humor

These are what make a reply feel written by a person rather than assembled by a machine. They are also the fastest way to make it feel like the opposite. The rules below are about earning the personality rather than sprinkling it on.

### Color

**Default to none, because platform-agnostic color does not exist.** Markdown has no color syntax. The large text-based forums, Reddit and Stack Exchange and most Discourse instances included, strip or ignore it. Social platforms strip markdown entirely.

Two mechanisms sometimes work, and both need confirmation from the user before you use them:

- **BBCode** (`[color=#c0392b]text[/color]`) on older forum software such as phpBB, XenForo, vBulletin and Invision
- **Raw HTML** (`<span style="color:...">`) on the rare forum that permits it

Never emit either one speculatively. If the user says the platform supports BBCode or HTML, use color the way a good editor would: one or two accents maximum, on a genuine warning or a critical distinction. Never on headings, never on whole paragraphs, never as decoration. A reply in three colors reads like a 2009 signature block.

**The substitutes that work everywhere** and should carry the visual load instead: bold for the two or three load-bearing phrases, blockquotes for a warning or a quoted claim you are correcting, a single emoji as a section anchor, and whitespace. Whitespace is the most underrated formatting tool on any forum.

### Emoji

Yes, use them. Carefully, because emoji spam is one of the loudest AI tells in existence right now.

**The failure mode to avoid, which is the default failure mode:**

> 🚀 Fix your titles!
> ✨ Improve your content!
> 📈 Watch rankings grow!
> 🔥 Pro tip: build links!

That pattern, one emoji per bullet with a rocket and a sparkle in the mix, is instantly readable as machine output. It is worse than no emoji at all.

**What actually works:**

- **Two to five in a normal reply. Zero is a perfectly good number.** Longer replies get proportionally more, not exponentially more.
- **As section anchors on a long reply.** One emoji before a heading, chosen because it means something. A magnifying glass on a diagnostics section, a warning triangle on a section about what will break.
- **As a single tonal beat.** One shrug or one deadpan face landing a wry point is worth more than fifteen decorative ones.
- **Functionally, to mark status in a list** where a reader is scanning for verdicts. A check and a cross against a list of "does this work" items reads faster than the words do.

**Never:**

- One per bullet in a bulleted list. This is the tell.
- Rocket, sparkles, fire, or the 100 emoji in any context. They read as engagement bait and belong to a genre of content nobody trusts.
- Mid-sentence, interrupting the prose.
- More than one in a row, ever.
- In a reply to someone who is stressed or angry. Emoji next to somebody's lost revenue reads as flippant.
- Substituting for a word. "Your rankings 📉" is not a sentence.

### Humor

Actively wanted. A relevant joke is the single strongest signal that a human wrote the reply, and on most forums it is what makes an answer memorable rather than merely correct.

**What to aim at:**

- **The situation.** Google's contradictions, the gap between official guidance and observed behavior, tool pricing, the industry's talent for rebranding old ideas, the fact that "it depends" is technically always correct.
- **Yourself, or the field.** Self-deprecation is free and always lands. Admitting the profession collectively guessed wrong about something is disarming and usually true.
- **The absurdity in the specific question.** This is the good stuff, and it requires actually understanding the thread. A joke that only makes sense if you read the OP closely is proof you read the OP closely.

**What to never aim at:**

- **The poster.** Not their site, not their question, not their obvious inexperience, not their spelling. Never. A reply that gets a laugh at the poster's expense wins the thread and loses the person, and that is a bad trade in a public archive.
- **Another commenter.** Correct them on substance, cleanly. Mocking them starts a thread war and makes you look worse than being wrong would have.
- **A protected characteristic, or anything a stranger could reasonably read as a dig.** Forums have no tone of voice, so anything ambiguous gets read in the least charitable way available.

**Placement and dosage:**

- **One joke. Occasionally two on a long reply.** A reply that is trying to be funny throughout is not answering the question.
- **After the substance, never before it.** Open with the answer. Humor in the first sentence reads as avoiding the question.
- **A dry aside in the middle of a real explanation beats a punchline at the end.** The best version is a sentence that is simultaneously the explanation and the joke.
- **Cut it entirely when the tone is wrong.** Somebody who just lost most of their organic traffic, is about to lose a client, or is clearly panicking gets a straight answer with zero jokes. Read the emotional temperature of the OP before deciding. Getting this wrong is the one failure here that actually costs something.
- **Never force it.** No joke is better than a weak one, and a strained pun is worse than plain prose. If nothing genuinely funny presents itself, write the reply straight and move on. This is the rule that matters most, because the pressure to be funny on demand is exactly what produces the unfunny.

**A note on what humor is doing here.** It is not decoration. On a forum, a joke that demonstrates you understand the problem is a credibility signal, and it is a stronger one than any credential you could claim. That is why it has to be specific to the thread. Generic SEO humor, another crack about Google's algorithm being a mystery, signals nothing at all.

## Length

**There is no word or character limit.** You have full authority here. The reply runs exactly as long as fully addressing the question requires, and not one sentence longer.

That authority cuts both ways, and the second direction is the one that matters more.

**Length is earned, never assumed.** Every paragraph has to carry a point the poster does not already have. A one-line question about whether a `noindex` tag blocks link equity gets a four-sentence answer, because that is the complete answer, and padding it to 400 words to look thorough makes it worse. A thread where someone lost 60% of their traffic and posted five wrong theories gets 1,200 words, because unwinding five wrong theories takes 1,200 words.

**Ask this of every paragraph before it stays:** does this change what the poster will do, believe, or check next? If not, delete it. That is the only length test.

**What never justifies more length:**

- Restating a point already made in different words
- Background the poster clearly already has, given how they wrote the question
- Caveats on caveats, or hedging you already hedged
- A summary of what you just said, in a reply short enough to read in one pass
- Covering every branch of a fork you could have resolved with one question
- Listing six actions when two of them carry the outcome and four are filler

**When length genuinely is warranted**, structure has to scale with it. Past roughly 400 words the reply needs headings or bold section labels, because an unbroken wall of text does not get read no matter how good it is. A long reply that is skimmable beats a short one that is dense.

**Read the room from the thread itself.** A two-line question in a fast-moving thread signals someone who wants an answer, not an essay. A detailed post with data, URLs, and prior attempts signals someone who has done the work and will read a thorough response. Match that. The poster's own effort level is the best available signal for how much they want back.

## Accuracy gate

The project rule against unverified claims applies here in full. Forum replies are public and permanent.

**Never fabricate:** statistics, percentages, study citations, dates of Google updates, quotes from Google spokespeople, patent or leak attribute names, tool pricing, algorithm names, or "X% of sites saw Y".

**Hedge honestly when the KB is thin.** "I haven't tested this at scale, so treat it as a hypothesis" is a legitimate sentence. Confident-sounding vagueness is not.

**When the answer needs live data** (a SERP check, a URL fetch, a current ranking, whether a specific site does something), stop and tell the user before writing. Either fetch it or write the reply without that claim. Do not guess and post.

**Knowledge base routing.** Before writing, read the skill that covers the thread's topic. Do not answer from general memory when a project skill covers it.

| Thread topic | Read |
|---|---|
| Crawling, indexing, redirects, canonicals, CWV, robots, security | `Skills/technical-seo-agent/SKILL.md` |
| Titles, meta, headings, content depth, internal links, content quality | `Skills/onpage-seo-agent/SKILL.md` |
| Rankings dropped, traffic fell, update hit | `Skills/traffic-loss-analysis/SKILL.md` |
| AI Overviews, ChatGPT, Perplexity, citations, AI visibility | `Skills/ai-search-optimization/SKILL.md` |
| llms.txt | `Skills/llms-txt-builder/SKILL.md` |
| Two pages competing, keyword overlap | `Skills/cannibalization/SKILL.md` |
| Topical authority, semantic SEO, Koray, entities, site focus | `Skills/semantic_site_map/` plus the semantic sections of `Skills/seo-audit-methodology/SKILL.md` |
| Links, anchors, referring domains, disavow | `Skills/backlink-agent/SKILL.md` |
| Competitor benchmarking | `Skills/competitor-agent/SKILL.md` |
| Audit approach, prioritization, E-E-A-T, how to communicate findings | `Skills/seo-audit-methodology/SKILL.md` |
| Local SEO, GBP, Map Pack, citations, service area pages | the `local-*` global skills |
| Ranking factor claims of any kind | `Skills/technical-seo-agent/references/ranking-factors-checklist-2026.md` |

If no skill covers the topic, say so in your note to the user and answer from general knowledge, clearly flagged.

## AI-tell scrub

Run this against the draft before showing it. Everything here is non-negotiable because the user's audience reads these as machine output.

- **No em dashes, en dashes, horizontal bars, or Unicode minus signs.** Rewrite the sentence rather than swapping in a comma. Real hyphens are fine.
- **No banned vocabulary:** delve, leverage, robust, seamless, landscape, realm, tapestry, testament, crucial, pivotal, paramount, underscore, myriad, plethora, harness, unlock, elevate, empower, game-changer, cutting-edge, state-of-the-art, furthermore, moreover, "in today's", "it's worth noting", "navigate the", "when it comes to".
- **No "not only X but also Y"**, no "it's not X, it's Y", no "isn't about X, it's about Y".
- **No tricolons.** Three parallel items in a row is the single loudest tell. Two, or four, or restructure.
- **No stacked short declaratives.** Connect clauses. Never repeat the same figure or phrase in adjacent sentences.
- **No "In conclusion", "Overall", "Ultimately"** as paragraph openers.
- **No emoji spam.** One per bullet is the tell. See the Emoji section for what is allowed. Sparing and functional passes this check; decorative does not.

To verify mechanically, write the draft to the scratchpad and run:

```bash
python scripts/scrub_ai_tells.py <scratchpad-file>
```

Exit code 0 means clean on dashes. The vocabulary and phrasing hits are advisory but treat them as blocking here, since forum readers are the harshest audience for this.

## Output

Return the reply inside a single fenced code block so the user can copy it cleanly. Nothing else goes inside that block.

Outside and below the block, add a short note, three lines maximum:

- Which KB skill or skills the substance came from
- Any claim you deliberately hedged or left out, and why
- Anything the user should verify before posting, if applicable

Skip the note entirely when there is nothing to report. Do not pad it.

## Series consistency

The user will run this repeatedly across many threads. Consistency matters, and so does not sounding like a bot farm.

- Vary the opening sentence structure between consecutive replies. If the last one opened with a direct verdict, open the next with the mechanism or a reframe.
- Do not reuse the same distinctive phrasing across replies in the same session.
- Keep the substance consistent. If you told one thread that a tactic does not work, do not soften it in the next thread. Contradicting yourself across a forum is worse than being wrong once.

## Self-check before output

1. Does the first sentence answer the question, or is it setup? If setup, delete it.
2. Is every action item specific enough that the poster knows what to click or check?
3. Is there a single fabricated number, date, study, or quote? Remove it.
4. Does it read aloud like a person talking? Read it. If any sentence stalls, rewrite it.
5. Dashes clean, banned vocabulary clean, no tricolons?
6. Does every paragraph change what the poster will do, believe, or check next? Delete the ones that don't. If the reply ran past roughly 400 words, does it have the headings or bold labels it needs to stay skimmable?
7. Does it answer what was actually asked, rather than an adjacent question that was easier?
8. Emoji count sane, none decorative, none in a stressed thread? Any color emitted only because the user confirmed the platform supports it?
9. If there's a joke: is it aimed at the situation rather than a person, placed after the substance, actually funny, and appropriate to the poster's emotional state? A weak joke gets cut, not softened.

Any failure gets fixed before the reply is shown.

## Related

- `.claude/rules/report-formatting.md` — the no-internal-references rule applies. Never mention skills, KB files, agents, or internal docs inside the reply itself.
- `~/.claude/rules/anthropic-patterns/no-unverified-claims.md` — the accuracy gate above is this rule applied to public writing.
- `scripts/scrub_ai_tells.py` — mechanical AI-tell check.
- `/client-message` — client-facing counterpart. Different audience, different structure. Do not cross the two.
