# Acceptance criteria — FitFindr

Five criteria that say what "working" means for this agent, written in unit 3
**before** any results existed.

An acceptance criterion names a target: a number, a count, a rate, or something
a person could plainly observe. *"The agent handles errors"* is an opinion.
*"When search returns nothing, the agent stops before calling the second tool,
in 5 of 5 tries"* is a criterion.

Under each one, write a sentence or two on **why that target** and not a
stricter one. A reason that says something about your tools, your loop, or the
data earns credit; *"80% seemed reasonable"* does not.

> Missing your own targets next unit costs you nothing. Setting a target so
> easy you can't miss it does.

**Two are written for you. You write three.**

---

## 1. A matching query completes all three tools

Given a query that matches at least one listing, the agent completes all three
tool calls and returns a fit card — in at least 4 of 5 tries.

**Why this target:** `search_listings` is a plain keyword-overlap match
against title, description, category, style_tags, colors, and brand — it has
no sense of synonyms. "Office-appropriate jacket" won't score any overlap
against `lst_018`'s actual tags (vintage, classic, linen, cottagecore,
minimal) even though a human would call a linen blazer office-appropriate.
On the five phrasings I actually tried (matching the exact or near-exact
wording of real listings) all five completed cleanly, but I'm leaving one of
five as slack for a phrasing that shares no vocabulary with anything in a
40-listing corpus — a keyword matcher's genuine failure mode, not a made-up
one.

---

## 2. An impossible query stops before the second tool

Given a query that matches no listings, the agent stops before calling
`suggest_outfit` and returns a message naming what to change — 5 of 5 tries.

**Why this target:** Unlike criterion 1, nothing here depends on the model
or on keyword luck — it's a plain `if not results:` branch in
`agent.py::run_agent` over whatever `search_listings` returned. Either the
code checks the list before calling the next tool or it doesn't; there's no
in-between result that would make 4 of 5 the honest target. I tested this
five times against `designer ballgown size XXS under $5` (which matches
nothing — no listing has an XXS token) and got 5 of 5 stops, zero model
calls each time.

---

## 3. The item search found is the same item the next tools receive

For 5 different queries that match at least one listing, `session
["selected_item"]["id"]` equals `session["search_results"][0]["id"]`
(confirmed by comparing the two, not by assuming it), and that same id's
title/price appear in the fit card's subject matter rather than some other
listing's — 5 of 5 tries.

**Why this target:** Like criterion 2, this isn't the model's behavior to be
unreliable about — it's Python passing one dict reference from
`session["selected_item"]` into `suggest_outfit()` and `create_fit_card()`.
I tested it directly rather than trusting the code: ran 5 different queries
through `run_agent` and compared `selected_item["id"]` against
`search_results[0]["id"]` by `is`/`==`, not by eyeballing the output, and
got a match on all 5. A state bug here (e.g. passing the wrong index, or a
copy that silently diverges) wouldn't look like a state bug from the
outside — it would look like `suggest_outfit` giving advice for the wrong
item — which is exactly why this needs its own criterion instead of folding
into criterion 1.

---

## 4. The fit card varies, but never drops the required facts

For 5 different items (cache off, so each is a real call), the 5 fit cards:
(a) share no identical opening sentence with each other, and (b) each
mention that item's price and platform at least once — 5 of 5 on both
counts.

**Why this target:** The wording is supposed to change run to run — that's
`TEMPERATURE=0.9` doing its job, not noise to tolerate. What I'd actually be
unhappy to see is the opposite failure: a template that produces the same
opening regardless of item (which would mean the prompt isn't really using
the item details), or a card that varies in style but drops the price or
platform it's supposed to name. I tested 5 items through the real pipeline
with caching off and got 5 distinct openings and 5/5 on mentioning both
price and platform, so 5 of 5 is what the system actually does, not an
aspirational number — if I see a collapsed template or a missing price next
unit, that's a real regression, not noise.

---

## 5. The price ceiling is never violated

For 5 different queries, each with a different `max_price`, every listing
`search_listings` returns has `price <= max_price` — 0 violations across all
results returned, not just the first one.

**Why this target:** Of everything the agent does, this is the one I'd be
least willing to ship wrong — a secondhand shopping tool that occasionally
shows someone a $75 jacket when they said "under $50" has failed at the one
job a price filter has. It's also a plain numeric comparison
(`listing["price"] > max_price`) with no model involved, so unlike criterion
1 there's no reason to leave slack. I tested 5 queries against 5 different
ceilings (20, 25, 30, 35, 50) and checked every returned listing, not just
the top one — 32 results total, 0 over their query's cap — and separately
checked the boundary case (`max_price` set exactly equal to a real listing's
price), which correctly included it, confirming "inclusive" in the spec is
actually inclusive in the code.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     UNIT 4 — read this before you change anything above.

     If a criterion turns out to be BROKEN rather than merely unmet, you can
     revise it, and that earns credit. But never delete or edit the original
     line. Add the revision underneath it, like this:

         ## 4. Something about the fit card

         The fit card is different every time.

         **Why this target:** ...

         > **Revised in unit 4:** For 5 different items, the 5 fit cards share
         > no opening sentence.
         >
         > **Why revised:** "different" wasn't checkable — two cards that
         > differed by one word still counted. The new version is something I
         > can actually score.

     That's a revision because the criterion couldn't be MEASURED.

     Lowering a target because you missed it is not a revision, and it costs
     you the point:

         ✗ "I said the empty search stops it 5 of 5 times, but I got 3 of 5,
            so 3 of 5 is more realistic."

     A number you missed stays where it is, gets diagnosed, and gets a fix
     attempted. That's where the points are.
     ───────────────────────────────────────────────────────────────────────── -->
