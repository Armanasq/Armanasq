#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path

def replace_section(source, start, end, body):
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError("Missing or duplicated section markers")
    before, rest = source.split(start, 1)
    _, after = rest.split(end, 1)
    return before + start + "\n" + body + "\n" + end + after

def safe(value):
    return html.escape(str(value or ""), quote=True)

def render(readme, snapshot):
    featured = sorted(snapshot.get("featured", []), key=lambda r: (-int(r.get("stars") or 0), r.get("name", "")))[:6]
    rows = ['<table><tr><th>Repository</th><th>Research area</th><th>Stars</th></tr>']
    for item in featured:
        url = item["url"]
        if not url.startswith("https://github.com/Armanasq/"):
            raise ValueError("Unexpected repository URL")
        name = item["name"]
        label = name if len(name) <= 49 else name[:46] + "..."
        rows.append(f'<tr><td><a href="{safe(url)}">{safe(label)}</a></td><td>{safe(item.get("area", "Unclassified"))}</td><td align="right">{int(item.get("stars") or 0)}</td></tr>')
    rows.append("</table>")
    readme = replace_section(readme, "<!-- featured:start -->", "<!-- featured:end -->", "\n".join(rows))
    events = ['<table><tr><th>Date</th><th>Activity</th><th>Repository</th></tr>']
    for item in snapshot.get("events", [])[:5]:
        url = item.get("url", "")
        if not url.startswith("https://github.com/Armanasq/"):
            continue
        events.append(f'<tr><td>{safe(item.get("date", "")[:10])}</td><td>{safe(item.get("action", ""))}</td><td><a href="{safe(url)}">{safe(item.get("repository", ""))}</a></td></tr>')
    events.append("</table>")
    return replace_section(readme, "<!-- activity:start -->", "<!-- activity:end -->", "\n".join(events))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument("--snapshot", type=Path, default=Path("data/public-snapshot.json"))
    args = parser.parse_args()
    original = args.readme.read_text(encoding="utf-8")
    result = render(original, json.loads(args.snapshot.read_text(encoding="utf-8")))
    if result != original:
        args.readme.write_text(result, encoding="utf-8")

if __name__ == "__main__":
    main()
