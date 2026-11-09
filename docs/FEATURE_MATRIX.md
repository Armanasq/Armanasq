# Feature catalogue and evidence gates

| Component | Source / inspiration | Implementation |
|---|---|---|
| Original light/dark hero | Custom research graphics | Versioned local SVG, immediately visible |
| Agentic AI, clinical systems, robotics | Public repositories + editorial research description | Curated README, no private repo disclosure |
| Dynamic public footprint | GitHub REST API | Reproducible JSON and SVG, scheduled |
| Public event timeline | Public event endpoint | Bounded sample, explicit gaps and fallback |
| Research radar | Original | Curated projects joined to verified repository metadata |
| Data lineage | Original | Timestamp, GitHub data source, snapshot checksum |
| Research method graph | Original | Static transparent methodology visual |
| Languages (most/recent) | Lowlighter Metrics | GitHub Action panel |
| Isometric contributions | Lowlighter Metrics | GitHub Action panel |
| GitHub achievements | Lowlighter Metrics | GitHub Action panel |
| Notable contributions | Lowlighter Metrics | GitHub Action panel |
| Community and people | Lowlighter Metrics | GitHub Action panel |
| Repository showcase and topics | Lowlighter Metrics | GitHub Action panel |
| Recent activity | Lowlighter Metrics | GitHub Action panel |
| Coding habits, issues, and PRs | Lowlighter Metrics | GitHub Action panel |
| Stars and license footprint | Lowlighter Metrics | GitHub Action panel |
| Profile games such as chess | Other README examples | Not included: unrelated to technical portfolio |
| Entertainment/music/sponsors panels | Optional Lowlighter plugins | Not included: unsupported or unrelated personal data |
| Publications | Public research repositories | No invented DOI, publication status, or impact figure |

## Quality gates

- Valid XML SVGs, readable desktop and mobile widths, light/dark-safe hero.
- Tests cover event semantics, input escaping, public/private boundary, snapshot output.
- No undocumented achievements or misleading contribution numbers.
- Generated files and upstream plugin outputs are stored in the same public repository.
- Public research links must be verified public before inclusion in the automated radar.

GitHub's own user profile Overview page is not under repository control; only the profile README and generated assets can be changed from this repository.
