---
title: {{title}}

first_name: {{first_name}}
last_name: {{last_name}}

superuser: {{superuser}}

role: {{role}}

organizations:
  - name: {{org_name}}
    url: '{{org_url}}'

bio: {{short_bio}}

interests:
  {% for item in interests %}
  - {{item}}
  {% endfor %}

education:
  courses:
  {% for item in education %}
    - course: {{item.course}}
      institution: {{item.institution}}
      year: {{item.year}}
  {% endfor %}

social:
  - icon: envelope
    icon_pack: fas
    link: 'mailto:{{email}}'
  - icon: linkedin
    icon_pack: fab
    link: {{linkedin}}
  - icon: github
    icon_pack: fab
    link: {{github}}
  - icon: google-scholar
    icon_pack: ai
    link: {{scholar}}

email: '{{email_for_gravatar}}'

highlight_name: {{highlight_name}}

user_groups:
  {% for group in user_groups %}
  - {{group}}
  {% endfor %}
---

{{long_bio}}
