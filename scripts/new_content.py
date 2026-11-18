#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = []
# ///
"""
Create a news post or an event page with valid front matter.

    uv run scripts/new_content.py post  "Title of the news" [--date 2026-11-14] [--author paolo-di-lorenzo]
    uv run scripts/new_content.py event "Seminar title" --date 2026-12-03 --location "Sapienza, Rome"

Creates content/post/<slug>/index.md or content/event/<slug>/index.md and prints the path.
Refuses to overwrite an existing page.
"""

import argparse
import datetime as dt
import json
import re
import sys
import unicodedata
from pathlib import Path


def slugify(text: str) -> str:
    text = unicodedata.normalize("NFKD", text).encode("ascii", "ignore").decode()
    return re.sub(r"-+", "-", re.sub(r"[^a-z0-9]+", "-", text.lower())).strip("-")[:80]


def q(value: str) -> str:
    return json.dumps(" ".join(value.split()), ensure_ascii=False)


def post(a: argparse.Namespace, iso: str) -> str:
    authors = "\n".join(f"  - {x}" for x in a.author) if a.author else "  - admin"
    return f"""---
title: {q(a.title)}
subtitle: ''
summary: {q(a.summary)}
date: '{iso}'
draft: false
featured: false
authors:
{authors}
tags: []
categories: []
projects: []
# Optional banner: put an image named `featured.jpg` in this folder.
image:
  caption: ''
  focal_point: ''
  preview_only: false
---

Write the news here (Markdown).
"""


def event(a: argparse.Namespace, iso: str) -> str:
    end = a.end_date or a.date
    authors = (
        "\n" + "\n".join(f"  - {x}" for x in a.author) if a.author else "[]"
    )
    return f"""---
title: {q(a.title)}
event: {q(a.event_name)}
event_url: ''
location: {q(a.location)}
address:
  street: ''
  city: ''
  region: ''
  postcode: ''
  country: ''
summary: {q(a.summary)}
abstract: ''
date: '{iso}'
date_end: '{end}T00:00:00Z'
all_day: true
publishDate: '{iso}'
authors: {authors}
tags: []
featured: false
url_code: ''
url_pdf: ''
url_slides: ''
url_video: ''
projects: []
---

Describe the event here (Markdown).
"""


def main() -> None:
    ap = argparse.ArgumentParser(
        description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter
    )
    ap.add_argument("kind", choices=["post", "event"])
    ap.add_argument("title")
    ap.add_argument(
        "--date",
        default=dt.date.today().isoformat(),
        help="YYYY-MM-DD (default: today)",
    )
    ap.add_argument("--end-date", help="events only, YYYY-MM-DD")
    ap.add_argument(
        "--author", action="append", help="author folder name; repeat for several"
    )
    ap.add_argument("--summary", default="")
    ap.add_argument("--location", default="")
    ap.add_argument("--event-name", default="")
    a = ap.parse_args()

    try:
        dt.date.fromisoformat(a.date)
        if a.end_date:
            dt.date.fromisoformat(a.end_date)
    except ValueError:
        sys.exit("Dates must look like 2026-11-14.")

    slug = slugify(a.title)
    if not slug:
        sys.exit("The title must contain letters or digits.")
    folder = Path("content") / a.kind / slug
    if folder.exists():
        sys.exit(f"{folder} already exists; pick another title or edit that page.")

    for author in a.author or []:
        if not (Path("content/authors") / author).is_dir():
            sys.exit(
                f"No profile 'content/authors/{author}'. Folder names look like 'paolo-di-lorenzo'."
            )

    iso = f"{a.date}T00:00:00Z"
    folder.mkdir(parents=True)
    (folder / "index.md").write_text(
        (post if a.kind == "post" else event)(a, iso), encoding="utf-8"
    )
    print(folder / "index.md")


if __name__ == "__main__":
    main()
