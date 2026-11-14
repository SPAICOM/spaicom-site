---
name: add-news-post
description: Publish a news item (award, new paper, new member, grant, talk recap) on the News page and homepage. Use when someone says "add a news" or gives text announcing something.
---

# Add a news post

1. Collect: **title**, **date** (default today), 1-3 sentences or paragraphs of text,
   optional author(s) (profile folder names, e.g. `paolo-di-lorenzo`), optional image.
   Ask only for what is missing; do not invent details.
2. Create it: `just new-post "Title" --date YYYY-MM-DD --author <slug> --summary "One line"`
   (`--author` can repeat). The command prints the new file path.
3. Replace the placeholder line `Write the news here (Markdown).` with the user's text.
   Keep their wording; fix only obvious typos. Links are written `[text](https://...)`.
4. Optional: add `tags`, and an image (`featured.jpg` in the same folder, see `add-image`).
   Future-dated posts stay hidden until their date.
5. **Verify**: `just check-content`, `just serve`, open News and the homepage.
   Then offer `submit-changes`.
