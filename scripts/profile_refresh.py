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
        "lineage.svg": lineage_svg(snapshot, digest),
    }
    output_dir.mkdir(parents=True, exist_ok=True)
    snapshot_path.parent.mkdir(parents=True, exist_ok=True)
    for filename, contents in files.items():
        (output_dir / filename).write_text(contents, encoding="utf-8")
    snapshot_path.write_text(canonical, encoding="utf-8")


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
