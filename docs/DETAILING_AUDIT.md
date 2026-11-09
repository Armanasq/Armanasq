# Profile presentation and reliability audit

## Root causes addressed

- Removed Markdown embedded inside raw HTML table cells: GitHub CommonMark does not reliably parse Markdown there.
- Replaced badge overload with an upstream skill-icons service and clear research taxonomy.
- Replaced excessively wide repository titles with readable HTML tables, escaped fields and source-backed star counts.
- Used image widths that can share a row without forcing fixed-width HTML table columns.
- Consolidated the opening research description and reduced duplicate dashboard panels.
- Aligned README generation and tests to use the same HTML representation.

## Upstream services

- https://github.com/lowlighter/metrics
- https://github.com/tandpfun/skill-icons
- https://github.com/Platane/snk
- https://github.com/ryo-ma/github-profile-trophy
- https://github.com/DenverCoder1/github-readme-streak-stats

## Known limitations

The GitHub profile still contains static SVG hero and isometric charts. A successful commit does not prove their visual quality. The external snake renderer requires a successful output-branch workflow run. The upstream Metrics action can fail independently. GitHub Actions and browser screenshot checks are necessary before visual sign-off.

The workflow push/rebase conflict is mitigated with the recursive merge strategy, but concurrent writers to main should ideally be consolidated into one workflow to eliminate races.
