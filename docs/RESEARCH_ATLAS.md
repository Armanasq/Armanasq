# Research Atlas — data and visual contract

The README uses a research-first editorial hierarchy: identity, linked research constellation, scientific signal, research chronology, then repositories and operational metrics.

## Research constellation

The eight nodes are derived from `data/public-snapshot.json`. Node names and curated areas are provided by `config/featured.json`; public star counts and repository URLs are sourced from GitHub. Each node links to its original repository. The shared-methods connector is conceptual, not an inferred citation network. No graph centrality or impact scores are claimed.

## Scientific signal

The paired curves are explicitly illustrative. They are not generated from a real dataset, and no model accuracy is implied. A future data-backed version requires a verified experiment artifact with reference/prediction series, sampling interval, units, provenance and error metric.

## Chronicle

Chronicle points are sourced from the `pushed_at` fields in the public GitHub snapshot. They are neither publication dates nor claims about completed research. The layout is ordered by timestamp.

## Rendering and dependencies

All three new graphics are local SVG assets, compatible with GitHub's sanitized README renderer. External third-party metrics are nonessential and collapsed. The core presentation requires no JavaScript, external image CDN, secret, GitHub Pages runtime, or CSS.

## Limitations

This commit adds static generated assets based on the currently verified snapshot. Automatic regeneration of these three assets has not yet been integrated into the refresh script. Browser screenshot QA remains outstanding.
