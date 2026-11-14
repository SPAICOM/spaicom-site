---
name: submit-changes
description: Put the user's changes online for review: create a branch, commit, push and open a pull request. Use only when the user asks to submit, publish, share or open a PR for their changes.
---

# Submit changes

The site goes live when a pull request is merged into `main`. The user should never need
to know git; you handle it, but **ask before each outward-facing step** (commit, push, PR).

1. Run `just check-content` (and `just check` if Hugo is available). Do not submit if it
   reports errors.
2. Look at what changed: `git status` and `git diff --stat`. Tell the user in plain words
   what will be submitted. If unrelated files changed, ask whether to include them.
   Never include `.env`, `public/`, `resources/` or temp files.
3. If on `main`, create a branch: `git switch -c content/<short-topic>-<YYYY-MM-DD>`.
4. After the user agrees: stage **specific paths** (`git add content/publication/<slug>`),
   not `git add -A`. Commit with a clear message, e.g.
   `content: add paper "Topological neural networks over the air"`.
   Follow any attribution rule given by the environment or the user.
5. Push the branch and open the PR (`gh pr create`) with a short description of what a
   reviewer will see and which pages to look at. If `gh` is not logged in, tell the user
   to run `gh auth login` and stop.
6. Give the user the PR link. Explain that a maintainer reviews it, CI checks run, and
   merging publishes the change within a few minutes.

## Never

- Push to `main`, force-push, or merge the PR yourself unless the user explicitly asks.
- Commit generated build output or secrets.
