---
name: update-people
description: Add, change or remove a lab member, move someone to Alumni, fix a bio, role or link, or refresh the People page. Use for any question about team members.
---

# Update people

**Member profiles are generated from the Google Sheet** (tab "people"). Never edit
`content/authors/*/_index.md` directly: the next sync overwrites it.

## What the user does

Edit the sheet. Relevant columns: `first_name`, `last_name`, `role`, `user_groups`
(`;`-separated: Principal Investigators, Senior Researchers, Ph.D. Students,
Collaborators, Alumni), `short_bio`, `long_bio`, `interests` (`;`-separated),
`education` (`course|institution|year` entries separated by `;`), `linkedin`, `github`,
`scholar`, `email`. Move someone on: change `user_groups` to `Alumni`; do not delete the
row, so their papers keep linking to their profile.

## What you do

1. Explain the sheet edit above in the user's terms. If they give you the new data, show
   them exactly what to type per column.
2. After they edit the sheet, bring it into the repo:
   `just authors` (needs `.env` with `SPAICOM_SHEET_ID`; if the script says it is missing,
   point to `.env.example`). The nightly workflow does the same via a pull request.
3. If the script prints problems (empty name, duplicate person, missing `user_groups`),
   translate them into "row N of the sheet needs X" and stop; nothing was written.
4. Check what changed with `git status` / `git diff --stat content/authors` and summarise:
   "2 new people, 1 changed role".
5. A new person has no photo: use `add-image` (member photo section).
6. A new member can only be referenced by papers/posts **after** their profile exists.
7. **Verify**: `just check-content` (a group not shown on People is flagged; groups shown
   are listed in `content/people/index.md`), `just serve`, open People.

## Edge cases

- Removing someone entirely: rows deleted from the sheet are *not* deleted from the repo.
  Ask the user to confirm, then remove the folder `content/authors/<slug>/` and check no
  publication still lists that slug (`just check-content` will fail if one does).
- `superuser: true` marks the group leaders (admin permissions in the theme's CMS).
