---
name: add-event
description: Add a seminar, talk, workshop, conference attendance or other event to the Events page. Use when someone announces or wants to record an event.
---

# Add an event

1. Collect: **title**, **start date**, end date if it spans days, **location**, event
   name if it is part of a larger conference, link to the event page, a short summary.
2. Create it:
   `just new-event "Title" --date YYYY-MM-DD [--end-date YYYY-MM-DD] --location "City, Country" --event-name "Conference name" --summary "One line"`
3. Open the printed file and fill `event_url`, `address` (city/country), `abstract` and the
   body. Add `authors:` (profile folder names) for the speakers, and `url_slides` /
   `url_video` once available.
4. Events are listed as "Recent & Upcoming". Dates in the future show as upcoming.
5. **Verify**: `just check-content`, `just serve`, open Events. Then offer `submit-changes`.
