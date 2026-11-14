---
name: fix-broken-build
description: Diagnose and fix a failed site build, a failed GitHub Action (deploy, PR check, sheet sync) or a page that renders wrong. Use when something that used to work now fails.
---

# Fix a broken build

1. **Reproduce locally**: `just check`. If Hugo is missing use `nix develop`.
2. **Find the cause** in the first error line, not the last. Common ones:
   - *Front matter YAML error* in a content file: unquoted colon, bad indent, a tab. Fix that file.
   - *Unknown author slug* / missing field: `just check-content` names the file.
   - *Shortcode errors*: unbalanced `{{% ... %}}`.
   - *Hugo module / network errors*: `go` missing or no internet; retry, then `hugo mod get -u` only if asked.
   - *Hugo version*: CI and Netlify pin **0.135.0**; newer local Hugo prints deprecation
     warnings from the theme (libsass). Warnings are not failures.
3. **GitHub Actions**: `gh run list --limit 5`, then `gh run view <id> --log-failed`.
   - `sync-people` / `sync-publications` fail with "SPAICOM_SHEET_ID is not set": the
     repository variable is missing (Settings > Secrets and variables > Actions > Variables).
   - "GitHub Actions is not permitted to create pull requests": enable it in
     Settings > Actions > General.
   - Sheet validation errors: they name the sheet row to fix.
   - The sheet returns an HTML page / 401: sharing is not "anyone with the link can view".
4. Make the smallest fix. Do not edit generated files to silence an error; fix the source
   (the sheet, a template, the script).
5. Re-run `just check` and report what was wrong and what you changed. Offer
   `submit-changes`.
