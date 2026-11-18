---
title: Contact
date: 2024-06-13

type: landing

sections:
  - block: contact
    content:
      title: Contact
      text: |-
        Get in touch with the SPAICOM group at the Department of Information Engineering, Electronics, and Telecommunications (DIET), Sapienza University of Rome. For questions about our research, collaborations, or open positions, write to us by email.
      email: paolo.dilorenzo@uniroma1.it
      address:
        street: Via Eudossiana 18
        city: Rome
        region: RM
        postcode: '00184'
        country: Italy
        country_code: IT
      coordinates:
        latitude: '41.893498'
        longitude: '12.493990'
      #contact_links:
      #  - icon: comments
      #    icon_pack: fas
      #    name: Discuss on Forum
      #    link: 'https://discourse.gohugo.io'
    
      # Automatically link email and phone or display as text?
      autolink: true
    
      # Email form provider
      form:
        provider: netlify
        formspree:
          id:
        netlify:
          # Enable CAPTCHA challenge to reduce spam?
          captcha: false
    design:
      columns: '1'

  - block: markdown
    content:
      title:
      subtitle: ''
      text:
    design:
      columns: '1'
      background:
        image: 
          filename: lab-team-2025.jpg
          filters:
            brightness: 1
          parallax: false
          position: center
          size: cover
          text_color_light: true
      spacing:
        padding: ['20px', '0', '20px', '0']
      css_class: fullscreen
---
