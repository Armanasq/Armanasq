#!/usr/bin/env python3
import argparse
import html
import json
import os
import urllib.request
from pathlib import Path

API = "https://api.github.com/repos/Armanasq/Armanasq/issues?state=all&per_page=100&page="
KEYS = ("A", "B", "C")
NAMES = {"A": "Data leakage / split", "B": "Distribution shift", "C": "Baseline mismatch"}

def tally(issues):
    votes = {}
    for issue in issues:
        if "pull_request" in issue:
            continue
        title = issue.get("title", "")
        key = title.removeprefix("Research challenge: ").strip()
        if title != "Research challenge: " + key or key not in KEYS:
            continue
        user = (issue.get("user") or {}).get("login", "").lower()
        if user and user not in votes:
            votes[user] = key
    return {k: sum(v == k for v in votes.values()) for k in KEYS}

def fetch():
    token = os.getenv("GH_TOKEN", "")
    headers = {"Accept": "application/vnd.github+json", "User-Agent": "research-challenge"}
    if token:
        headers["Authorization"] = "Bearer " + token
    issues = []
    for page in range(1, 11):
        request = urllib.request.Request(API + str(page), headers=headers)
        with urllib.request.urlopen(request, timeout=20) as response:
            batch = json.load(response)
        issues.extend(batch)
        if len(batch) < 100:
            break
    return issues

def svg(counts):
    total = sum(counts.values())
    out = ['<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 900 225" role="img" aria-label="Research challenge vote tally">',
           '<rect width="900" height="225" rx="12" fill="#0d1320"/>',
           '<text x="25" y="35" fill="#dce6f6" font-family="Arial" font-size="18" font-weight="bold">Research challenge / public responses</text>']
    colors = {"A": "#9e8df5", "B": "#64c5d3", "C": "#d5b17b"}
    for index, key in enumerate(KEYS):
        y = 73 + index * 49
        width = 590 * counts[key] / max(total, 1)
        out += [f'<text x="25" y="{y}" fill="#dce6f6" font-family="Arial" font-size="14">{html.escape(key + "  " + NAMES[key])}</text>',
                f'<rect x="250" y="{y-14}" width="590" height="18" rx="5" fill="#263249"/>',
                f'<rect x="250" y="{y-14}" width="{width:.1f}" height="18" rx="5" fill="{colors[key]}"/>',
                f'<text x="858" y="{y}" fill="#dce6f6" font-family="Arial" font-size="14">{counts[key]}</text>']
    out += [f'<text x="25" y="212" fill="#9aa8bf" font-family="Arial" font-size="12">{total} unique public participants · first valid issue per account</text>', '</svg>']
    return "\n".join(out) + "\n"

def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--output", type=Path, default=Path("assets/interactive/research-challenge.svg"))
    args = parser.parse_args()
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(svg(tally(fetch())), encoding="utf-8")

if __name__ == "__main__":
    main()
