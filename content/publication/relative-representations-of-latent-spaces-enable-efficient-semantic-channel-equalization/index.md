---
title: "Relative Representations of Latent Spaces enable Efficient Semantic Channel Equalization"
authors:
- Tomas Huttebraucker
- simone-fiorellino
- Mohamed Sana
- paolo-di-lorenzo
- Emilio Calvanese Strinati
date: "2024-11-29T00:00:00Z"
doi: "https://doi.org/10.48550/arXiv.2411.19719"

# Schedule page publish date (NOT publication's date).
publishDate: "2024-11-29T00:00:00Z"

# Publication type.
# Accepts a single type but formatted as a YAML list (for Hugo requirements).
# Enter a publication type from the CSL standard.
publication_types: ["article-journal"]

# Publication name and optional abbreviated publication name.
publication: ""
publication_short: ""

abstract: In multi-user semantic communication, language mismatch poses a significant challenge when independently trained agents interact. We present a novel semantic equalization algorithm that enables communication between agents with different languages without additional retraining. Our algorithm is based on relative representations, a framework that enables different agents employing different neural network models to have unified representation. It proceeds by projecting the latent vectors of different models into a common space defined relative to a set of data samples called \textit{anchors}, whose number equals the dimension of the resulting space. A communication between different agents translates to a communication of semantic symbols sampled from this relative space. This approach, in addition to aligning the semantic representations of different agents, allows compressing the amount of information being exchanged, by appropriately selecting the number of anchors. Eventually, we introduce a novel anchor selection strategy, which advantageously determines prototypical anchors, capturing the most relevant information for the downstream task. Our numerical results show the effectiveness of the proposed approach allowing seamless communication between agents with radically different models, including differences in terms of neural network architecture and datasets used for initial training.

# Summary. An optional shortened abstract.
summary: ""

tags:
 - Goal-oriented Semantic Communications

featured: false

# links:
# - name: ""
#   url: ""
url_pdf: https://arxiv.org/pdf/2411.19719
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
#  caption: 'Image credit: [**Unsplash**](https://unsplash.com/photos/jdD8gXaTZsc)'
#  focal_point: ""
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
slides: ""
---
