---
title: 'Topological neural networks over the air'

# Authors
# If you created a profile for a user (e.g. the default `admin` user), write the username (folder name) here
# and it will be replaced with their full name and linked to their profile.
authors:
  - simone-fiorellino
  - claudio-battiloro
  - paolo-di-lorenzo

# Author notes (optional)

date: '2024-03-18T00:00:00Z'
doi: 'https://doi.org/10.1109/ICASSP48485.2024.10446693'

# Schedule page publish date (NOT publication's date).
publishDate: '2024-03-18T00:00:00Z'

# Publication type.
# Accepts a single type but formatted as a YAML list (for Hugo requirements).
# Enter a publication type from the CSL standard.
publication_types: ['paper-conference']

# Publication name and optional abbreviated publication name.
publication: In *2024 IEEE International Conference on Acoustics, Speech and Signal Processing*
publication_short: In *ICASSP 2024*

abstract: Topological neural networks (TNNs) are information processing architectures that model representations from data lying over topological spaces (e.g., simplicial or cell complexes) and allow for decentralized implementation through localized communications over different neighborhoods. Existing TNN architectures have not yet been considered in realistic communication scenarios, where channel effects typically introduce disturbances such as fading and noise. This paper aims to propose a novel TNN design, operating on regular cell complexes, that performs over-the-air computation, incorporating the wireless communication model into its architecture. Specifically, during training and inference, the proposed method considers channel impairments such as fading and noise in the topological convolutional filtering operation, which takes place over different signal orders and neighborhoods. Numerical results illustrate the architecture's robustness to channel impairments during testing and the superior performance with respect to existing architectures, which are either communication-agnostic or graph-based.

# Summary. An optional shortened abstract.
summary: ''

tags:
  - Topological Signal Processing
  - Topological Neural Networks
  - Over-the-Air Computation
  - Cell Complexes

# Display this page in the Featured widget?
featured: true

# Custom links (uncomment lines below)
# links:
# - name: Custom Link
#   url: http://example.org

url_pdf: 'https://arxiv.org/pdf/2502.10070'
url_code: ''
url_dataset: ''
url_poster: ''
url_project: ''
url_slides: ''
url_source: ''
url_video: ''

# Featured image
# To use, add an image named `featured.jpg/png` to your page's folder.
#image:
#  caption: 'Image credit: [**Unsplash**](https://unsplash.com/photos/pLCdAaMFLTE)'
#  focal_point: ''
#  preview_only: false

# Associated Projects (optional).
#   Associate this publication with one or more of your projects.
#   Simply enter your project's folder or file name without extension.
#   E.g. `internal-project` references `content/project/internal-project/index.md`.
#   Otherwise, set `projects: []`.
projects: []

# Slides (optional).
#   Associate this publication with Markdown slides.
#   Simply enter your slide deck's filename without extension.
#   E.g. `slides: "example"` references `content/slides/example/index.md`.
#   Otherwise, set `slides: ""`.
slides: ''
---
