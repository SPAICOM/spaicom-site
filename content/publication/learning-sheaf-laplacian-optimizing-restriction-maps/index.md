---
title: 'Learning Sheaf Laplacian Optimizing Restriction Maps'

# Authors
# If you created a profile for a user (e.g. the default `admin` user), write the username (folder name) here
# and it will be replaced with their full name and linked to their profile.
authors:
  - leonardo-di-nino
  - Sergio Barbarossa
  - paolo-di-lorenzo

date: '2024-10-27T00:00:00Z'
doi: '10.1109/IEEECONF60004.2024.10942997'

# Schedule page publish date (NOT publication's date).
publishDate: '2024-10-27T00:00:00Z'

# Publication type.
# Accepts a single type but formatted as a YAML list (for Hugo requirements).
# Enter a publication type from the CSL standard.
publication_types: ['paper-conference']

# Publication name and optional abbreviated publication name.
publication: In *2024 58th Asilomar Conference on Signals, Systems, and Computers*
publication_short: In *Asilomar 2024*

abstract: "The aim of this paper is to propose a novel framework to infer the sheaf Laplacian, including the topology of a graph and the restriction maps, from a set of data observed over the nodes of a graph. The proposed method is based on sheaf theory, which represents an important generalization of graph signal processing. The learning problem aims to find the sheaf Laplacian that minimizes the total variation of the observed data, where the variation over each edge is also locally minimized by optimizing the associated restriction maps. Compared to alternative methods based on semidefinite programming, our solution is significantly more numerically efficient, as all its fundamental steps are resolved in closed form. The method is numerically tested on data consisting of vectors defined over subspaces of varying dimensions at each node. We demonstrate how the resulting graph is influenced by two key factors: the cross-correlation and the dimensionality difference of the data residing on the graph's nodes."

# Summary. An optional shortened abstract.
summary: ''

tags:
 - Graph Learning
 - Graph Signal Processing
 - Representation Learning
 - Sheaf Signal Processing

# Display this page in the Featured widget?
featured: true

# Custom links (uncomment lines below)
# links:
# - name: Custom Link
#   url: http://example.org

url_pdf: 'https://arxiv.org/pdf/2501.19207'
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
