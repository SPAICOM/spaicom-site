---
name: edit-page-text
description: Change wording on the homepage, contact page, tour page, People page title, menus or site title and description. Use for text or navigation edits that are not news, events, papers or people.
---

# Edit page text

| What | Where |
|---|---|
| Homepage hero title/text, news and preprint blocks | `content/_index.md` (`sections:` list; each `block:` is a section) |
| Contact page | `content/contact/index.md` |
| Tour page | `content/tour/index.md` |
| People page heading, which groups are shown | `content/people/index.md` |
| Menu entries and order | `config/_default/menus.yaml` (`weight` sets the order) |
| Site title, footer, language | `config/_default/hugo.yaml`, `params.yaml`, `languages.yaml` |

Known leftovers from the template that need real text: the homepage hero paragraph
("The **Wowchemy Research Group**...") and the contact page (Lorem ipsum). `just check-content`
lists remaining template text.

Rules:

1. Front matter is YAML between `---` lines. Keep indentation (2 spaces) and quotes. A
   colon inside text needs the value in quotes.
2. Keep shortcodes like `{{% cta ... %}}` and `block:` names intact.
3. Keep the user's wording; do not rewrite or "improve" copy unasked.
4. Do not change a menu `url` unless the target page exists.
5. **Verify**: `just check-content`, `just serve`, open the affected page. Then offer
   `submit-changes`.
