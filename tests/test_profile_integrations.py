import unittest
from scripts.update_profile_readme import render
from scripts.research_challenge import tally, svg

class ProfileIntegrationTests(unittest.TestCase):
    def test_readme_section_updates(self):
        text = "x\n<!-- featured:start -->\nold\n<!-- featured:end -->\n<!-- activity:start -->\nold\n<!-- activity:end -->"
        snapshot = {"featured":[{"name":"Demo","url":"https://github.com/Armanasq/Demo","stars":4,"area":"Research"}],"events":[]}
        result = render(text, snapshot)
        self.assertIn("| [Demo](https://github.com/Armanasq/Demo) | Research | 4 |", result)
        self.assertEqual(render(result,snapshot),result)

    def test_challenge_deduplicates_voters(self):
        issues = [{"title":"Research challenge: A","user":{"login":"user1"}},{"title":"Research challenge: B","user":{"login":"user1"}},{"title":"Research challenge: C","user":{"login":"user2"}},{"title":"Research challenge: A","pull_request":{},"user":{"login":"user3"}}]
        self.assertEqual(tally(issues),{"A":1,"B":0,"C":1})
        self.assertIn("<svg",svg({"A":1,"B":0,"C":1}))

if __name__ == "__main__":
    unittest.main()
