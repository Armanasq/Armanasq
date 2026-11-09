#!/usr/bin/env python3
import argparse
import html
import json
from pathlib import Path

START_FEATURED = "<!-- featured:start -->"
END_FEATURED = "<!-- featured:end -->"
START_ACTIVITY = "<!-- activity:start -->"
END_ACTIVITY = "<!-- activity:end -->"

def escape(value):
    return str(value).replace("|", "\\|").replace("<", "&lt;").replace(">", "&gt;")

def replace_section(source, start, end, body):
    if source.count(start) != 1 or source.count(end) != 1:
        raise ValueError("Missing or duplicated generated section markers")
    left, remainder = source.split(start, 1)
    _, right = remainder.split(end, 1)
    return left + start + "\n" + body + "\n" + end + right

def render(readme, snapshot):
    featured = sorted(snapshot.get("featured", []), key=lambda r: (-int(r.get("stars") or 0), r.get("name", "")))[:6]
    rows = ["| Repository | Research area | Stars |", "|:--|:--|--:|"]
    for item in featured:
        url = item["url"]
        if not url.startswith("https://github.com/Armanasq/"):
            raise ValueError("Unexpected repository URL")
        rows.append(f'| [{escape(item["name"])}]({url}) | {escape(item.get("area", "Unclassified"))} | {int(item.get("stars") or 0)} |')
    readme = replace_section(readme, START_FEATURED, END_FEATURED, "\n".join(rows))
    events = ["| Date (UTC) | Activity | Repository |", "|:--|:--|:--|"]
    for event in snapshot.get("events", [])[:5]:
        url = event.get("url", "")
        if not url.startswith("https://github.com/Armanasq/"):
            continue
        events.append(f'| {escape(event.get("date", "")[:10])} | {escape(event.get("action", ""))} | [{escape(event.get("repository", ""))}]({url}) |')
    return replace_section(readme, START_ACTIVITY, END_ACTIVITY, "\n".join(events))

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--readme", type=Path, default=Path("README.md"))
    parser.add_argument("--snapshot", type=Path, default=Path("data/public-snapshot.json"))
    args = parser.parse_args()
    text = args.readme.read_text(encoding="utf-8")
    data = json.loads(args.snapshot.read_text(encoding="utf-8"))
    rendered = render(text, data)
    if rendered != text:
        args.readme.write_text(rendered, encoding="utf-8")

if __name__ == "__main__":
    main()
