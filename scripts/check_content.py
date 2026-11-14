#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "pyyaml",
# ]
# ///
"""
Sanity-check the site content before it is published.

Errors (exit status 1) are things that would break or silently corrupt a page:
  * a publication lists an author slug that has no profile in content/authors/
  * missing title / date / authors / publication type
  * a profile without first_name, last_name or user_groups
  * a post or event without title or date

Warnings (reported, exit status 0 unless --strict) are things to look at:
  * template placeholder text still on the site ("Lorem ipsum", "Wowchemy Research Group")
  * a profile in a group that the People page does not display
  * a publication without cite.bib or abstract

Usage:  uv run scripts/check_content.py [--strict]
"""

import argparse
import re
import sys
from pathlib import Path

import yaml

CONTENT = Path("content")
PUBLICATION_TYPES = {
    "paper-conference",
    "article-journal",
    "article",
    "book",
    "chapter",
    "thesis",
    "report",
}
PLACEHOLDERS = [
    "Lorem ipsum",
    "Wowchemy Research Group",
    "An example ",
    "Source Themes",
]
SLUG_RE = re.compile(r"^[a-z0-9]+(-[a-z0-9]+)*$")


def front_matter(path: Path) -> dict | None:
    text = path.read_text(encoding="utf-8")
    m = re.match(r"^---\s*\n(.*?)\n---\s*(\n|$)", text, re.DOTALL)
    if not m:
        return None
    try:
        return yaml.safe_load(m.group(1)) or {}
    except yaml.YAMLError as exc:
        raise ValueError(f"invalid YAML front matter: {exc}") from exc


def displayed_groups() -> set[str]:
    """User groups listed (uncommented) in the People page."""
    try:
        fm = front_matter(CONTENT / "people" / "index.md") or {}
        for section in fm.get("sections", []):
            if section.get("block") == "people":
                return set(section["content"].get("user_groups", []))
    except (OSError, ValueError, KeyError):
        pass
    return set()


def main() -> None:
    ap = argparse.ArgumentParser()
    ap.add_argument("--strict", action="store_true", help="Treat warnings as errors.")
    args = ap.parse_args()

    errors: list[str] = []
    warnings: list[str] = []

    def load(path: Path) -> dict:
        try:
            fm = front_matter(path)
        except ValueError as exc:
            errors.append(f"{path}: {exc}")
            return {}
        if fm is None:
            errors.append(f"{path}: no front matter (the file must start with '---')")
            return {}
        return fm

    # ---- Authors ---------------------------------------------------------
    groups = displayed_groups()
    author_slugs: set[str] = set()
    for index in sorted((CONTENT / "authors").glob("*/_index.md")):
        author_slugs.add(index.parent.name)
        fm = load(index)
        for key in ("first_name", "last_name"):
            if not str(fm.get(key) or "").strip():
                errors.append(f"{index}: '{key}' is empty")
        user_groups = fm.get("user_groups") or []
        if not user_groups:
            errors.append(
                f"{index}: 'user_groups' is empty, so the person would not appear on People"
            )
        elif groups and not set(user_groups) & groups:
            warnings.append(
                f"{index}: groups {user_groups} are not displayed on the People page "
                f"(shown: {sorted(groups)})"
            )

    # ---- Publications ----------------------------------------------------
    seen_dois: dict[str, Path] = {}
    for folder in sorted((CONTENT / "publication").glob("*/")):
        index = folder / "index.md"
        if not index.exists():
            errors.append(f"{folder}: no index.md")
            continue
        fm = load(index)
        if not str(fm.get("title") or "").strip():
            errors.append(f"{index}: missing title")
        if not fm.get("date"):
            errors.append(f"{index}: missing date")
        doi = re.sub(
            r"^(https?://(dx\.)?doi\.org/|doi:)",
            "",
            str(fm.get("doi") or ""),
            flags=re.IGNORECASE,
        ).lower()
        if doi and doi in seen_dois:
            errors.append(
                f"{index}: same DOI as {seen_dois[doi]} ({doi}); one of them is wrong"
            )
        elif doi:
            seen_dois[doi] = index
        types = fm.get("publication_types") or []
        if not types or not set(types) <= PUBLICATION_TYPES:
            errors.append(
                f"{index}: publication_types {types} must use {sorted(PUBLICATION_TYPES)}"
            )
        authors = fm.get("authors") or []
        if not authors:
            errors.append(f"{index}: no authors")
        for a in authors:
            a = str(a)
            if SLUG_RE.match(a) and a not in author_slugs:
                errors.append(
                    f"{index}: author '{a}' looks like a profile slug but content/authors/{a}/ does not exist"
                )
        if not (folder / "cite.bib").exists():
            warnings.append(f"{folder}: no cite.bib (the Cite button will be empty)")
        if not str(fm.get("abstract") or "").strip():
            warnings.append(f"{index}: empty abstract")

    # ---- Posts and events --------------------------------------------------
    for section in ("post", "event"):
        for path in sorted((CONTENT / section).rglob("*.md")):
            if path.name == "_index.md":
                continue
            fm = load(path)
            if not str(fm.get("title") or "").strip():
                errors.append(f"{path}: missing title")
            if not fm.get("date"):
                errors.append(f"{path}: missing date")

    # ---- Template leftovers ------------------------------------------------
    for path in sorted(CONTENT.rglob("*.md")):
        text = path.read_text(encoding="utf-8")
        for needle in PLACEHOLDERS:
            if needle in text:
                warnings.append(
                    f"{path}: still contains template text '{needle.strip()}'"
                )

    for w in warnings:
        print(f"WARNING  {w}")
    for e in errors:
        print(f"ERROR    {e}")
    print(f"\n{len(errors)} error(s), {len(warnings)} warning(s)")
    sys.exit(1 if errors or (args.strict and warnings) else 0)


if __name__ == "__main__":
    main()
