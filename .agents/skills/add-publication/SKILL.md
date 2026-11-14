---
name: add-publication
description: Add a paper (conference, journal or preprint) to the Publications page. Use when someone gives a DOI, arXiv link/ID, BibTeX, a title or a PDF and wants it on the website.
---

# Add a publication

The source of truth is the **publications tab of the Google Sheet**. New rows create pages;
rows for papers already on the site update them **in place** (links, tags, featured, and
preprint -> published upgrades). Nothing is deleted, and body text, curated abstracts/authors
and images are kept.

## Steps

1. **Get an identifier.** From what the user gave you, find the DOI (`10.xxxx/...`) or
   arXiv ID (`2403.12345`). A pasted URL is fine. If they only have a title, search for
   the DOI and confirm the match with them. Do not guess.
2. **Choose the route:**
   - *Normal*: tell the user to add a row to the publications tab with the `id` (and
     optionally `featured`, `tags`, `code_url`, `slides_url`, `video_url`, `project_url`,
     `pdf_url`). The nightly sync opens a pull request, or you can run step 3 now.
   - *Quick, from this machine*: write a one-row CSV (header `id,type,featured,tags,code_url,...`)
     in a temp file and run `uv run scripts/sync_publications.py --csv <file>`. Use this when
     the user wants it now and has no access to the sheet. Remind them to also add the row
     to the sheet so it is not lost, because the sheet is the master list.
   - *No DOI/arXiv* (workshop, thesis, report): rows may use `title`, `venue`, `year`,
     `authors` ("Given Family; Given Family") and `type` (`conference|journal|preprint`) instead of `id`.
3. **Run `just papers-dry` first**, read the report, then `just papers`.
4. **Read the report to the user in plain words:**
   - *Authors not matched*: a co-author without a profile (fine, shown as plain text) or a
     lab member whose name differs from their profile (e.g. "P. Di Lorenzo"). For the
     latter, replace the name in the new page's `authors:` list with the profile folder name.
   - *Possible duplicate*: the paper is probably a preprint that is now published. Do not
     create a second page; offer to update the existing page (`doi`, `publication`,
     `publication_short`, `publication_types`, date) by hand.
   - *Without an abstract*: ask whether they want to paste one into `abstract:`.
5. **Optional polish** the user may ask for: featured image (`featured.jpg` in the paper
   folder, see `add-image`), `summary`, `url_*` links, `tags`.
6. **Verify**: `just check-content`, then `just serve` and look at Publications.
   Then offer `submit-changes`.

## Updating a paper that is already on the site

| Request | Sheet change |
|---|---|
| Add code/slides/video/poster link, tags, featured | Fill the cell on that paper's row |
| A preprint was published | Add a row with the new DOI. The preprint page is upgraded automatically when the title matches; otherwise set `replaces` to the arXiv ID (or page folder name) |
| Metadata is wrong / abstract now available | Set `update` to `yes` on the row, run, then clear it |

Run `just papers-dry` first: the "Existing pages updated" section lists which fields change.
An "Existing pages updated" entry for a page the user hand-edited means a sheet cell overrode
it; check with them. A duplicate report means the same title exists but is not a preprint.

## Do not

- Edit the `doi`, title or authors of a *generated* page to "fix" metadata without telling
  the user what you changed and why.
- Delete a publication folder unless explicitly asked.
