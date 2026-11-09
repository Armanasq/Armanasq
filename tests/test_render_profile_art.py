import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import render_profile_art as art


class ProfileArtTests(unittest.TestCase):
    def test_skyline_uses_real_stars(self):
        snapshot = {"generated_at_utc": "2026-11-09T00:00:00Z", "featured": [
            {"name": "OpenSLAM", "stars": 4}, {"name": "Deep-VO", "stars": 1}
        ]}
        svg = art.skyline(snapshot)
        ET.fromstring(svg)
        self.assertIn("4 stars", svg)
        self.assertIn("1 stars", svg)
        self.assertNotIn("private", svg.lower().split("4 stars")[0])

    def test_missing_calendar_does_not_fabricate(self):
        svg = art.calendar_svg({"status": "unavailable", "days": []})
        ET.fromstring(svg)
        self.assertIn("unavailable", svg)
        self.assertNotIn("<polygon", svg)

    def test_calendar_uses_365_daily_observations(self):
        start = date(2025, 11, 9)
        days = [
            {"date": str(start + timedelta(days=i)), "count": i % 7, "level": (i % 4) + 1}
            for i in range(365)
        ]
        svg = art.calendar_svg({
            "status": "verified", "source": "QA fixture",
            "granularity": "daily-count", "total_reported": sum(x["count"] for x in days),
            "days": days,
        })
        ET.fromstring(svg)
        self.assertIn("365 days in perspective", svg)
        self.assertGreater(svg.count("<polygon"), 800)

    def test_untrusted_text_is_escaped(self):
        snippet = art.text(1, 2, "<script>&unsafe")
        self.assertIn("&lt;script&gt;&amp;unsafe", snippet)


if __name__ == "__main__":
    unittest.main()
