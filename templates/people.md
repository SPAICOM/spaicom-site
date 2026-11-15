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
  {% for item in interests or [] %}
  - {{item}}
  {% endfor %}

education:
  courses:
  {% for item in education or [] %}
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

# Still takes part in the lab (an alumnus can be active); read by the paper-discovery tool
active: {{active}}

user_groups:
  {% for group in user_groups %}
  - {{group}}
  {% endfor %}
---

{{long_bio}}
