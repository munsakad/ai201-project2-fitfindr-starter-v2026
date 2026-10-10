# FitFindr

> ### 👋 Start here
>
> **New to this repo? Read [RUNNING.md](RUNNING.md) first** — setup, every
> command, and what to do when something breaks.
>
> Once `python test.py` passes:
>
> ```bash
> python app.py listings --full -n 6      # read the data (Milestone 1)
> python app.py fields                    # what you can filter on
> python app.py ask 'vintage graphic tee under $30'
> ```
>
> All three tools are stubs, so that last command will do nothing useful yet.
> That's the starting position.
>
> **The rest of this file is your submission.** Fill it in as you go.

---

<!-- ─────────────────────────────────────────────────────────────────────────
     HOW TO USE THIS FILE

     This is your submission. Fill each section in as you finish the milestone
     it belongs to — don't leave it all to the end.

     Unit 3 asks for the first five sections. Unit 4 adds the five below them.
     Leave the unit 4 sections alone until then; they're here so you know
     what's coming.

     Everything is pasted as TEXT. No screenshots, no images, no video links.
     A typed block of output gets full credit; a picture of the same output
     gets none.
     ───────────────────────────────────────────────────────────────────────── -->

<!-- ═══════════════════════ UNIT 3 — THE BUILD ═══════════════════════ -->

## What This Does

FitFindr is an agent over a 40-item mock thrift-listings dataset. A user
types a plain-language request — `vintage graphic tee under $30`, `90s
track jacket in size M` — and the agent searches the listings, picks the
best match, asks a model to suggest an outfit pairing it with the user's
saved wardrobe (or general styling advice if they haven't saved one), and
writes a short caption naming the item, its price, and the platform it's
on. If nothing in the data matches what was asked, it says so and names
what to change — size, price, or keywords — instead of calling the next
two tools with nothing to work from.

---

## Tool Inventory

<!-- Four lines per tool. This is worth 2 points and it's the single most
     common place students lose them.

     "Returns a list" earns NOTHING. The description has to say what is IN
     the list.

     The empty case isn't optional either — it's the thing your loop branches
     on, and if you don't decide it here you'll discover it as a crash in
     Milestone 5. -->

### `search_listings`

- **What it does:** Searches the 40 mock listings for keyword overlap with a
  description, optionally filtered to a size and a price ceiling.
- **Inputs:** `description` (str) — free-text keywords, e.g. `"vintage
  graphic tee"`. `size` (str | None) — a size token, e.g. `"M"` or `"8"`,
  matched against the listing's size string split into whole tokens
  (`"S/M"` → `{"S","M"}`), never a raw substring test — `"M" in "XL
  (oversized)"` would otherwise be true and wrong. `max_price` (float |
  None) — inclusive price ceiling; a listing priced exactly at the ceiling
  is included.
- **Returns:** `list[dict]`, best keyword-overlap match first (ties broken
  by lower price), each dict a full listing record — `id, title,
  description, category, style_tags, size, condition, price, colors,
  brand, platform` — at most `config.SEARCH_RESULT_LIMIT` (10) of them.
- **When it has nothing:** `[]` — an empty list, never `None`, never an
  exception. This is what `run_agent`'s branch checks.

### `suggest_outfit`

- **What it does:** Asks the model for 1-2 outfits combining a new item
  with the user's wardrobe, or general styling advice if the wardrobe has
  nothing in it.
- **Inputs:** `new_item` (dict) — a listing dict, as returned by
  `search_listings`. `wardrobe` (dict) — `{"items": list[dict]}`, each item
  dict holding `id, name, category, colors, style_tags, notes`. `items` may
  be `[]`.
- **Returns:** `str` — a non-empty, 2-4 sentence suggestion.
- **When it has nothing:** `wardrobe["items"] == []` → still returns a
  non-empty string, but general styling advice (category/color/silhouette
  guidance) rather than combinations with owned pieces that don't exist.
  Never raises, never returns `""`.

### `create_fit_card`

- **What it does:** Writes a short, postable caption for the item using the
  outfit suggestion as context.
- **Inputs:** `outfit` (str) — the string `suggest_outfit` returned.
  `new_item` (dict) — the listing dict.
- **Returns:** `str` — 2-4 sentences, naming the item, its price, and its
  platform once each.
- **When it has nothing:** `outfit` is empty or whitespace-only → returns a
  plain descriptive fallback (`"Found {title} (${price} on {platform}), but
  there's no outfit suggestion yet to build a caption from."`) with **no
  model call**, rather than raising or sending the model an empty prompt.

---

## Planning Loop

<!-- Your branch rule, stated as a rule — the condition AND both paths — plus
     the file and function that holds it.

     Like this:
       "If search_listings returns an empty list, put a message in the session
        and stop. Otherwise take the first result and go to suggest_outfit."
        — agent.py::run_agent

     The grader checks your code against what you claim here, so the file and
     function have to be real. -->

**Branch rule:** If `search_listings` returns an empty list, put a message
in `session["error"]` naming what to change (size, price, or keywords) and
stop — `suggest_outfit` and `create_fit_card` are never called. Otherwise,
take `search_results[0]` as `selected_item` and continue to `suggest_outfit`,
then `create_fit_card`.

**Where it lives:** `agent.py::run_agent`

**How the query is parsed:** Regex, in `agent.py::parse_query`. One pattern
(`\bsize\s+([A-Za-z0-9.]+)\b`) pulls out an explicit size, another
(`under\s*\$?\s*(\d+(?:\.\d+)?)`) pulls out a price ceiling, and whatever's
left after both are stripped out becomes the description handed to
`search_listings`. I used regex rather than a model call because both
patterns are literal phrases the example queries always use ("size X",
"under $X") — there's no ambiguity for a model to resolve, and spending an
API call (and rate-limit budget) on something this mechanical would be
solving a problem that isn't there.

**What moves through the session:** `query` → `parsed` (description, size,
max_price) → `search_results` → `selected_item` (first of `search_results`)
→ `outfit_suggestion` → `fit_card`, in that order. `error` is set instead
and the run returns early if `search_results` comes back empty.

---

## Sample Run

<!-- Two things go here.

     1. One FULL query and its output, pasted as text.
     2. Your three per-tool terminal tests — the command and what it printed. -->

**One full query**

```
$ python app.py ask 'vintage graphic tee under $30'

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair your new Y2K butterfly baby tee with the baggy straight-leg dark wash jeans and chunky white sneakers for an effortless off-duty streetwear look, layering the black cropped zip hoodie on top if it gets chilly. Alternatively, lean into a retro-casual vibe by tucking the tee into the wide-leg khaki trousers, cinched with the brown leather belt, and finished off with your favorite black crossbody bag.

  Fit card: Found this literal dream butterfly baby tee on depop and my inner 2004 self is screaming. It was only $18.0 and honestly, the fit is so nostalgic with low-rise denim and beat-up sneakers. Can't wait to wear this all through festival season!

2 model calls this session, 540 prompt + 145 output tokens
```

And the empty-search branch, for contrast:

```
$ python app.py ask 'designer ballgown size XXS under $5'

  No listings matched 'designer ballgown' in size XXS and under $5. Try different keywords or a different size or a higher price ceiling.

0 model calls this session
```

**The three tools, tested one at a time**

```
$ python -c "from tools import search_listings; print(search_listings('graphic tee', max_price=30))"
[{'id': 'lst_017', 'title': 'Mesh Long-Sleeve Top — Black', ... 'price': 15.0, ...}, {'id': 'lst_002', 'title': 'Y2K Baby Tee — Butterfly Print', ... 'price': 18.0, ...}, {'id': 'lst_033', 'title': 'Vintage Band Tee — Faded Grey', ... 'price': 19.0, ...}, {'id': 'lst_006', 'title': 'Graphic Tee — 2003 Tour Bootleg Style', ... 'price': 24.0, ...}, {'id': 'lst_015', 'title': 'Vintage Graphic Hoodie — Faded Black', ... 'price': 26.0, ...}, {'id': 'lst_011', 'title': 'Low-Rise Cargo Pants — Khaki', ... 'price': 27.0, ...}]
```

Worth noting honestly: the top result here is a mesh top, not a tee — its
*description* happens to contain the literal phrase "graphic tee" ("great
for layering under a graphic tee"), which ties it with the actual graphic
tees on keyword overlap, and it wins the tiebreak on price ($15). That's a
real, visible limit of keyword-only scoring — it matches on word
co-occurrence, not on what the item actually is — which is exactly the kind
of miss criterion 1's "4 of 5, not 5 of 5" is there to allow for.

```
$ python -c "from tools import suggest_outfit; from utils.data_loader import get_example_wardrobe, load_listings; print(suggest_outfit(load_listings()[0], get_example_wardrobe()))"
Pair your new Levi's with the white ribbed tank top and oversized grey crewneck sweatshirt, layered with the black combat boots and black crossbody bag for an effortless, cozy streetwear look. Alternatively, go for a classic double-denim moment by tucking the white ribbed tank into the jeans, adding the brown leather belt, and throwing on the vintage black denim jacket and chunky white sneakers.
```

```
$ python -c "from tools import create_fit_card; from utils.data_loader import load_listings; print(create_fit_card('jeans and white sneakers', load_listings()[0]))"
Score these vintage Levi's 501 jeans on Depop for just $38.0 and honestly they fit like a absolute dream. They've got that perfectly worn-in medium wash that gives off total effortless streetwear energy. Just threw them on with crisp white sneakers and I'm never taking them off.
```

---

## How I Used AI

<!-- Two specific moments. What you asked, what came back, what you changed.

     "I used Claude to help me code" is not enough.

     "I gave Claude my search_listings spec. It returned None on no match
     instead of an empty list, so I changed it" is the level we want. -->

<!-- REVIEW BEFORE SUBMITTING: these describe what actually happened in this
     session. Edit them to reflect your own review before submitting — this
     section is graded as your own account. -->

**Moment 1**

- *What I asked for:* A size-matching approach for `search_listings` that
  wouldn't fall into the substring trap the spec warns about (`"S" in "US
  9"` is `True` and wrong).
- *What came back:* A token-based matcher — split both the query size and
  the listing's size string into alphanumeric tokens and check for exact
  membership (`"S/M"` → `{"S","M"}`), rather than any substring test.
- *What I changed:* Nothing structurally, but I didn't take it on faith —
  I ran it against the actual sizes in the data (`"US 8.5"` vs query `"8"`,
  `"XL (oversized)"` vs query `"M"`) to confirm it correctly rejected the
  near-miss cases before using it in `search_listings`.

**Moment 2**

- *What I asked for:* Help figuring out why three `create_fit_card` calls on
  the same item came back word-for-word identical, per the Milestone 4
  warning that it's one of two settings in `config.py`.
- *What came back:* Since `TEMPERATURE` was already `0.9`, not `0`, the
  explanation had to be the cache — identical `(prompt, system, temperature)`
  triples return the stored answer on repeat calls.
- *What changed:* I re-ran the same test with `AI201_CACHE=0` to confirm —
  three real calls, three genuinely different captions — before writing
  criterion 4 around the real (non-cached) behavior rather than what three
  identical cached strings would have suggested.

**Moment 3 (unit 4)** — All five criteria passed cleanly on the first
`run_eval.py --label before` run, so I asked Claude to help find a failure
my five scenarios wouldn't catch, since the milestone explicitly warns that
a clean sweep usually means safe targets rather than an excellent agent. It
proposed testing an ordinary conversational size phrasing ("a size that
fits loose") on the theory that the regex-based parser might assume the
word right after "size" is always a real size value. That theory was
right — it broke a real, findable match. I verified the failure myself
(parsed the query, then separately confirmed by hand that `lst_011` really
does match on keywords and price) before accepting it as a genuine bug
rather than an edge case not worth fixing.

**Moment 4 (unit 4)** — Before accepting the regex fix, I asked what the
allowlist approach might still miss. It named two things: phrasings outside
the allowed shapes (e.g. "petite," "runs big") and the fact that the fix
is specific to this dataset's actual size vocabulary rather than a general
solution. Both are in What's Still Broken because I checked them against
`data/listings.json` myself and agreed they were real gaps, not because
they were handed to me — I decided the first was acceptable (fails open to
no size filter, which is safe) and the second was out of scope for a
one-line fix tied to a specific diagnosis.

<!-- ═══════════════════════ UNIT 4 — THE TEST ═══════════════════════

     Don't fill these in during unit 3.
     ═══════════════════════════════════════════════════════════════════ -->

---

## Run Log — Before

Produced by `python run_eval.py --label before` (`agent.py::run_agent`,
scenarios in `scenarios.py`), full transcript in
[`results/run_2026-10-10_1158_before.md`](results/run_2026-10-10_1158_before.md).
50 real model calls, cache off. Each row is one scenario from `scenarios.py`,
run 5 separate times.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Item search found reaches the next tools unchanged | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card varies, never drops price/platform | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price ceiling never violated | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

**Real output from one try**, criterion 3 (`agent.py::run_agent`, state
flowing into `tools.py::suggest_outfit` / `tools.py::create_fit_card`),
query `90s track jacket in size M`, try 1:

```
- selected_item: 90s Track Jacket — Navy/White Stripe ($45.0, poshmark)
- search_results: 4

Fit card:
Scored this crispy navy and white 90s track jacket on Poshmark for just $45 and I'm obsessed with the retro athletic energy. Going straight into heavy rotation with baggy denim and chunky sneakers for the ultimate off-duty look. Best thrift win all week!
```

Same item (`90s Track Jacket`, $45, poshmark) named correctly in all 5
tries — the fit card never drifted to a different listing than the one
`search_results[0]` actually returned.

**Real output**, criterion 5 (`tools.py::search_listings`, called via MCP),
query `vintage under $20`, all 7 results across all 5 tries:

```
Leather Belt — Brown, Braided ($12.0), Bucket Hat — Reversible, Brown Plaid ($14.0),
Henley Long Sleeve — Washed Burgundy ($16.0), Y2K Baby Tee — Butterfly Print ($18.0),
Vintage Polo Shirt — Forest Green ($18.0), Vintage Band Tee — Faded Grey ($19.0),
Oversized Crewneck Sweatshirt — Vintage Navy ($20.0)
```

All 7 at or under $20 — including the $20.00 item, confirming `max_price`
is inclusive as specified. 0 violations across 5 tries.

---

## Verdicts and Diagnoses

<!-- MET or MISSED per criterion against LAST UNIT's target, plus a sentence on
     how you decided.

     Then, for every miss: which of the four places it happened — a tool, the
     loop's branch, the session, or the model's output — AND the mechanism.

     Not a diagnosis:  "The fit card was bad."
     A diagnosis:      "The fit card criterion missed on 2 of 5 items. Both had
                        an empty brand field. My prompt puts the brand in the
                        first sentence, so the card opened with a blank and read
                        like a fragment. The tool worked; the prompt assumed a
                        field that isn't always there."

     Look for a pattern. Three misses on the same tool is one problem, not
     three. -->

| # | Criterion | Target | Verdict | How I decided |
|---|---|---|---|---|
| 1 | Matching query completes all three tools | 4 of 5 | MET | 5/5. `vintage graphic tee under $30` produced a full fit card in all 5 real tries. |
| 2 | Impossible query stops before tool 2 | 5 of 5 | MET | 5/5. `designer ballgown size XXS under $5` stopped at the branch every time, 0 model calls. |
| 3 | Item search found reaches the next tools unchanged | 5 of 5 | MET | 5/5. All 5 tries selected the same item (`90s Track Jacket`, id `lst_004`) and every outfit/fit card discussed that exact item, never a different one. |
| 4 | Fit card varies, never drops price/platform | 5 of 5 | MET | 5/5 on both halves. 5 real calls on the same item produced 5 different opening sentences, and every card named the $30 price and Depop at least once. |
| 5 | Price ceiling never violated | 5 of 5 | MET | 5/5. Checked all 7 returned listings each try, not just the top one — 0 over the $20 cap in any try, all 5 identical since `search_listings` has no randomness. |

**Diagnoses**

I missed nothing against my own five criteria. That's the signal the
milestone warns about — a target that's cleared with this much room
(0/50 real tries failed) is more likely a safe target than an excellent
agent, so before calling this unit done I went looking for a question my
five scenarios don't ask.

I found one, in `agent.py::parse_query` — the regex-based query parser,
not one of the three tools. The size pattern was originally
`\bsize\s+([A-Za-z0-9.]+)\b`: whatever single word follows the literal word
"size" gets treated as the requested size, no matter what that word is.
`"90s track jacket in size M"` works fine. But a completely ordinary
phrasing — **`"low-rise cargo pants in a size that fits loose"`** — parses
`size` as `"that"`, because "that" is the word right after "size" and the
old pattern didn't check whether it looked like an actual size. That gets
passed to `search_listings` as `size="that"`, which matches no listing's
size tokens, so the agent reported **"No listings matched... in size
that"** for a query the data can clearly answer (`lst_011`, Low-Rise Cargo
Pants, `W29`, exists and should have been found).

**Where this sits in the four places things can go wrong:** not a tool —
`search_listings` did exactly what it promises with the input it was
given. Not the branch — the branch correctly stopped on an empty list; the
list was wrong, not the branch's response to it. Not the session or the
model. It's upstream of all four: the query-parsing step that feeds the
first tool made an assumption (the word after "size" is always a size)
that was never tested against ordinary conversational phrasing, only
against the clean "size M" / "size 8" style of my own five scenarios and
the starter's own example queries.

That's the pattern worth naming honestly: every one of my scenarios writes
"size" immediately followed by an actual size token, because I wrote them
to test the agent's branches and tools, not to adversarially test my own
parser. A criterion written to probe the parser itself would have caught
this; none of mine did.

---

## Loop Trace

<!-- One full run, printed step by step, with the MCP call visible in it.

     `python app.py ask '...' --trace` once you've added the trace.step()
     calls in Milestone 2.

     Worth pasting BOTH the happy path and the empty-search path. The empty
     one should be visibly shorter, because it stops. If your two traces are
     the same length, your branch isn't working — and this is the fastest way
     anyone will ever find that out. -->

**Happy path**

```
$ python app.py ask 'vintage graphic tee under $30' --trace

[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: 10 items: Y2K Baby Tee — Butterfly Print, Vintage Band Tee — Faded Grey, Graphic Tee — 2003 Tour Bootleg Style … +7 more
[2] suggest_outfit
      in:  dict with keys: item, wardrobe_items
      out: Pair the butterfly baby tee with your baggy straight-leg dark wash jeans and chunky white sneakers for an effo…
[3] create_fit_card
      in:  dict with keys: item
      out: Found this absolute gem on depop for only $18.0 and I am so obsessed with the little butterfly graphic. It's g…

  Found:    Y2K Baby Tee — Butterfly Print — $18.0 on depop

  Outfit:   Pair the butterfly baby tee with your baggy straight-leg dark wash jeans and chunky white sneakers for an effortless Y2K streetwear vibe. Layer the black cropped zip hoodie loosely over top and finish the look with your black crossbody bag.

  Fit card: Found this absolute gem on depop for only $18.0 and I am so obsessed with the little butterfly graphic. It's giving major early 2000s mall rat energy, especially paired with some baggy dark denim. Can't wait to live in this all summer!

2 model calls this session, 502 prompt + 106 output tokens
```

**Empty search**

```
$ python app.py ask 'designer ballgown size XXS under $5' --trace

[1] search_listings (via MCP)
      in:  dict with keys: description, size, max_price
      out: [] (empty)
[2] branch
      →    search_results empty -> stopping before suggest_outfit

  No listings matched 'designer ballgown' in size XXS and under $5. Try different keywords or a different size or a higher price ceiling.

0 model calls this session
```

Three steps vs. two — the empty-search path is visibly shorter because it
stops before `suggest_outfit` and `create_fit_card` ever run, and makes
zero model calls.

**On the MCP move:** `search_listings` is now registered as an MCP tool in
`mcp_server.py` with a typed, published description (inputs, units,
matching rules, and the empty case spelled out for a reader who can't see
`tools.py`). `agent.py::run_agent` no longer imports `search_listings`
directly — it calls `mcp_client.call_tool("search_listings", {...})`,
which starts the server over stdio, makes the call, and shuts it down
again. The return shape did not change (still a `list[dict]` of the same
listing records), which is the thing the spec says to check — I confirmed
it by diffing the MCP-routed output against the direct-call output for the
same query before trusting the swap. The only behavioral difference is
latency: each `search_listings` call now starts a subprocess, so a run
through MCP takes noticeably longer than the direct call did, which is the
expected cost of the trade-off `mcp_client.py`'s docstring names
("slower... and much easier to reason about").


---

## The Improvement

<!-- What you changed, why your diagnosis pointed at it, and the after-run in
     the same table format. One change, measured properly.

     `python run_eval.py --label after` -->

**What I changed:** `agent.py::parse_query`'s `_SIZE_RE`. Before:
`\bsize\s+([A-Za-z0-9.]+)\b` — any single word after "size" becomes the
size filter. After: the captured group is restricted to an explicit list of
shapes that actually look like sizes — `XS/S/M/L/XL` and their doubled
forms, the slash combinations in the data (`S/M`, `M/L`, `L/XL`), a bare
1-2 digit number with an optional decimal (`7`, `8`, `8.5`), or a waist
size (`W28`). Nothing else. Everything downstream (`search_listings`,
`suggest_outfit`, `create_fit_card`, the MCP registration) is unchanged.

**Which failure it was meant to fix:** The parsing bug from Diagnoses —
`"a size that fits loose"` capturing `"that"` as the size and wrongly
emptying out a real match.

### Run Log — After

Produced the same way, `python run_eval.py --label after`, full transcript
in [`results/run_2026-10-10_1204_after.md`](results/run_2026-10-10_1204_after.md).
51 model calls, cache off.

| Criterion | Target | Try 1 | Try 2 | Try 3 | Try 4 | Try 5 | Verdict |
|---|---|---|---|---|---|---|---|
| 1. Matching query completes all three tools | 4 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 2. Impossible query stops before tool 2 | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 3. Item search found reaches the next tools unchanged | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 4. Fit card varies, never drops price/platform | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |
| 5. Price ceiling never violated | 5 of 5 | PASS | PASS | PASS | PASS | PASS | MET (5/5) |

Identical to the before table — none of my five scenarios ever exercised
the broken regex path (they all write "size" immediately followed by a
real size token), so this run log can't show the fix. The real evidence is
the scenario the criteria never asked for:

```
Query: "low-rise cargo pants in a size that fits loose"

Before: parsed as {'description': 'low-rise cargo pants in a fits loose', 'size': 'that', 'max_price': None}
        -> 0 results -> "No listings matched 'low-rise cargo pants in a fits loose' in size that."
        (WRONG — lst_011, Low-Rise Cargo Pants, W29, exists and matches)

After:  parsed as {'description': 'low-rise cargo pants in a size that fits loose', 'size': None, 'max_price': None}
        -> 10 results, top match: Low-Rise Cargo Pants — Khaki ($27.0, poshmark)
        -> real outfit suggestion and fit card produced
        (CORRECT)
```

**Did it help, and how do I know:** Yes, for the failure it targeted —
confirmed by the before/after pair above, which I re-ran after the change
rather than assumed. I also reran every size-bearing query used elsewhere
in this README (`size M`, `size 8`, `size W28`, `size XXS`) to check the
tighter pattern didn't narrow things too far — all four still parse their
size correctly:

```
'90s track jacket in size M'              -> size: 'M'
'platform sneakers size 8'                -> size: '8'
'70s corduroy pants in size W28'          -> size: 'W28'
'designer ballgown size XXS under $5'     -> size: 'XXS'
```

Cost-wise this change is free: it touches only the parsing regex, makes no
additional model calls, and the before/after token totals (12,054 vs
12,095 prompt+output tokens across 50-51 calls) are within the normal
run-to-run variance of fit-card length, not a result of the fix itself.


---

## What's Still Broken

No criterion is missed, so this is about what the fix doesn't cover rather
than a graded miss.

**The size regex is a tighter allowlist, not a real understanding of
sizes.** It now rejects obvious non-sizes like "that," but it's still a
fixed list of shapes (letter sizes, `S/M`-style combinations, 1-2 digit
numbers, `W`+digits) matched against whatever word follows the literal
word "size." A real size phrasing outside that list — "a petite," "runs
big," or a shoe size written as "size 8 wide" — either gets rejected
(falls back to no size filter, which fails safe) or could still be
misparsed if it happens to match one of the allowed shapes. I stopped here
because the allowlist covers every size format that actually appears in
`data/listings.json`, which is what the agent needs to work correctly
against this dataset; making it understand sizes in general is a different,
larger problem (closer to the model-based parsing the spec explicitly
says isn't needed for *this* dataset) and not what my diagnosis pointed at.

**The MCP call starts a fresh server subprocess every time.** That's the
documented, intentional trade-off in `mcp_client.py`, not a bug, but it
means every query is slower than it was with a direct call, and that cost
is paid on every single run, not just ones that need it — the same shape
of trade-off as unit 3's `TOP_K` fix in the other project. I didn't treat
this as something to fix, since the spec is explicit that a held-open
connection is out of scope for one unit, but it's the honest cost of this
unit's required move.



<!-- ═════════════════════════════════════════════════════════════════════

     SUBMISSION CHECKLIST — unit 3

       [ ] criteria.md has five numbered criteria, each with a target
       [ ] Each criterion has a reason underneath it
       [ ] All five unit 3 sections above have real content
       [ ] Tool Inventory: all three tools, inputs WITH TYPES, a specific
           return value, and the empty case
       [ ] Planning Loop names the branch rule and agent.py::run_agent
       [ ] Sample Run: one full query plus the three per-tool tests, as text
       [ ] At least four new commits
       [ ] Repository URL submitted — WRITE IT DOWN, you submit the same one
           next unit

     SUBMISSION CHECKLIST — unit 4

       [ ] mcp_server.py exists with one tool registered
           (or a written record of exactly where the rewire broke)
       [ ] Run Log — Before, five criteria, five tries each
       [ ] Real output pasted underneath, naming file and function
       [ ] A verdict on every criterion
       [ ] A diagnosis for every miss, naming a place AND a mechanism
       [ ] Loop Trace, with the MCP call visible in it
       [ ] All three failure modes triggered and handled
       [ ] One improvement, with Run Log — After in the same format
       [ ] What's Still Broken
       [ ] At least four new commits
       [ ] The SAME repository URL as last unit

     Do not delete and recreate this repository. Your commit history is what
     shows your criteria existed before your results did.
     ═════════════════════════════════════════════════════════════════════ -->

---

📖 **How to run this project: [RUNNING.md](RUNNING.md)**
