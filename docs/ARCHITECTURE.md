# Profile architecture

The public GitHub profile README is the product. It is rendered by GitHub, not by a separate website. Its visuals are self-contained SVGs; no client-side scripts or external page permissions are required to view it.

## Data flows

1. `scripts/profile_refresh.py` calls GitHub's public REST API with an optional GitHub Actions token.
2. It enumerates **public repositories owned by Armanasq**, excludes private repositories and other owners, and records a bounded sample of public events.
3. It reads `config/featured.json` to select public projects and supply editorial research-area labels. Only matching verified public repositories appear in the generated radar.
4. It generates `data/public-snapshot.json` alongside SVG assets in `assets/live/`. The lineage panel stores a digest of the exact JSON snapshot and a generation timestamp.
5. The Lowlighter Metrics GitHub Action refreshes the four `assets/metrics/*.svg` panels with additional GitHub telemetry. When an integration is unavailable, source-backed local fallback SVGs provide public statistics rather than invented plugin output.
6. GitHub renders the updated README from the default branch.

## What this profile measures

- The number of public repositories and non-fork repositories owned by the account.
- Total stars on **original public repositories** (not unique stargazers).
- Public follower count reported by GitHub.
- A bounded sample of the account's public events, with an explicit unavailable state.
- Repository push timestamps and the selected research-repository view.
- Additional language, community, calendar, notable, and open-source metrics calculated by the Lowlighter engine.

## Novel verification surfaces

- The **research repository radar** joins curated project identities with live GitHub push timestamps and stars.
- The **research constellation** maps curated public repositories to their editorial research domains, with equal-sized nodes, source-backed GitHub stars and push dates, and an explicit disclaimer that the links do not represent measured similarity.
- The **research evidence footprint** checks the default-branch trees of public projects for six file-presence markers (README, tests, workflows, license, citation, setup). A marker is not a quality rating and does not assert that any code or experiment passed.
- The **provenance panel** records exact source endpoints, refresh time and a snapshot digest.
- Public-source fallback metrics prevent a broken external renderer from leaving empty, misleading panels.

## Limitations and privacy

- A profile repository cannot render arbitrary JavaScript, interactive apps, or custom HTML/CSS layouts. SVGs and regular Markdown links are supported.
- Public GitHub event history is not a complete ledger. The recent-event panel does not imply otherwise.
- Private APEX-G and clinical-agent repositories are not queried, linked as public projects, or included in counts.
- Inferred achievement badges, fabricated awards, paper acceptance, total private contributions, and imagined project milestones are not displayed.
- GitHub usernames are validated before constructing API paths. Dynamic strings are escaped before rendering SVG.
- The generator uses Python standard library only; no API keys are written to the repository.
- The snapshot is public metadata; review `data/public-snapshot.json` before publishing if changing the generator's data scope.

## Automation

`.github/workflows/profile.yml` refreshes assets on a daily schedule and allows manual execution. It has explicit `contents: write` permissions to commit generated changes. Repository Actions settings must permit workflow write access. The default `GITHUB_TOKEN` is used; no external paid service is required for the basic snapshot.

Lowlighter currently uses a pinned upstream action version. Some advanced plugins may depend on specific GitHub API permissions and can fail to render with the default token. The workflow treats optional plugin generation as best effort and preserves labelled fallback assets. Missing statistics are not considered zero.

## Visual authorship

Custom header, research map, evidence-loop infographic, radar, and provenance panels are original to this repository. The external analytics renderer is [Lowlighter Metrics](https://github.com/lowlighter/metrics); the workflow references its upstream GitHub Action without vendoring source code.

## Development

```bash
python -m unittest discover -s tests -v
GH_TOKEN= python scripts/profile_refresh.py --user Armanasq
```

The second command requires access to GitHub's public API. To verify a change without network access, run the unit tests using mocked API responses.

## Upstream metrics versioning and fallback

The Lowlighter action uses the public **v3.34** release tag. Its historical Docker bootstrap identifies the upstream publisher by extracting the prefix before `metrics` from `GITHUB_ACTION`. Custom step IDs like `engineering` cause it to misclassify the invocation as a fork and rebuild the image, which fails when the historical container lacks `xzcat`. Every action step therefore uses an explicit `lowlighter_metrics_*` ID so the upstream Docker image is selected; this is verified against `source/app/action/run.sh` in the upstream repository. The basic public GitHub snapshot and local source-backed metric fallbacks remain independent of Lowlighter.

Both `assets/live/` and `assets/metrics/` are staged before rebasing and pushing the daily refresh. The generated fallback assets must be committed together with the JSON snapshot, otherwise a dirty worktree prevents `git pull --rebase`.

## Isometric graphics and contribution provenance

The README prioritizes original, repo-hosted SVG visuals rather than generic external badge services. The generated project skyline encodes verified public repository stars as isometric extrusion height; zero-star repositories remain present with baseline pedestals. The research-orbit is an editorial diagram and never implies quantified scientific similarity.

`python scripts/render_profile_art.py` first attempts GitHub GraphQL daily contributions with the short-lived workflow token, then a publicly visible HTML calendar with ordinal activity levels as a fallback. Only calendars with at least 300 dated observations are rendered as 3D daily blocks. The source, granularity and dates are retained in `data/contributions.json`. If neither source is available, the output explicitly says so. Test fixtures use synthetic counts only for local QA and are never published as real activity.

All SVGs use native geometry, no external fonts/scripts and explicit alt text. The generator uses Python's standard library. The daily workflow validates XML for these visuals and stages them with the GitHub API snapshot in a single commit.

## Visual composition audit (2026-11-09)

The earlier profile used vertically stacked SVG reports without an editorial layout system. The redesign separates visual responsibilities: 3D contribution geometry for daily history, star-proportional skyline for public project signals, orbital research taxonomy, and a four-layer isometric engineering stack. Lowlighter widgets use asymmetric two-column composition. GitHub Markdown permits static SVG and HTML tables but does not execute interactive WebGL or JavaScript. Technology labels are editorial descriptions, not measured proficiency or proficiency scores. SVG asset existence alone is not evidence of successful GitHub rendering; the rendered profile must be checked independently.
