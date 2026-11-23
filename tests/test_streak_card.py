import sys
import unittest
from datetime import date, timedelta
from pathlib import Path
from xml.etree import ElementTree as ET

sys.path.insert(0, str(Path(__file__).resolve().parents[1] / "scripts"))
import streak_card as sc


class StreakCardTests(unittest.TestCase):
    def calendar(self, values, snapshot="2026-11-23"):
        start = date.fromisoformat(snapshot) - timedelta(days=len(values) - 1)
        return {
            "status": "verified", "granularity": "daily-count",
            "generated_at_utc": snapshot + "T13:00:00+00:00",
            "source": "GitHub GraphQL contribution calendar",
            "days": [{"date": str(start + timedelta(days=i)), "count": value,
                      "level": min(value, 4)} for i, value in enumerate(values)],
        }

    def test_streak_ending_today_and_yesterday(self):
        records = [0] * 360 + [1, 2, 3, 0, 0]
        stats = sc.summary(self.calendar(records))
        self.assertEqual(stats["current"], 0)
        self.assertEqual(stats["longest"], 3)
        self.assertEqual(stats["active"], 3)
        records[-2], records[-1] = 2, 0
        stats = sc.summary(self.calendar(records))
        self.assertEqual(stats["current"], 4)
        records[-1] = 3
        self.assertEqual(sc.summary(self.calendar(records))["current"], 5)

    def test_gaps_reset_longest_streak(self):
        dates = self.calendar([0] * 360 + [1, 2, 0, 4, 5])
        del dates["days"][362]
        stats = sc.summary(dates)
        self.assertEqual(stats["longest"], 2)
        self.assertEqual(stats["current"], 2)

    def test_unavailable_data_does_not_fabricate(self):
        output = sc.render({"status": "unavailable", "days": []})
        ET.fromstring(output)
        self.assertIn("DATA UNAVAILABLE", output)
        self.assertNotIn("class=\"day\"", output)

    def test_verified_svg_is_accessible_and_valid(self):
        output = sc.render(self.calendar([i % 3 for i in range(365)]))
        root = ET.fromstring(output)
        self.assertEqual(root.tag, "{http://www.w3.org/2000/svg}svg")
        self.assertIn("CURRENT STREAK", output)
        self.assertIn("LONGEST STREAK", output)
        self.assertIn("ACTIVE DAYS", output)
        self.assertEqual(output.count('class="day"'), 56)


if __name__ == "__main__":
    unittest.main()
