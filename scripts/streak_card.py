#!/usr/bin/env python3
"""Render dated, evidence-backed GitHub contribution streaks as a standalone SVG."""

import argparse
import html
import json
from datetime import date, datetime, timedelta
from pathlib import Path


BG = "#0b101b"
BORDER = "#304055"
TEXT = "#eaf3f6"
MUTED = "#adbecb"
MINT = "#79d1c2"
GOLD = "#e4b07e"
LEVELS = ("#283647", "#285b55", "#317f70", "#56ab91", "#9be5bb")


def escaped(value):
    return html.escape(str(value), quote=True)


def text(x, y, value, size=16, color=TEXT, weight=400, anchor="start", css=""):
    return (f'<text x="{x}" y="{y}" text-anchor="{anchor}" fill="{color}" '
            f'font-size="{size}" font-family="Arial,Helvetica,sans-serif" '
            f'font-weight="{weight}" class="{css}">{escaped(value)}</text>')


def summary(calendar):
    if calendar.get("status") != "verified":
        return None
    records = {}
    for item in calendar.get("days", []):
        try:
            observed = date.fromisoformat(item["date"])
            value = item.get("count")
            if value is None:
                value = item.get("level")
            if not isinstance(value, int) or isinstance(value, bool) or value < 0:
                continue
            level = item.get("level")
            if not isinstance(level, int) or level not in range(5):
                level = min(4, value) if value else 0
            records[observed] = (value > 0, level)
        except (ValueError, TypeError, KeyError):
            continue
    if len(records) < 300:
        return None
    ordered = sorted(records)
    longest = run = active = 0
    longest_end = None
    previous = None
    for current in ordered:
        if records[current][0]:
            active += 1
            run = run + 1 if previous and current - previous == timedelta(days=1) else 1
            if run > longest:
                longest, longest_end = run, current
        else:
            run = 0
        previous = current
    latest = ordered[-1]
    try:
        snapshot = datetime.fromisoformat(calendar["generated_at_utc"].replace("Z", "+00:00")).date()
    except (ValueError, TypeError, KeyError):
        snapshot = latest
    anchor = min(snapshot, latest)
    fresh = latest >= snapshot - timedelta(days=1)
    if not records.get(anchor, (False, 0))[0] and records.get(anchor - timedelta(days=1), (False, 0))[0]:
        anchor -= timedelta(days=1)
    current_streak = 0
    while records.get(anchor, (False, 0))[0]:
        current_streak += 1
        anchor -= timedelta(days=1)
    return {
        "current": current_streak if fresh else None,
        "longest": longest,
        "longest_start": longest_end - timedelta(days=longest - 1) if longest_end else None,
        "longest_end": longest_end,
        "active": active,
        "days": len(records),
        "latest": latest,
        "snapshot": snapshot,
        "records": records,
        "source": calendar.get("source") or "GitHub contribution calendar",
        "granularity": calendar.get("granularity"),
    }


def render(calendar):
    stats = summary(calendar)
    header = [
        '<svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1200 388" role="img" '
        'aria-labelledby="streak-title streak-desc">',
        '<title id="streak-title">GitHub contribution streak</title>',
        f'<desc id="streak-desc">{escaped("Current, longest and active contribution days from GitHub. Values use a dated UTC contribution calendar, not commit timestamps.")}</desc>',
        '<defs>',
        '<linearGradient id="panel-bg" x1="0" y1="0" x2="1" y2="1">'
        '<stop stop-color="#101c2c"/><stop offset="1" stop-color="#0a111b"/></linearGradient>',
        '<linearGradient id="accent" x1="0" x2="1"><stop stop-color="#47bda8"/>'
        '<stop offset="1" stop-color="#d7f3bb"/></linearGradient>',
        '<radialGradient id="halo"><stop stop-color="#2c907d" stop-opacity=".22"/>'
        '<stop offset="1" stop-color="#2c907d" stop-opacity="0"/></radialGradient>',
        '<style type="text/css"><![CDATA[',
        '@keyframes arrive{from{opacity:0;transform:translateY(8px)}to{opacity:1;transform:translateY(0)}}',
        '@keyframes breathe{0%,100%{opacity:.55}50%{opacity:1}}',
        '.day{animation:arrive .65s ease-out both}',
        '.pulse{animation:breathe 3s ease-in-out infinite}',
        '@media(prefers-reduced-motion:reduce){.day,.pulse{animation:none}}',
        ']]></style></defs>',
        '<rect x="1" y="1" width="1198" height="386" rx="18" fill="url(#panel-bg)" '
        'stroke="#304055" stroke-width="2"/>',
        '<ellipse cx="1007" cy="46" rx="250" ry="175" fill="url(#halo)"/>',
        '<rect x="39" y="38" width="5" height="36" rx="2" fill="url(#accent)"/>',
        text(60, 55, "CONTRIBUTION CADENCE", 22, TEXT, 700),
        text(60, 77, "Measured from GitHub contribution days · rolling annual window", 14, MUTED),
    ]
    if stats:
        through = stats["latest"].isoformat()
        stamp = f'SNAPSHOT {stats["snapshot"].isoformat()} UTC · LAST DAY {through}'
        longest_span = (f'{stats["longest_start"].strftime("%b %d")} – '
                        f'{stats["longest_end"].strftime("%b %d, %Y")}') if stats["longest"] else "No observed activity"
        metrics = [
            ("CURRENT STREAK", "—" if stats["current"] is None else str(stats["current"]),
             "Snapshot too old" if stats["current"] is None else "Consecutive active days", MINT),
            (f'LONGEST STREAK · {stats["days"]}D', str(stats["longest"]), longest_span, GOLD),
            (f'ACTIVE DAYS · {stats["days"]}D', str(stats["active"]), "Days with at least one contribution", "#a6c8f3"),
        ]
    else:
        stamp = "DATA UNAVAILABLE · NO ESTIMATED VALUES"
        metrics = [
            ("CURRENT STREAK", "—", "Awaiting verified contribution data", MINT),
            ("LONGEST STREAK", "—", "Not available", GOLD),
            ("ACTIVE DAYS", "—", "Not available", "#a6c8f3"),
        ]
    header.extend([text(1154, 59, stamp, 12, MUTED, 600, "end"),
                   '<path d="M40 92H1160" stroke="#304055" stroke-width="1"/>'])
    for i, (heading, value, detail, accent) in enumerate(metrics):
        x = 40 + 378 * i
        header.extend([
            f'<rect x="{x}" y="109" width="365" height="128" rx="12" '
            'fill="#132232" stroke="#304055"/>',
            f'<rect x="{x+1}" y="123" width="3" height="98" rx="1.5" fill="{accent}"/>',
            text(x+20, 136, heading, 13, MUTED, 700),
            text(x+19, 201, value, 60, accent, 700, css="pulse" if i == 0 else ""),
            text(x+116, 197, "DAYS" if value != "—" else "", 12, MUTED, 700),
            text(x+20, 222, detail, 13, MUTED),
        ])
    header += [text(41, 273, "RECENT CONTRIBUTION DAYS", 13, MUTED, 700),
               text(1158, 273, "OLDEST  →  NEWEST", 12, MUTED, 400, "end"),
               '<path d="M40 343H1160" stroke="#304055"/>']
    if stats:
        end = stats["latest"]
        for i in range(56):
            current_date = end - timedelta(days=55-i)
            on, level = stats["records"].get(current_date, (False, 0))
            color = LEVELS[level] if on else LEVELS[0]
            height = 9 + level * 8 if on else 7
            x = 45 + i * 19.85
            y = 339 - height
            opacity = 0.95 if on else 0.55
            header.append(
                f'<rect x="{x:.2f}" y="{y}" width="11" height="{height}" rx="3" '
                f'fill="{color}" opacity="{opacity}" class="day" '
                f'style="animation-delay:{i * .012:.3f}s">'
                f'<title>{current_date.isoformat()}: {"contribution recorded" if on else "no contribution recorded"}</title>'
                '</rect>'
            )
        footer = ("Source: " + stats["source"] + "  |  " +
                  ("Daily counts" if stats["granularity"] == "daily-count" else "Activity levels") +
                  "  |  Longest streak limited to the observed window")
    else:
        header.append(text(50, 327, "No verified daily observations available", 17, MUTED))
        footer = "Source: unavailable · No streak values inferred from repository push timestamps"
    header += [text(41, 369, footer, 12, MUTED), '</svg>\n']
    return "".join(header)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("--contributions", type=Path, default=Path("data/contributions.json"))
    parser.add_argument("--output", type=Path, default=Path("assets/visuals/streak.svg"))
    args = parser.parse_args()
    data = json.loads(args.contributions.read_text(encoding="utf-8"))
    args.output.parent.mkdir(parents=True, exist_ok=True)
    args.output.write_text(render(data), encoding="utf-8")


if __name__ == "__main__":
    main()
