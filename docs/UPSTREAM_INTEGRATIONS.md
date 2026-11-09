# External source integrations

The README now consumes original, publicly documented renderers and APIs.

| Upstream project | Source | Integration | State |
|---|---|---|---|
| Lowlighter Metrics | https://github.com/lowlighter/metrics | Four independently configured metrics action jobs | Existing workflow; inspect actual action outcomes |
| Platane/snk | https://github.com/Platane/snk | `Platane/snk/svg-only@v3` and published animated SVG | Workflow configured; output branch requires successful run |
| github-profile-trophy | https://github.com/ryo-ma/github-profile-trophy | `https://github-profile-trophy.vercel.app/?username=Armanasq` | External service; availability not guaranteed |
| github-readme-streak-stats | https://github.com/DenverCoder1/github-readme-streak-stats | `https://streak-stats.demolab.com/?user=Armanasq` | External service; availability not guaranteed |
| Shields.io | https://github.com/badges/shields | `https://img.shields.io/badge/...` | Existing external badge service |
| GitHub public REST API | https://docs.github.com/en/rest | Verified repository statistics and recent events | Existing Python generator |
| GitHub Issues and Actions | https://docs.github.com/en/actions | Interactive research poll and automated result publishing | Existing workflow |
| Simon Willison's generated README pattern | https://github.com/simonw/simonw | Marker-based README generation | Existing local implementation |

## Provenance

The source projects were inspected, including the actual `Platane/Platane` snake workflow and Lowlighter metrics workflow. Their original actions/endpoints are used directly rather than cloning visual approximations. No private credentials or personal data from other users is copied.

## Constraints

GitHub README cannot execute custom JavaScript or WebGL. Remote image providers can fail or rate-limit. The output branch will not exist until the first successful snake workflow run. GitHub Pages is not required for these images. A browser screenshot audit and upstream service health checks are still required before declaring the design visually complete.
