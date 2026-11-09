#!/usr/bin/env python3
"""Generate a source-labelled public GitHub research profile from the REST API."""

import argparse
import hashlib
import html
import json
import os
import re
import urllib.error
import urllib.parse
import urllib.request
from collections import Counter
from datetime import datetime, timezone
from pathlib import Path


API = "https://api.github.com"
BG = "#0c1520"
PANEL = "#12222d"
LINE = "#294050"
FG = "#eaf2f2"
MUTED = "#a2b7c1"
MINT = "#79d1c2"
GOLD = "#e4b07e"


def escaped(value):
    return html.escape(str(value), quote=True)


def compact(value, limit=56):
    value = str(value).replace("\n", " ").strip()
    return value if len(value) <= limit else value[:limit - 1] + "\u2026"


def parse_date(value):
    if not value:
        return None
    try:
        return datetime.fromisoformat(value.replace("Z", "+00:00")).astimezone(timezone.utc)
    except (TypeError, ValueError):
        return None


def day(value):
    parsed = parse_date(value)
    return parsed.strftime("%Y-%m-%d") if parsed else "Not available"


def fetch_json(path, token=""):
    req = urllib.request.Request(
        API + path,
        headers={
            "Accept": "application/vnd.github+json",
            "User-Agent": "Armanasq-public-profile-generator",
            "X-GitHub-Api-Version": "2022-11-28",
            **({"Authorization": "Bearer " + token} if token else {}),
        },
    )
    try:
        with urllib.request.urlopen(req, timeout=25) as response:
            return json.load(response)
    except urllib.error.HTTPError as error:
        raise RuntimeError("GitHub API request failed with HTTP " + str(error.code)) from error
    except urllib.error.URLError as error:
        raise RuntimeError("GitHub API request failed due to a network error") from error


def list_public_repositories(login, token):
    quoted = urllib.parse.quote(login, safe="")
    results = []
    for page in range(1, 16):
        part = fetch_json(
            f"/users/{quoted}/repos?type=owner&sort=updated&per_page=100&page={page}", token
        )
        if not isinstance(part, list):
            raise RuntimeError("GitHub repository response was not a list")
        results.extend(
            item for item in part
            if item.get("private") is False
            and item.get("owner", {}).get("login", "").casefold() == login.casefold()
        )
        if len(part) < 100:
            break
    else:
        raise RuntimeError("Pagination limit reached without confirming the final page")
    return results


SIGNAL_NAMES = ("readme", "tests", "workflows", "license", "citation", "setup")


def file_marker_signals(tree):
    if not isinstance(tree, dict) or tree.get("truncated"):
        return {name: None for name in SIGNAL_NAMES}
    entries = tree.get("tree")
    if not isinstance(entries, list):
        return {name: None for name in SIGNAL_NAMES}
    paths = {
        str(item.get("path", "")).lower()
        for item in entries
        if item.get("type") == "blob"
    }
    readmes = {"readme.md", "readme.rst", "readme.txt"}
    licenses = {"license", "license.md", "license.txt", "copying", "copying.md"}
    citations = {"citation.cff", ".github/citation.cff", "citation.bib"}
    setup_files = {
        "requirements.txt", "pyproject.toml", "setup.py", "environment.yml",
        "environment.yaml", "dockerfile", "package.json", "cargo.toml",
        "go.mod", "pom.xml", "uv.lock", "poetry.lock", "pipfile",
    }
    test_ext = (".py", ".rs", ".go", ".java", ".cpp", ".cc", ".js", ".jsx", ".ts", ".tsx")
    tests = any(
        path.startswith(("tests/", "test/", "__tests__/"))
        and path.endswith(test_ext)
        for path in paths
    )
    return {
        "readme": bool(paths & readmes),
        "tests": tests,
        "workflows": any(
            path.startswith(".github/workflows/") and path.endswith((".yml", ".yaml"))
            for path in paths
        ),
        "license": bool(paths & licenses),
        "citation": bool(paths & citations),
        "setup": bool(paths & setup_files),
    }


def inspect_public_repo(repo, token):
    fullname = repo.get("full_name")
    branch = repo.get("default_branch")
    if not fullname or not branch:
        return {"status": "unavailable", "source": None,
                "checks": {name: None for name in SIGNAL_NAMES}}
    path = (
        "/repos/" + urllib.parse.quote(fullname, safe="/")
        + "/git/trees/" + urllib.parse.quote(branch, safe="") + "?recursive=1"
    )
    try:
        tree = fetch_json(path, token)
    except RuntimeError:
        return {"status": "unavailable", "source": API + path,
                "checks": {name: None for name in SIGNAL_NAMES}}
    truncated = not isinstance(tree, dict) or bool(tree.get("truncated"))
    return {
        "status": "incomplete" if truncated else "complete",
        "source": API + path,
        "checks": file_marker_signals(tree),
    }


def event_label(event):
    kind = event.get("type", "")
    payload = event.get("payload") or {}
    action = compact(payload.get("action", ""), 22)
    labels = {
        "PushEvent": "Pushed code",
        "PullRequestEvent": "Pull request" + (": " + action if action else ""),
        "IssuesEvent": "Issue" + (": " + action if action else ""),
        "IssueCommentEvent": "Commented",
        "CreateEvent": "Created branch or tag",
        "ReleaseEvent": "Release" + (": " + action if action else ""),
        "WatchEvent": "Starred repository",
        "ForkEvent": "Forked repository",
        "PublicEvent": "Published repository",
        "PullRequestReviewEvent": "Reviewed pull request",
    }
    return labels.get(kind, compact(kind.removesuffix("Event"), 32) or "Other public event")


def build_snapshot(login, featured, token=""):
    if not re.fullmatch(r"[A-Za-z0-9-]{1,39}", login):
        raise ValueError("Invalid GitHub username")
    quoted = urllib.parse.quote(login, safe="")
    user = fetch_json(f"/users/{quoted}", token)
    repos = list_public_repositories(login, token)
    originals = [repo for repo in repos if not repo.get("fork")]
    try:
        events_raw = fetch_json(f"/users/{quoted}/events/public?per_page=100&page=1", token)
        if not isinstance(events_raw, list):
            raise RuntimeError("Invalid events response")
        events_status = "available"
    except RuntimeError:
        events_raw = []
        events_status = "unavailable"

    events = [
        {
            "date": item.get("created_at"),
            "repository": (item.get("repo") or {}).get("name", ""),
            "action": event_label(item),
            "url": "https://github.com/" + (item.get("repo") or {}).get("name", ""),
        }
        for item in events_raw
        if (item.get("repo") or {}).get("name", "").startswith(login + "/")
    ]

    events.sort(key=lambda item: item.get("date") or "", reverse=True)

    public = {item.get("name", "").casefold(): item for item in repos}
    selected = []
    for record in featured:
        name = record.get("name", "")
        item = public.get(name.casefold())
        if item is None:
            continue
        selected.append(
            {
                "name": item["name"],
                "area": record.get("area", "Research"),
                "description": record.get("description", ""),
                "url": item["html_url"],
                "stars": item.get("stargazers_count", 0),
                "pushed_at": item.get("pushed_at"),
                "language": item.get("language"),
                "file_signals": inspect_public_repo(item, token),
            }
        )

    lang_counts = Counter(repo["language"] for repo in originals if repo.get("language"))
    recent_pushes = sorted(originals, key=lambda r: r.get("pushed_at") or "", reverse=True)
    return {
        "schema_version": 1,
        "generated_at_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "login": login,
        "scope": "Public GitHub REST API; original and forked owned repositories",
        "statistics": {
            "public_repositories": len(repos),
            "original_public_repositories": len(originals),
            "forks": len(repos) - len(originals),
            "stars_on_original_public_repositories": sum(
                item.get("stargazers_count") or 0 for item in originals
            ),
            "public_followers": user.get("followers"),
            "sampled_public_events": len(events) if events_status == "available" else None,
        },
        "language_repository_counts": dict(lang_counts.most_common(12)),
        "featured": selected,
        "recent_public_repository_pushes": [
            {"name": repo["name"], "date": repo.get("pushed_at"), "url": repo["html_url"]}
            for repo in recent_pushes[:7]
        ],
        "events": events[:8],
        "events_status": events_status,
        "sources": [
            API + f"/users/{quoted}",
            API + f"/users/{quoted}/repos",
            API + f"/users/{quoted}/events/public",
        ] + [
            item["file_signals"]["source"] for item in selected
            if item["file_signals"]["source"]
        ],
        "limitations": [
            "Only public repositories are included; private work is intentionally excluded.",
            "Stars are summed across original public repositories and are not unique people.",
            "Event API exposes a bounded recent sample, not a complete contribution history.",
            "Language counts measure the number of repositories with that primary language.",
            "Repository pushed_at timestamps do not measure research quality or completion.",
        ],
    }


def svg_frame(title, description, height, contents):
    return (
        '<svg xmlns="http://www.w3.org/2000/svg" role="img" '
        f'aria-labelledby="title desc" viewBox="0 0 1100 {height}">'
        f'<title id="title">{escaped(title)}</title>'
        f'<desc id="desc">{escaped(description)}</desc>'
        f'<rect x="1" y="1" width="1098" height="{height-2}" rx="13" fill="{BG}" stroke="{LINE}"/>'
        f'{contents}</svg>\n'
    )


def label(x, y, value, size=16, color=FG, weight=400, anchor="start"):
    return (
        f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" '
        f'font-family="Arial,Helvetica,sans-serif" font-size="{size}" font-weight="{weight}">'
        f'{escaped(value)}</text>'
    )


def panel(title, subtitle, rows, footer):
    height = max(240, 115 + 52 * len(rows) + 41)
    parts = [
        label(28, 39, title, 23, FG, 700),
        label(28, 65, subtitle, 14, MUTED),
        f'<path d="M28 80 H1072" stroke="{LINE}"/>',
    ]
    for i, (name, value) in enumerate(rows):
        y = 116 + 52 * i
        parts.append(
            f'<rect x="27" y="{y-26}" width="1046" height="45" rx="6" '
            f'fill="{PANEL if i % 2 == 0 else BG}"/>'
        )
        parts.append(label(44, y + 3, compact(name, 66), 17, FG, 600))
        parts.append(label(1055, y + 3, compact(value, 41), 16, MINT, 400, "end"))
    parts.append(label(28, height - 17, compact(footer, 135), 12, MUTED))
    return svg_frame(title, subtitle + " " + footer, height, "".join(parts))


def overview_svg(snapshot):
    stats = snapshot["statistics"]
    items = [
        ("PUBLIC REPOSITORIES", stats["public_repositories"], "Owned, visible repositories"),
        ("ORIGINAL PROJECTS", stats["original_public_repositories"], "Public repositories excluding forks"),
        ("OPEN-SOURCE STARS", stats["stars_on_original_public_repositories"], "Sum on original public repositories"),
        ("PUBLIC FOLLOWERS", stats["public_followers"], "GitHub public profile"),
    ]
    parts = [
        label(28, 40, "PUBLIC ENGINEERING SIGNALS", 23, FG, 700),
        label(28, 67, "Source: GitHub REST API / owned public repositories", 14, MUTED),
    ]
    for i, (title, number, detail) in enumerate(items):
        x = 28 + (i % 2) * 528
        y = 90 + (i // 2) * 118
        parts.append(f'<rect x="{x}" y="{y}" width="514" height="106" rx="12" fill="{PANEL}" stroke="{LINE}"/>')
        parts.append(label(x + 19, y + 30, title, 13, MUTED, 700))
        parts.append(label(x + 19, y + 75, "Unavailable" if number is None else f"{number:,}", 36, MINT, 700))
        parts.append(label(x + 207, y + 75, detail, 13, MUTED))
    stamp = day(snapshot["generated_at_utc"])
    parts.append(label(28, 345, "Snapshot: " + stamp + " UTC   |   Excludes all private repositories", 13, MUTED))
    return svg_frame("Verified public engineering signals", "Four public GitHub statistics with explicit scope.", 365, "".join(parts))


def activity_svg(snapshot):
    events = snapshot["events"]
    if events:
        rows = [
            (day(e["date"]) + "  " + e["action"], compact(e["repository"], 45))
            for e in events[:6]
        ]
        return panel(
            "RECENT PUBLIC ACTIVITY",
            "GitHub public events; bounded to the most recent events returned by the API",
            rows,
            "Event feed is a sample, not a total historical contribution count. " + day(snapshot["generated_at_utc"]),
        )
    pushes = snapshot["recent_public_repository_pushes"]
    rows = [(compact(p["name"], 60), "Last push " + day(p["date"])) for p in pushes[:6]]
    return panel(
        "RECENT PUBLIC REPOSITORY PUSHES",
        "GitHub push timestamps, not an inferred personal activity feed",
        rows or [("No public repository pushes were returned", "Not available")],
        "Public events: " + snapshot["events_status"] + "; snapshot " + day(snapshot["generated_at_utc"]),
    )


def radar_svg(snapshot):
    rows = []
    for repo in snapshot["featured"]:
        rows.append(
            (
                compact(repo["area"] + "  /  " + repo["name"], 63),
                "Pushed " + day(repo["pushed_at"]) + "  |  " + str(repo["stars"]) + " stars",
            )
        )
    return panel(
        "RESEARCH REPOSITORY RADAR",
        "Curated public projects; values are live repository metadata, not subjective scores",
        rows[:9] or [("No curated public repositories were returned", "Not available")],
        "Research area labels come from config/featured.json; no private projects are queried.",
    )


def constellation_svg(snapshot):
    items = snapshot.get("featured", [])[:8]
    if not items:
        return panel(
            "PUBLIC RESEARCH CONSTELLATION",
            "No featured public repositories were returned by the GitHub API.",
            [("Verified research systems", "Not available")],
            "Nodes will be populated from source-backed GitHub metadata.",
        )
    coords = [(27, 91), (27, 208), (27, 325), (27, 442),
              (747, 91), (747, 208), (747, 325), (747, 442)]
    colors = (MINT, GOLD, "#83b7e8", "#c3a6e5")
    content = [
        label(28, 39, "RESEARCH CONSTELLATION", 24, FG, 700),
        label(28, 64, "Verified public projects / editorial research domains / equal-sized nodes", 14, MUTED),
    ]
    for index, item in enumerate(items):
        x, y = coords[index]
        right_side = index >= 4
        entry = (x if right_side else x + 326)
        anchor = "M " + str(entry) + " " + str(y + 47)
        ctrl1 = 580 if right_side else 520
        content.append(
            f'<path d="{anchor} C {ctrl1} {y + 47} {ctrl1} 322 550 322" '
            f'fill="none" stroke="{LINE}" stroke-width="1.5"/>'
        )
    content += [
        '<circle cx="550" cy="322" r="91" fill="#142a34" stroke="' + MINT + '" stroke-width="2"/>',
        '<circle cx="550" cy="322" r="70" fill="none" stroke="' + GOLD + '" stroke-width="1" stroke-dasharray="4 8"/>',
        label(550, 304, "RESEARCH", 22, FG, 700, "middle"),
        label(550, 332, "SYSTEMS", 22, FG, 700, "middle"),
        label(550, 356, "EVIDENCE / STATE / MODEL", 12, MUTED, 400, "middle"),
    ]
    for index, item in enumerate(items):
        x, y = coords[index]
        color = colors[index % len(colors)]
        short = compact(item.get("name", "Unknown repository"), 34)
        stars = item.get("stars")
        star_label = str(stars) + " stars" if isinstance(stars, int) else "Stars unknown"
        pushed = day(item.get("pushed_at"))
        content.append(
            f'<rect x="{x}" y="{y}" width="326" height="94" rx="9" '
            f'fill="{PANEL}" stroke="{LINE}"/>'
        )
        content.append(
            f'<rect x="{x}" y="{y + 17}" width="4" height="58" rx="2" fill="{color}"/>'
        )
        content.append(label(x + 15, y + 23, compact(item.get("area", "Research"), 40), 12, color, 700))
        content.append(label(x + 15, y + 51, short, 14, FG, 600))
        content.append(label(x + 15, y + 77, star_label + "  /  push " + pushed, 12, MUTED))
    content.append(label(
        28, 580,
        "Relationships are editorial research categories, not inferred co-authorship or measured project similarity.",
        12, MUTED,
    ))
    return svg_frame(
        "Source-grounded research constellation",
        "Featured public repositories connected to the author's research programme. "
        "Star counts and push dates are verified public metadata. Node size carries no numeric meaning.",
        600, "".join(content),
    )


def readiness_svg(snapshot):
    columns = [
        ("README", "readme", 582),
        ("TESTS", "tests", 676),
        ("WORKFLOW", "workflows", 773),
        ("LICENSE", "license", 877),
        ("CITE", "citation", 968),
        ("SETUP", "setup", 1044),
    ]
    featured = snapshot.get("featured", [])[:8]
    height = 140 + 53 * max(1, len(featured)) + 38
    parts = [
        label(27, 40, "RESEARCH EVIDENCE FOOTPRINT", 23, FG, 700),
        label(27, 66, "Default-branch file markers, not a test pass rate or research-quality score", 14, MUTED),
        label(27, 112, "CURATED PUBLIC REPOSITORY", 12, MUTED, 700),
    ]
    for heading, _, x in columns:
        parts.append(label(x, 112, heading, 12, MUTED, 700, "middle"))
    for index, item in enumerate(featured):
        y = 146 + index * 53
        parts.append(
            f'<rect x="26" y="{y-22}" width="1047" height="46" rx="6" '
            f'fill="{PANEL if index % 2 == 0 else BG}"/>'
        )
        parts.append(label(42, y + 6, compact(item["name"], 46), 15, FG, 600))
        checks = item.get("file_signals", {}).get("checks", {})
        for _, key, x in columns:
            value = checks.get(key)
            mark = "YES" if value is True else "NO" if value is False else "?"
            color = MINT if value is True else MUTED if value is False else GOLD
            parts.append(label(x, y + 6, mark, 13, color, 700, "middle"))
    if not featured:
        parts.append(label(40, 153, "No selected public projects available", 16, MUTED))
    parts.append(label(27, height - 18,
        "YES: marker found  /  NO: marker absent  /  ?: API result incomplete. Presence does not establish correctness.",
        12, MUTED))
    return svg_frame(
        "Public research evidence footprint",
        "Inspectability matrix derived from GitHub default-branch trees; checks indicate file presence only.",
        height, "".join(parts)
    )


def local_fallback_metrics(snapshot):
    stats = snapshot["statistics"]
    lang = list(snapshot.get("language_repository_counts", {}).items())[:7]
    engineering = panel(
        "PRIMARY LANGUAGES / PUBLIC REPOSITORIES",
        "Count of original public repositories grouped by primary language",
        [(key, str(value) + " repositories") for key, value in lang]
        or [("Language metadata", "Not available")],
        "Local public-GitHub fallback. Language counts are not lines of code.",
    )
    events = snapshot.get("events", [])
    chronicle = panel(
        "PUBLIC ACTIVITY / VERIFIED EVENTS",
        "Event API sample. An isometric calendar requires a successful Lowlighter render.",
        [(day(item["date"]) + "  " + item["action"], compact(item["repository"], 42))
         for item in events[:5]] or [("Event feed", snapshot["events_status"])],
        "Local public-GitHub fallback. Not a complete contribution calendar.",
    )
    recognition = panel(
        "PUBLIC COMMUNITY / FACTUAL SIGNALS",
        "Verified public signals; GitHub achievements are rendered by Lowlighter when available.",
        [
            ("Public followers", str(stats["public_followers"])),
            ("Stars on original public projects", str(stats["stars_on_original_public_repositories"])),
            ("Public original repositories", str(stats["original_public_repositories"])),
            ("Achievement and notable badges", "Upstream metrics unavailable"),
        ],
        "Local public-GitHub fallback. This view does not invent achievements.",
    )
    ecosystem = panel(
        "FEATURED PUBLIC REPOSITORIES",
        "Curated published research and engineering projects",
        [(compact(item["name"], 63), str(item["stars"]) + " stars")
         for item in sorted(snapshot.get("featured", []), key=lambda r: -r["stars"])[:6]]
        or [("Featured public projects", "Not available")],
        "Local public-GitHub fallback. Star counts are per repository.",
    )
    return {
        "engineering.svg": engineering,
        "chronicle.svg": chronicle,
        "recognition.svg": recognition,
        "ecosystem.svg": ecosystem,
    }


def write_metric_fallbacks(snapshot, assets_root):
    output = assets_root / "metrics"
    output.mkdir(parents=True, exist_ok=True)
    for name, svg in local_fallback_metrics(snapshot).items():
        path = output / name
        if path.exists():
            existing = path.read_text(encoding="utf-8")
            can_replace = (
                'data-generator="public-github-fallback"' in existing
                or "Initial panel" in existing
                or "Live snapshot pending" in existing
                or "Live scan pending" in existing
                or "Requires a successful Lowlighter action run" in existing
            )
            if not can_replace:
                continue
        svg = svg.replace(
            "<svg ", '<svg data-generator="public-github-fallback" ', 1
        )
        path.write_text(svg, encoding="utf-8")


def lineage_svg(snapshot, digest):
    rows = [
        ("Public repository data", "GitHub REST API"),
        ("Data boundary", "Public, user-owned repositories only"),
        ("Original projects", str(snapshot["statistics"]["original_public_repositories"])),
        ("Public events endpoint", snapshot["events_status"]),
        ("Snapshot timestamp (UTC)", snapshot["generated_at_utc"]),
        ("Snapshot SHA-256 (first 24 chars)", digest[:24]),
        ("Rendering engine", "Python standard library, no dynamic JavaScript"),
    ]
    return panel(
        "PROVENANCE & FRESHNESS",
        "Every number is traceable to the accompanying public snapshot",
        rows,
        "Source: data/public-snapshot.json. Unavailable values remain unavailable.",
    )


def write_profile(snapshot, output_dir, snapshot_path):
    output_dir = Path(output_dir)
    snapshot_path = Path(snapshot_path)
    canonical = json.dumps(snapshot, ensure_ascii=False, sort_keys=True, indent=2) + "\n"
    digest = hashlib.sha256(canonical.encode("utf-8")).hexdigest()
    files = {
        "overview.svg": overview_svg(snapshot),
        "activity.svg": activity_svg(snapshot),
        "research-radar.svg": radar_svg(snapshot),
        "constellation.svg": constellation_svg(snapshot),
        "readiness.svg": readiness_svg(snapshot),
        "lineage.svg": lineage_svg(snapshot, digest),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    for filename, contents in files.items():
        (output_dir / filename).write_text(contents, encoding="utf-8")
    snapshot_path.write_text(canonical, encoding="utf-8")
    write_metric_fallbacks(snapshot, output_dir.parent)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--user", default="Armanasq")
    parser.add_argument("--config", default="config/featured.json")
    parser.add_argument("--out", default="assets/live")
    parser.add_argument("--snapshot", default="data/public-snapshot.json")
    args = parser.parse_args()
    with Path(args.config).open(encoding="utf-8") as stream:
        config = json.load(stream)
    snapshot = build_snapshot(args.user, config["featured"], os.getenv("GH_TOKEN", ""))
    write_profile(snapshot, args.out, args.snapshot)
    print(
        "Rendered public snapshot:",
        snapshot["statistics"]["public_repositories"],
        "repositories,",
        len(snapshot["featured"]),
        "featured links,",
        len(snapshot["events"]),
        "recent events",
    )


if __name__ == "__main__":
    main()
