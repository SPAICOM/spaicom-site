# SPAICOM site: instructions for AI agents

This repository is the website of the SPAICOM research group (Signal Processing and
Artificial Intelligence for Communications, Sapienza University of Rome). It is a
static site built with **Hugo** and the **Wowchemy / Hugo Blox** research-group theme,
published to GitHub Pages on every push to `main`.

Most people who ask you for help are researchers, **not developers**. Talk in plain
language, say what you changed in terms of the website ("the paper now appears under
Publications"), and never make them learn git, YAML or Hugo.

## Rules (always)

1. **Never commit, push, merge or delete branches unless the user asks for it.**
   Use the `submit-changes` skill when they do. Never work directly on `main`: pushing
   goes through a branch and a pull request.
2. **Never hand-edit `content/authors/*/_index.md`.** Those files are generated from the
   Google Sheet by `just authors`. Tell the user to edit the sheet. (Photos such as
   `avatar.jpg` inside an author folder are fine; the script does not touch them.)
3. **Never edit `public/`, `resources/` or `*.lock` files by hand.** They are build output or generated.
4. **Create content with the `just` recipes and scripts**, not by writing front matter
   from memory. They produce valid, consistent files.
5. **Verify before you say "done":** run `just check-content` (and `just check` when
   Hugo is installed). Report any warnings that relate to your change.
6. Do not invent facts (authors, venues, dates, affiliations). If something is unknown,
   leave it empty or ask.
7. Ask before anything hard to undo: deleting content, rewriting many files, pushing.

## Layout

| Path | What it is |
|---|---|
| `content/_index.md` | Homepage (stack of blocks: hero, news, preprints...) |
| `content/authors/<first-last>/_index.md` | One profile per member. **Generated** from the sheet |
| `content/publication/<slug>/index.md` + `cite.bib` | One folder per paper |
| `content/post/<slug>/index.md` | News |
| `content/event/<slug>/index.md` | Events and talks |
| `content/people/index.md` | People page; lists which `user_groups` are shown |
| `content/contact`, `content/tour` | Static pages |
| `config/_default/` | Site config (`hugo.yaml`, `params.yaml`, `menus.yaml`) |
| `assets/media/` | Images used by pages (hero, banners) |
| `templates/` | Blank page templates and the Jinja template for author pages |
| `scripts/` | Automation (see below) |
| `src/` | Shared Python helpers |
| `.github/workflows/` | CI: deploy, PR checks, nightly sheet syncs |

Authors are referenced by **folder name** (`paolo-di-lorenzo`) in the `authors:` list of
publications and posts; Hugo turns that into a link to the profile. A plain name
(`Jane Roe`) is allowed for external co-authors.

## Commands (`just --list` shows all)

| Command | Purpose |
|---|---|
| `just serve` | Live preview at http://localhost:1313 |
| `just build` / `just check` | Production build / lint + content checks + build |
| `just check-content` | Validate front matter, author slugs, placeholder text |
| `just authors` / `just authors-check` | Regenerate / verify author pages from the sheet |
| `just papers` / `just papers-dry` | Create pages for new rows in the sheet's publications tab |
| `just new-post "Title" [--author slug] [--date YYYY-MM-DD]` | New news page |
| `just new-event "Title" --date YYYY-MM-DD [--location ...]` | New event page |

Setup: `nix develop` (or direnv, `.envrc` is provided) installs Hugo, Go, uv, just, git
and gh. Without Nix, install those by hand. Copy `.env.example` to `.env` and fill in the
Google Sheet IDs. The Python scripts declare their own dependencies and run with `uv run`.

## Data flow

- **People**: Google Sheet (tab "people") -> `scripts/populate_authors.py` + `templates/people.md` -> `content/authors/`.
  The nightly workflow `sync-people.yml` opens a pull request when the sheet changed.
- **Publications**: Google Sheet (tab "publications": a DOI or arXiv ID per row) ->
  `scripts/sync_publications.py` (Crossref / arXiv / OpenAlex) -> `content/publication/`.
  Creates pages, and updates existing ones in place (sheet link/featured/tags columns, preprint ->
  published via a matching title or the `replaces` column, `update=yes` to refresh metadata).
  Never deletes. `sync-publications.yml` runs it nightly.
- **Everything else** is edited directly in `content/`.
- **Deploy**: merge to `main` -> `publish.yaml` builds with Hugo 0.135.0 -> GitHub Pages.

## Conventions

- Dates are ISO: `2026-11-14` (front matter uses `'2026-11-14T00:00:00Z'`).
- Slugs are lowercase ASCII with hyphens, derived from the title.
- Publication type values: `paper-conference`, `article-journal`, `article` (preprint).
- Hugo/Hugo Blox shortcodes look like `{{% callout note %}}`; leave them intact.
- Python is formatted with `ruff` (run `just lint`).

## Skills

Task playbooks live in `.agents/skills/` (also visible at `.claude/skills/`):
`add-publication`, `add-news-post`, `add-event`, `update-people`, `add-image`,
`edit-page-text`, `preview-and-check`, `submit-changes`, `fix-broken-build`.
Read the matching one before starting a task.
