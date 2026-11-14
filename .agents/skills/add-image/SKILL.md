---
name: add-image
description: Add or replace an image: a member photo (avatar), a paper's featured image, a news/event banner, or the homepage hero. Use when someone provides a picture or asks for one to be changed.
---

# Add an image

Never commit very large images: resize first. Use Pillow through uv, no install needed:
`uv run --with pillow python - <<'PY' ... PY`.

| Purpose | File | Size guideline |
|---|---|---|
| Member photo | `content/authors/<slug>/avatar.jpg` | square crop, 400x400, JPEG |
| Paper featured image | `content/publication/<slug>/featured.jpg` | max width 1200 |
| News banner | `content/post/<slug>/featured.jpg` | max width 1200 |
| Event banner | `content/event/<slug>/featured.jpg` | max width 1200 |
| Homepage/section images | `assets/media/` + reference in `content/_index.md` | max width 1920 |

Steps:

1. Ask which page the image belongs to if unclear, and confirm they have the right to use
   it (their own, or properly credited). Add the credit to the page's `image.caption`.
2. Resize/crop with Pillow, quality about 85, save as JPEG (`featured.jpg`, `avatar.jpg`).
   For avatars, centre-crop to a square.
3. Replacing: overwrite the same filename, so no front matter edit is needed.
4. Add alt text where the page supports it (`image.caption` for banners).
5. **Verify**: `just serve`, look at the page. Check file size is under about 500 KB.
