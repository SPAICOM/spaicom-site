---
# Leave the homepage title empty to use the site title
title:
date: 2022-10-24
type: landing

sections:
  - block: hero
    content:
      title: |
        <span class="wm-sp">Signal Processing</span> and <span class="wm-ai">Artificial Intelligence</span> for <span class="wm-com">Communications</span>
      image:
        filename: welcome.jpg
      text: |
        <br>
        
        <span class="wm"><span class="wm-sp">SP</span><span class="wm-ai">AI</span><span class="wm-com">COM</span></span> is a research group at the Department of Information Engineering, Electronics, and Telecommunications of Sapienza University of Rome. We develop signal processing and machine learning methods for communication systems, with a focus on topological signal processing and topological deep learning, goal-oriented and semantic communications, and distributed and federated learning.
  
  - block: collection
    content:
      title: Latest News
      subtitle:
      text:
      count: 5
      filters:
        author: ''
        category: ''
        exclude_featured: false
        publication_type: ''
        tag: ''
      offset: 0
      order: desc
      page_type: post
    design:
      view: card
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
          filename: coders.jpg
          filters:
            brightness: 1
          parallax: false
          position: center
          size: cover
          text_color_light: true
      spacing:
        padding: ['20px', '0', '20px', '0']
      css_class: fullscreen

  - block: collection
    content:
      title: Latest Preprints
      text: ""
      count: 5
      filters:
        folders:
          - publication
        publication_type: 'article'
    design:
      view: citation
      columns: '1'

  - block: markdown
    content:
      title:
      subtitle:
      text: |
        {{% cta cta_link="./people/" cta_text="Meet the team →" %}}
    design:
      columns: '1'
---
