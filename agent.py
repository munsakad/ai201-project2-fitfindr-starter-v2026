"""
The FitFindr planning loop.

This is the file that makes FitFindr an agent rather than a script. It decides
which tool to run next based on what the last one returned.

If your loop calls all three tools no matter what comes back, you have a list
of function calls. A loop looks at the last result before it picks the next
step. **That branch is the graded part of this unit.**

Build and test your three tools in `tools.py` first. Then come here.

    python agent.py          runs both example paths below
"""

import re

import config
import trace
from mcp_client import call_tool, MCPError
from tools import suggest_outfit, create_fit_card
from generate import ModelUnavailable

# ── query parsing ───────────────────────────────────────────────────────────
#
# Regex, not the model — a query like "90s track jacket in size M" has its
# size and price sitting in predictable, literal phrases ("size X", "under
# $X"), so there's nothing for a model call to disambiguate. Spending an API
# call (and the rate-limit budget that comes with it) to parse something this
# mechanical would be solving the wrong problem.

_SIZE_RE = re.compile(r"\bsize\s+([A-Za-z0-9.]+)\b", re.IGNORECASE)
_PRICE_RE = re.compile(r"under\s*\$?\s*(\d+(?:\.\d+)?)", re.IGNORECASE)


def parse_query(query: str) -> dict:
    """
    Pull a description, a size, and a max_price out of a plain-language query.

    Returns {"description": str, "size": str | None, "max_price": float | None}.
    Whatever isn't matched by the size/price patterns becomes the description,
    fed to search_listings for keyword scoring.
    """
    size_match = _SIZE_RE.search(query)
    size = size_match.group(1) if size_match else None

    price_match = _PRICE_RE.search(query)
    max_price = float(price_match.group(1)) if price_match else None

    description = _SIZE_RE.sub("", query)
    description = _PRICE_RE.sub("", description)
    description = re.sub(r"\s+", " ", description).strip(" ,")

    return {"description": description, "size": size, "max_price": max_price}


# ── session state ─────────────────────────────────────────────────────────────

def new_session(query: str, wardrobe: dict) -> dict:
    """
    A fresh session for one user interaction.

    The session is the single source of truth for a run. Every tool result goes
    in here, and the next tool reads it back out.

    You could pass values straight from one call to the next. It would work,
    and you would not be able to test it — you can't print a variable you have
    already overwritten. Going through the session is what makes the state
    visible, and unit 4 has you write a criterion about exactly that.

    Add fields if you need them.
    """
    return {
        "query": query,              # what the user typed
        "parsed": {},                # description / size / max_price you pulled out of it
        "search_results": [],        # everything search_listings returned
        "selected_item": None,       # the one you chose — goes into suggest_outfit
        "wardrobe": wardrobe,        # the user's wardrobe
        "outfit_suggestion": None,   # what suggest_outfit returned
        "fit_card": None,            # what create_fit_card returned
        "error": None,               # set when the run ended early
    }


# ── planning loop ─────────────────────────────────────────────────────────────

def run_agent(query: str, wardrobe: dict) -> dict:
    """
    Run the loop once and return the finished session.

    Args:
        query:    what the user asked for, in plain language
                  (e.g. "vintage graphic tee under $30, size M").
        wardrobe: a wardrobe dict — get_example_wardrobe() or
                  get_empty_wardrobe() from utils/data_loader.py.

    Returns:
        The session dict. **Check session["error"] first** — if it isn't None,
        the run ended early and the later fields will still be None.

    ─────────────────────────────────────────────────────────────────────────
    TODO — build this, following the branch rule you wrote in Milestone 2.

      1. Start a session with new_session().

      2. Count the times round the loop, and call trace.check_iterations(count)
         on each one before you go again. It raises when the count passes
         MAX_ITERATIONS in config.py — see trace.py.

      3. Parse the query into a description, a size, and a max_price. Regex,
         string splitting, or asking the model are all fine — say which you
         chose in your README. Put the result in session["parsed"].

      4. Call search_listings() with what you parsed.
         Put the results in session["search_results"].

         ⚠️ THIS IS THE BRANCH. If nothing came back:
              - put a message in session["error"] saying what the user could
                change — "No results" is not that message
              - return the session
              - do NOT call suggest_outfit with nothing

      5. Choose an item — the first result is fine. Put it in
         session["selected_item"].

      6. Call suggest_outfit() with the selected item and the wardrobe.
         Put the result in session["outfit_suggestion"].

      7. Call create_fit_card() with the outfit and the item.
         Put the result in session["fit_card"].

      8. Return the session.

    ─────────────────────────────────────────────────────────────────────────
    IN UNIT 4 you come back and add two things:

      • Trace calls. One per step. `trace.step("search_listings", inputs=...,
        returned=...)` — see trace.py. Your README needs the output.

      • A handler for ModelUnavailable, so a bad key produces a message rather
        than a stack trace. The import is already at the top of this file.
    """
    session = new_session(query, wardrobe)
    iterations = 0

    # Step 1: parse the query, then search.
    iterations += 1
    trace.check_iterations(iterations)

    parsed = parse_query(query)
    session["parsed"] = parsed

    # search_listings runs behind MCP — the agent is a client now, not a
    # direct caller. The arguments and the return shape are unchanged; only
    # how the call gets there is different (see mcp_server.py, Milestone 1).
    search_args = {
        "description": parsed["description"],
        "size": parsed["size"],
        "max_price": parsed["max_price"],
    }
    try:
        results = call_tool("search_listings", search_args)
    except MCPError as exc:
        trace.step("search_listings (via MCP)", inputs=search_args, returned=None,
                   note="MCP call failed")
        session["error"] = (
            f"Couldn't reach the search tool over MCP: {exc}\n"
            f"Check that mcp_server.py runs on its own: python mcp_server.py"
        )
        return session

    session["search_results"] = results
    trace.step("search_listings (via MCP)", inputs=search_args, returned=results)

    # ⚠️ THE BRANCH. Nothing came back -> stop here, name what to change, and
    # never call suggest_outfit with an empty selection.
    if not results:
        constraints = []
        if parsed["size"]:
            constraints.append(f"size {parsed['size']}")
        if parsed["max_price"] is not None:
            constraints.append(f"under ${parsed['max_price']:.0f}")
        described = parsed["description"] or query
        where = f" in {' and '.join(constraints)}" if constraints else ""

        suggestions = ["different keywords"]
        if parsed["size"]:
            suggestions.append("a different size")
        if parsed["max_price"] is not None:
            suggestions.append("a higher price ceiling")

        session["error"] = (
            f"No listings matched '{described}'{where}. "
            f"Try {' or '.join(suggestions)}."
        )
        trace.step("branch", note="search_results empty -> stopping before suggest_outfit")
        return session

    # Step 2: pick an item, suggest an outfit.
    iterations += 1
    trace.check_iterations(iterations)

    session["selected_item"] = results[0]

    try:
        session["outfit_suggestion"] = suggest_outfit(session["selected_item"], wardrobe)
    except ModelUnavailable as exc:
        trace.step("suggest_outfit", inputs={"item": session["selected_item"].get("id")},
                   returned=None, note="model unavailable")
        session["error"] = f"Couldn't reach the styling model: {exc}"
        return session

    trace.step(
        "suggest_outfit",
        inputs={"item": session["selected_item"].get("id"), "wardrobe_items": len(wardrobe.get("items") or [])},
        returned=session["outfit_suggestion"],
    )

    # Step 3: write the caption.
    iterations += 1
    trace.check_iterations(iterations)

    try:
        session["fit_card"] = create_fit_card(
            session["outfit_suggestion"], session["selected_item"]
        )
    except ModelUnavailable as exc:
        trace.step("create_fit_card", inputs={"item": session["selected_item"].get("id")},
                   returned=None, note="model unavailable")
        session["error"] = f"Couldn't reach the captioning model: {exc}"
        return session

    trace.step(
        "create_fit_card",
        inputs={"item": session["selected_item"].get("id")},
        returned=session["fit_card"],
    )

    return session


# ── running it directly ───────────────────────────────────────────────────────

def _show(session: dict) -> None:
    if session["error"]:
        print(f"  stopped: {session['error']}")
        print(f"  fit_card is {session['fit_card']!r} — it should still be None here")
        return

    item = session["selected_item"] or {}
    print(f"  found:    {item.get('title')} — ${item.get('price')} on {item.get('platform')}")
    print(f"  outfit:   {session['outfit_suggestion']}")
    print(f"  fit card: {session['fit_card']}")


if __name__ == "__main__":
    from utils.data_loader import get_example_wardrobe

    print("=== A query the data can match ===")
    _show(run_agent(
        query="looking for a vintage graphic tee under $30",
        wardrobe=get_example_wardrobe(),
    ))

    print("\n=== A query it can't ===")
    _show(run_agent(
        query="designer ballgown size XXS under $5",
        wardrobe=get_example_wardrobe(),
    ))

    print(
        "\nThe second one should stop before the fit card. If both paths look "
        "the same,\nthe branch isn't doing anything yet."
    )
