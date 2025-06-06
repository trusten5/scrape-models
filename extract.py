"""parse_js_extract_name_slug.py

Walk through the raw JavaScript bundle (raw.js) and extract every unique
(name, slug) pair that shows up in any top-level object literal.

The original script filtered for a very specific set of fields, which meant we
missed most of the small snapshot definitions you care about.  In practice we
only need two keys – `name` and `slug` – so this rewrite takes a simpler,
streaming approach:

1.  It token-walks the file once, yielding every *top-level* `{ … }` block.  We
    reuse the original `_brace_blocks()` generator for this so we never load
    the whole file into memory twice.
2.  For each block we look for `name:"…"` *and* `slug:"…"` using a regex.  If
    both are found we add them to an ordered set so duplicates are collapsed
    but original ordering is preserved.
3.  Results are written to **model_slugs.txt** in CSV form (`name,slug`).  CSV
    makes it trivial to open in a spreadsheet or post-process further.

Run it exactly the same way:

    python parse_js_extract_name_slug.py

If you want a different output filename, just change `OUTPUT_FILE` below.
"""
from __future__ import annotations

import re
from collections import OrderedDict
from pathlib import Path
from typing import Iterable, Tuple

RAW_FILE = Path("raw.js")      # Input bundle
OUTPUT_FILE = Path("model_slugs.txt")  # Where we'll write "name,slug" lines

# ---------------------------------------------------------------------------
# The brace-matching generator from the earlier script (unchanged)
# ---------------------------------------------------------------------------

def _brace_blocks(text: str) -> Iterable[str]:
    """Yield every top-level `{ … }` block found in *text*."""
    start: int | None = None
    stack: list[str] = []
    in_string = False
    escape = False
    quote_char = ""

    for i, ch in enumerate(text):
        if in_string:
            if escape:
                escape = False
            elif ch == "\\":
                escape = True
            elif ch == quote_char:
                in_string = False
        else:
            if ch in ("'", '"'):
                in_string = True
                quote_char = ch
            elif ch == "{":
                if not stack:
                    start = i
                stack.append(ch)
            elif ch == "}":
                if stack:
                    stack.pop()
                    if not stack and start is not None:
                        yield text[start : i + 1]
                        start = None

# ---------------------------------------------------------------------------
# Core extraction logic
# ---------------------------------------------------------------------------

# Regex: name:"…", ... slug:"…"  (order-independent thanks to look-ahead)
NAME_SLUG_RE = re.compile(
    r"name\s*:\s*\"([^\"]+)\"(?:(?:(?!name|slug)[^{}])*)slug\s*:\s*\"([^\"]+)\"",
    re.DOTALL,
)
SLUG_NAME_RE = re.compile(
    r"slug\s*:\s*\"([^\"]+)\"(?:(?:(?!name|slug)[^{}])*)name\s*:\s*\"([^\"]+)\"",
    re.DOTALL,
)


def extract_name_slug(js_text: str) -> "OrderedDict[str, str]":
    """Return an *ordered* dict of {name: slug}.  Earlier occurrences win."""
    pairs: "OrderedDict[str, str]" = OrderedDict()

    for block in _brace_blocks(js_text):
        m = NAME_SLUG_RE.search(block) or SLUG_NAME_RE.search(block)
        if m:
            name, slug = m.groups()
            # If we matched SLUG_NAME_RE the order of groups is reversed
            if block[ m.start() : m.start() + 4 ] == "slug":
                slug, name = name, slug
            if name not in pairs:  # keep first occurrence (source order)
                pairs[name] = slug
    return pairs


def main() -> None:
    if not RAW_FILE.exists():
        raise SystemExit(f"❌ Could not find {RAW_FILE}. Put your JS file there or edit RAW_FILE.")

    print("Reading raw.js …")
    raw_text = RAW_FILE.read_text(encoding="utf-8", errors="replace")

    print("Extracting name/slug pairs …")
    pairs = extract_name_slug(raw_text)

    OUTPUT_FILE.write_text("\n".join(f"{n},{s}" for n, s in pairs.items()), encoding="utf-8")
    print(f"✅ Wrote {len(pairs)} unique models → {OUTPUT_FILE}")


if __name__ == "__main__":
    main()
