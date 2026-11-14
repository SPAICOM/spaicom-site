# SPAICOM site: common tasks. Run `just` to list them.
# Requires: just, uv, hugo (extended) and go. `nix develop` provides all of them.

set dotenv-load := true
set shell := ["bash", "-euo", "pipefail", "-c"]

# List the available recipes
default:
    @just --list --unsorted

# ---------------------------------------------------------------- preview ---

# Preview the site at http://localhost:1313 (drafts and future-dated items included)
serve:
    hugo server --buildDrafts --buildFuture --navigateToChanged

# Build the production site into ./public
build:
    hugo --gc --minify

# Delete build output
clean:
    rm -rf public resources

# ------------------------------------------------------------------ people ---

# Regenerate content/authors/* from the Google Sheet
authors:
    uv run scripts/populate_authors.py

# Exit 1 if the author files differ from the sheet (does not write anything)
authors-check:
    uv run scripts/populate_authors.py --check

# ------------------------------------------------------------ publications ---

# Create pages for new rows of the sheet's publications tab (writes files)
papers:
    uv run scripts/sync_publications.py

# Show what `papers` would create, without writing
papers-dry:
    uv run scripts/sync_publications.py --dry-run

# ----------------------------------------------------------- new content ---

# New news post:   just new-post "Title" --author paolo-di-lorenzo --date 2026-11-14
new-post title *args:
    uv run scripts/new_content.py post "{{ title }}" {{ args }}

# New event:       just new-event "Title" --date 2026-12-03 --location "Rome"
new-event title *args:
    uv run scripts/new_content.py event "{{ title }}" {{ args }}

# ----------------------------------------------------------------- quality ---

# Validate the content (front matter, author slugs, placeholders)
check-content:
    uv run scripts/check_content.py

# Python lint and format check
lint:
    uvx ruff check scripts src
    uvx ruff format --check scripts src

# Everything CI runs: lint, content checks and a full site build
check: lint check-content
    hugo --gc --minify --destination "$(mktemp -d)"
