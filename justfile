# SPAICOM site: common tasks. Run `just` to list them.
# Requires: just, uv, hugo (extended) and go. `nix develop` provides all of them.

set dotenv-load := true
set shell := ["bash", "-euo", "pipefail", "-c"]

# List the available recipes
default:
    @just --list --unsorted

# ---------------------------------------------------------------- preview ---

# Preview the site at http://localhost:1313 (drafts and future-dated items included)
# Usage: just serve [nix=auto|yes|no]  (the "nix=" prefix is optional, e.g. `just serve yes` also works)
#   auto (default): enters the Nix dev shell only if `hugo` isn't already on PATH
#   yes: forces the Nix dev shell
#   no: forces plain `hugo` (fails if it isn't installed)
serve nix="auto":
    #!/usr/bin/env bash
    set -euo pipefail
    nix="{{nix}}"; nix="${nix#nix=}"
    if [ "$nix" = yes ] || { [ "$nix" = auto ] && ! command -v hugo >/dev/null; }; then
        exec nix develop -c just serve nix=no
    fi
    hugo server --buildDrafts --buildFuture --navigateToChanged

# Preview reachable from your other devices over Tailscale (http://<tailscale-ip>:1313)
# Usage: just serve-remote [nix=auto|yes|no] -- same as `serve`, see above.
serve-remote nix="auto":
    #!/usr/bin/env bash
    set -euo pipefail
    nix="{{nix}}"; nix="${nix#nix=}"
    if [ "$nix" = yes ] || { [ "$nix" = auto ] && ! command -v hugo >/dev/null; }; then
        exec nix develop -c just serve-remote nix=no
    fi
    ip=$(tailscale ip -4 | head -n1)
    echo "Open http://$ip:1313/ from any device on your tailnet"
    hugo server --buildDrafts --buildFuture --bind "$ip" --port 1313 --baseURL "http://$ip:1313/" --appendPort=false

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

# Find new papers of active members (OpenAlex) and pick which to add, in a terminal UI
discover *ARGS:
    uv run scripts/discover_papers.py {{ARGS}}

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
    uvx ruff@0.17.5 check scripts src
    uvx ruff@0.17.5 format --check scripts src

# Everything CI runs: lint, content checks and a full site build
check: lint check-content
    hugo --gc --minify --destination "$(mktemp -d)"
