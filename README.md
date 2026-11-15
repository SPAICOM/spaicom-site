# SPAICOM site

Website of the **SPAICOM** research group (Signal Processing and Artificial Intelligence
for Communications), Sapienza University of Rome.
Live at <https://spaicom.github.io/spaicom-site/>.

Built with [Hugo](https://gohugo.io) and the [Hugo Blox / Wowchemy](https://hugoblox.com)
research-group theme. Every push to `main` is built and published to GitHub Pages.

## What goes where

| Content | Where it comes from |
|---|---|
| **People** | Google Sheet (tab "people") -> `content/authors/`, synced nightly through a pull request |
| **Publications** | Google Sheet (tab "publications": one DOI or arXiv ID per row) -> `content/publication/` |
| **News, events** | `just new-post` / `just new-event`, or ask an AI agent |
| **Page text** (home, contact, menus) | Edit `content/` and `config/` directly |

Non-technical members only need the Google Sheet, or an AI agent that follows
[`AGENTS.md`](AGENTS.md) (works with Claude Code, Codex, Cursor and similar tools; task
playbooks are in [`.agents/skills/`](.agents/skills)).

## Getting started

```bash
nix develop          # Hugo, Go, uv, just, git, gh. Or install these yourself.
cp .env.example .env # then fill in the Google Sheet IDs
just serve           # http://localhost:1313
```

With direnv, `direnv allow` loads the shell automatically.

| Command | What it does |
|---|---|
| `just serve` / `just build` | Preview / production build |
| `just authors` | Regenerate people pages from the sheet (`just authors-check` only compares) |
| `just papers` | Apply the optional publications tab (`just papers-dry` to preview) |
| `just discover` | Terminal screen: find new papers by active members (OpenAlex), choose add / featured / discard |
| `just new-post "Title"` / `just new-event "Title" --date 2026-12-03` | New news / event page |
| `just check-content` | Validate front matter, author references, leftover template text |
| `just check` | Lint + content checks + full build (what CI runs on pull requests) |

## Automation

| Workflow | When | Does |
|---|---|---|
| `publish.yaml` | push to `main` | Build with Hugo 0.135.0, deploy to GitHub Pages |
| `check.yml` | pull request | Ruff, content validation, build |
| `sync-people.yml` | nightly + manual | Sheet -> `content/authors/`, opens a PR |
| `sync-publications.yml` | nightly + manual | Optional publications tab -> `content/publication/`, opens a PR |

One-time repository setup: add the **variables** `SPAICOM_SHEET_ID`,
`SPAICOM_PEOPLE_GID` (and optionally `SPAICOM_PUBLICATIONS_GID`, `CROSSREF_MAILTO`) under
*Settings > Secrets and variables > Actions > Variables*, and enable *Settings > Actions >
General > Allow GitHub Actions to create and approve pull requests*.
The sheet must be viewable by "anyone with the link"; its ID is configuration, not a secret.

## The publications tab (optional)

New papers are normally added with `just discover` (see below). The "publications" tab is
optional and only needed for extras. Fill the first four columns: `id` (a DOI or arXiv ID,
the only one the script cannot work without), `pdf_url`, `code_url` and `type`
(`conference`, `journal` or `preprint`; guessed if blank). Every other column is marked
`(Optional)`. Import [`templates/publications-sheet.csv`](templates/publications-sheet.csv)
to get the header (a trailing ` (Optional)`, case and extra columns are ignored).

With just a DOI the page is created from Crossref / arXiv / OpenAlex. The optional columns
add what the tool cannot know: `slides_url`, `video_url`, `project_url`, `dataset_url`,
`poster_url`, `tags`, `featured`, or the fields for papers without an identifier (`title`,
`year`, `authors`, `venue`, `abstract`). Without the tab (no `SPAICOM_PUBLICATIONS_GID`
variable) the nightly sync simply does nothing.

Two more columns control updates: `replaces` (the DOI, arXiv ID or folder of the page this
row supersedes) and `update` (`yes` to re-fetch and refresh the page).

**Updating a paper that is already on the site** (pages are edited in place; the body,
curated abstract/authors, images and hand-added fields are kept; nothing is ever deleted):

| You want to... | Do this in the sheet |
|---|---|
| Add a code/slides/video link, tags, or feature it | Fill the cell on the paper's row (an empty cell never clears a value) |
| Mark a preprint as published | Add a row with the new DOI. The matching preprint page is upgraded (type, venue, DOI, date, `cite.bib`). If the title changed a lot, set `replaces` to the arXiv ID |
| Fix wrong metadata or pick up a new abstract | Put `yes` in `update` on its row, then clear it |

Possible duplicates (same title, nothing to upgrade) are reported in the PR, not written.

## Credits

Theme: [Hugo Blox / Wowchemy](https://github.com/HugoBlox/hugo-blox-builder) (MIT).
Demo images in `assets/media/` should be replaced with the group's own.

## Finding new papers (optional)

`just discover` lists papers by active members that are not on the site yet. Mark each
one in the terminal (`a` add, `f` add as featured, `d` discard, `w` apply). Added papers
become pages like the sheet-driven ones, and every decision is stored in
`discovery/papers_reviewed.csv` so nothing is offered twice. `discovery/discovery.toml` sets
the start date and the co-author rule (for example "Barbarossa or Di Lorenzo must be an
author"). Commit `content/publication/` and `discovery/` afterwards.
