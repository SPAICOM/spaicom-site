---
title: 'Topological Adaptive Least Mean Squares Algorithms over Simplicial Complexes'

# Authors
# If you created a profile for a user (e.g. the default `admin` user), write the username (folder name) here
# and it will be replaced with their full name and linked to their profile.
authors:
  - lorenzo-marinucci
  - claudio-battiloro
  - paolo-di-lorenzo

date: '2025-05-29T00:00:00Z'
doi: '10.23919/EUSIPCO63174.2024.10714988'

# Schedule page publish date (NOT publication's date).
publishDate: '2025-05-29T00:00:00Z'

# Publication type.
# Accepts a single type but formatted as a YAML list (for Hugo requirements).
# Enter a publication type from the CSL standard.
publication_types: ['paper-conference']

# Publication name and optional abbreviated publication name.
publication: ""
publication_short: ""

abstract: This paper introduces a novel adaptive framework for processing dynamic flow signals over simplicial complexes, extending classical least-mean-squares (LMS) methods to high-order topological domains. Building on discrete Hodge theory, we present a topological LMS algorithm that efficiently processes streaming signals observed over time-varying edge subsets. We provide a detailed stochastic analysis of the algorithm, deriving its stability conditions, steady-state mean-square-error, and convergence speed, while exploring the impact of edge sampling on performance. We also propose strategies to design optimal edge sampling probabilities, minimizing rate while ensuring desired estimation accuracy. Assuming partial knowledge of the complex structure (e.g., the underlying graph), we introduce an adaptive topology inference method that integrates with the proposed LMS framework. Additionally, we propose a distributed version of the algorithm and analyze its stability and mean-square-error properties. Empirical results on synthetic and real-world traffic data demonstrate that our approach, in both centralized and distributed settings, outperforms graph-based LMS methods by leveraging higher-order topological features.

# Summary. An optional shortened abstract.
summary: ''

tags:
 - Adaptive Learning
 - Mean Square Error
 - Flow Signal
 - Graph-based Methods
 - Least Mean Square
 - Signal Processing
 - Prediction Error
 - Notable Example
 - Noise Variance
 - Adaptive Technique
 - Cell Dimensions
 - Laplacian Matrix
 - Bicontinuous
 - Topological Information
 - Adaptive Filter
 - Simplicial Complex
 - Topological Space


# Display this page in the Featured widget?
featured: true

# Custom links (uncomment lines below)
# links:
# - name: Custom Link
#   url: http://example.org

url_pdf: 'https://arxiv.org/pdf/2505.23160'
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
