#!/usr/bin/env python3
# /// script
# requires-python = ">=3.11"
# dependencies = [
#     "jinja2",
#     "polars",
#     "requests",
# ]
# ///

# Add root to the path
import sys
from pathlib import Path

sys.path.append(str(Path(sys.path[0]).parent))

import argparse
import os
import re
import unicodedata

import polars as pl
from jinja2 import Template

from src.download_utils import download_sheet_as_csv

# -------------------------------------------------
# CONFIG
# -------------------------------------------------
# Set these as environment variables (see `.env.example`), or as GitHub
# repository *variables* (Settings > Secrets and variables > Actions > Variables).

# Google Sheet ID (the long identifier in the sheet URL).
SHEET_ID = os.environ.get("SPAICOM_SHEET_ID", "")

# GID of the "people" tab (the number after `gid=` in the tab URL).
GID = int(os.environ.get("SPAICOM_PEOPLE_GID", "0"))

# Columns that must exist and be non-empty for every row.
REQUIRED_COLUMNS = ["first_name", "last_name", "user_groups"]

# Columns the template reads; missing ones only produce a warning.
TEMPLATE_COLUMNS = [
    "role",
    "org_name",
    "org_url",
    "short_bio",
    "long_bio",
    "interests",
    "education",
    "email",
    "email_for_gravatar",
    "linkedin",
    "github",
    "scholar",
    "superuser",
    "highlight_name",
]

# Markdown template file
TEMPLATE_FILE = Path("templates/people.md")

# Output folder for generated .md files
OUTPUT_DIR = Path("content/authors")


# -------------------------------------------------
# Helper functions
# -------------------------------------------------
def slugify_author_name(name: str) -> str:
    # Normalize unicode → remove accents (Diàcrítics → Diacritics)
    name = unicodedata.normalize("NFKD", name)
    name = name.encode("ascii", "ignore").decode("ascii")

    # Lowercase
    name = name.lower()

    # Replace apostrophes and spaces with hyphens
    name = re.sub(r"[ '\t]+", "-", name)

    # Remove any character that is not alphanumeric or hyphen
    name = re.sub(r"[^a-z0-9-]+", "", name)

    # Collapse multiple hyphens
    name = re.sub(r"-+", "-", name)

    # Remove leading/trailing hyphens
    name = name.strip("-")

    return name


def validate(df: pl.DataFrame) -> list[str]:
    """Return a list of human-readable problems (empty list = all good)."""
    errors = []

    missing = [c for c in REQUIRED_COLUMNS if c not in df.columns]
    if missing:
        errors.append(f"Missing required column(s) in the sheet: {', '.join(missing)}")
        return errors

    for c in TEMPLATE_COLUMNS:
        if c not in df.columns:
            print(
                f"WARNING: column '{c}' not found in the sheet; it will render empty."
            )

    seen: dict[str, int] = {}
    for i, row in enumerate(df.to_dicts(), start=2):  # row 1 is the header
        first = (row.get("first_name") or "").strip()
        last = (row.get("last_name") or "").strip()
        if not first or not last:
            errors.append(
                f"Sheet row {i}: first_name and last_name must both be filled."
            )
            continue
        if not (row.get("user_groups") or "").strip():
            errors.append(f"Sheet row {i} ({first} {last}): user_groups is empty.")
        slug = slugify_author_name(f"{first} {last}")
        if slug in seen:
            errors.append(
                f"Sheet rows {seen[slug]} and {i}: both produce the author folder '{slug}'."
            )
        seen[slug] = i
    return errors


# -------------------------------------------------
# Main process
# -------------------------------------------------


def main():
    parser = argparse.ArgumentParser(
        description="Generate content/authors/* from the Google Sheet."
    )
    parser.add_argument(
        "--csv",
        type=Path,
        help="Read the people table from a local CSV instead of downloading it (testing).",
    )
    parser.add_argument(
        "--output-dir",
        type=Path,
        default=OUTPUT_DIR,
        help="Where to write the author folders (default: content/authors).",
    )
    parser.add_argument(
        "--check",
        action="store_true",
        help="Write nothing; exit with status 1 if the files on disk differ from what the sheet would generate.",
    )
    args = parser.parse_args()
    output_dir: Path = args.output_dir

    # Load template
    with open(TEMPLATE_FILE) as f:
        print(TEMPLATE_FILE)
        template = Template(f.read())

    # Read the table: local CSV (testing) or Google Sheet
    if args.csv:
        csv_bytes = args.csv.read_bytes()
    else:
        if not SHEET_ID:
            sys.exit(
                "SPAICOM_SHEET_ID is not set. Copy .env.example to .env and fill it in "
                "(or set it as a GitHub repository variable)."
            )
        csv_bytes = download_sheet_as_csv(SHEET_ID, GID)

    # Load into Polars
    df = pl.read_csv(
        csv_bytes,
        schema_overrides={"superuser": pl.String, "highlight_name": pl.String},
    )

    # Headers may be labelled "role (Optional)" in the sheet; ignore the label and case.
    df = df.rename(
        {
            c: re.sub(
                r"\s*\(optional\)\s*$", "", c.strip(), flags=re.IGNORECASE
            ).lower()
            for c in df.columns
        }
    )
    # `title` (display name) defaults to "First Last"; the two flags default to false.
    defaults = {
        "title": pl.concat_str(
            ["first_name", "last_name"], separator=" ", ignore_nulls=True
        )
        if {"first_name", "last_name"} <= set(df.columns)
        else pl.lit(""),
        "superuser": pl.lit("false"),
        "highlight_name": pl.lit("false"),
        "active": pl.lit("yes"),  # still takes part in the lab (alumni may too)
    }
    for col, default in defaults.items():
        if col not in df.columns:
            df = df.with_columns(default.alias(col))
        else:
            df = df.with_columns(
                pl.when(pl.col(col).fill_null("").str.strip_chars() == "")
                .then(default)
                .otherwise(pl.col(col))
                .alias(col)
            )

    df = df.with_columns(
        pl.col("active")
        .str.strip_chars()
        .str.to_lowercase()
        .is_in(["no", "n", "false", "0"])
        .not_()
        .cast(pl.String)
        .str.to_lowercase()
        .alias("active")
    )

    problems = validate(df)
    if problems:
        print("The people sheet has problems, nothing was written:", file=sys.stderr)
        for p in problems:
            print(f"  - {p}", file=sys.stderr)
        sys.exit(1)

    # Convert multi-value fields
    df = df.with_columns(
        pl.col("interests").str.split(";").list.eval(pl.element().str.strip_chars()),
        pl.col("user_groups").str.split(";").list.eval(pl.element().str.strip_chars()),
        pl.col("education")
        .str.split(";")
        .list.eval(
            pl.element()
            .str.split("|")
            .list.to_struct(
                # n_field_strategy="max_width",
                fields=["course", "institution", "year"],
            )
        ),
    ).fill_null("")

    # Ensure output directory exists
    if not args.check:
        output_dir.mkdir(exist_ok=True, parents=True)

    # Generate markdown files
    differing = []
    for row in df.to_dicts():
        filename = f"{row['first_name']} {row['last_name']}"
        filename = slugify_author_name(filename)

        authorpath = output_dir / filename
        filepath = authorpath / "_index.md"
        rendered = template.render(**row)

        if args.check:
            current = filepath.read_text() if filepath.exists() else None
            if current != rendered:
                differing.append(filepath)
            continue

        authorpath.mkdir(exist_ok=True, parents=True)
        with open(filepath, "w") as f:
            f.write(rendered)
        print(f"Generated: {filepath}")

    if args.check:
        if differing:
            print("These author files differ from the sheet (run `just authors`):")
            for f in differing:
                print(f"  - {f}")
            sys.exit(1)
        print("Author files are in sync with the sheet.")


if __name__ == "__main__":
    main()
