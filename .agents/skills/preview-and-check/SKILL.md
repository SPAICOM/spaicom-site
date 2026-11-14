---
name: preview-and-check
description: Preview the website locally, run the checks, and explain any errors in plain language. Use before sharing changes or when the user asks "does it look right" or "does it build".
---

# Preview and check

1. `just check-content`: finds broken author references, missing titles/dates, and
   template leftovers. Errors must be fixed; warnings should be mentioned.
2. `just serve`: starts the site at http://localhost:1313 and reloads on changes. Tell the
   user which page to open for their change. Stop the server when done.
3. `just check`: the full gate (lint, content checks, production build). This is what
   CI runs on pull requests.

If a tool is missing (`hugo`, `go`, `uv`, `just`): `nix develop` provides them all;
otherwise install them. Without Hugo you can still run `just check-content`; say clearly
that you could not build the site.

Translate errors for the user:

| Message | Meaning / fix |
|---|---|
| `author 'xxx' looks like a profile slug but content/authors/xxx/ does not exist` | The person has no profile. Add them in the sheet, or write their name as plain text with a space ("Jane Roe") |
| `'user_groups' is empty` | The person would not appear on People; fill the column in the sheet |
| `missing title` / `missing date` | Front matter is incomplete in the named file |
| `invalid YAML front matter` | A quote/colon/indent error in the named file |
| `groups [...] are not displayed on the People page` | Add the group to the list in `content/people/index.md`, or fix the group name in the sheet |
| Hugo `failed to extract shortcode` / `module` errors | See `fix-broken-build` |
