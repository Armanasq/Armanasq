# Profile architecture

The public GitHub profile README is the product. It is rendered by GitHub, not by a separate website. Its visuals are self-contained SVGs; no client-side scripts or external page permissions are required to view it.

## Data flows

1. \`scripts/profile_refresh.py\` calls GitHub's public REST API with an optional GitHub Actions token.
2. It enumerates **public repositories owned by Armanasq**, excludes private repositories and other owners, and records a bounded sample of public events.
3. It reads \`config/featured.json\` to select public projects and supply editorial research-area labels. Only matching verified public repositories appear in the generated radar.
4. It generates \`data/public-snapshot.json\` alongside SVG assets in \`assets/live/\`. The lineage panel stores a digest of the exact JSON snapshot and a generation timestamp.
5. The Lowlighter Metrics GitHub Action refreshes the four \`assets/metrics/*.svg\` panels with additional GitHub telemetry. When an integration is unavailable, a labelled placeholder remains rather than inventing data.
6. GitHub renders the updated README from the default branch.

## What this profile measures

- The number of public repositories and non-fork repositories owned by the account.
- Total stars on **original public repositories** (not unique stargazers).
- Public follower count reported by GitHub.
- A bounded sample of the account's public events, with an explicit unavailable state.
- Repository push timestamps and the selected research-repository view.
- Additional language, community, calendar, notable, and open-source metrics calculated by the Lowlighter engine.

## Limitations and privacy

- A profile repository cannot render arbitrary JavaScript, interactive apps, or custom HTML/CSS layouts. SVGs and regular Markdown links are supported.
- Public GitHub event history is not a complete ledger. The recent-event panel does not imply otherwise.
- Private APEX-G and clinical-agent repositories are not queried, linked as public projects, or included in counts.
- Inferred achievement badges, fabricated awards, paper acceptance, total private contributions, and imagined project milestones are not displayed.
- GitHub usernames are validated before constructing API paths. Dynamic strings are escaped before rendering SVG.
- The generator uses Python standard library only; no API keys are written to the repository.
- The snapshot is public metadata; review \`data/public-snapshot.json\` before publishing if changing the generator's data scope.

## Automation

\`.github/workflows/profile.yml\` refreshes assets on a daily schedule and allows manual execution. It has explicit \`contents: write\` permissions to commit generated changes. Repository Actions settings must permit workflow write access. The default \`GITHUB_TOKEN\` is used; no external paid service is required for the basic snapshot.

Lowlighter currently uses a pinned upstream action version. Some advanced plugins may depend on specific GitHub API permissions and can fail to render with the default token. The workflow treats optional plugin generation as best effort and preserves labelled fallback assets. Missing statistics are not considered zero.

## Visual authorship

Custom header, research map, evidence-loop infographic, radar, and provenance panels are original to this repository. The external analytics renderer is [Lowlighter Metrics](https://github.com/lowlighter/metrics); the workflow references its upstream GitHub Action without vendoring source code.

## Development

\`\`\`bash
python -m unittest discover -s tests -v
GH_TOKEN= python scripts/profile_refresh.py --user Armanasq
\`\`\`

The second command requires access to GitHub's public API. To verify a change without network access, run the unit tests using mocked API responses.
