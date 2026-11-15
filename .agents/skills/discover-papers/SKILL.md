---
name: discover-papers
description: Find new papers by lab members and choose which to add to the Publications page, using the terminal review screen. Use when someone asks "what new papers do we have", "find papers by <member>" or wants to bulk-check for missing publications.
---

# Discover new papers

Run `just discover` (all active members) or `just discover --member paolo-di-lorenzo`.
Add `--list` to only print the candidates without the interactive screen.

1. First run: for each member the tool shows OpenAlex author matches and asks which one is them.
   Pick the one with the right institution and number of works. The answer is saved in
   `discovery/openalex_ids.csv`. If unsure, type `s` to skip that member for now.
2. In the review screen: `a` add, `f` add as featured, `d` discard, `u` undo, `r` switch the
   co-author rule on/off, `w` apply and save, `q` quit (twice if there are unsaved marks).
3. Applying creates the pages (same code as the sheet sync) and records every decision in
   `discovery/papers_reviewed.csv`, so a paper is never offered twice.

Settings (date cutoff, required co-authors) are in `discovery/discovery.toml`.
Members with `active = no` in the People sheet are skipped.

After applying: run `just check`, show the user `git status`, and let them commit
(`content/publication/` and `discovery/`). Never commit yourself.

The review screen needs a real terminal. An agent cannot drive it: ask the user to run
`just discover` themselves, or use `--list` to show them the candidates.
