import json
import tempfile
import unittest
from pathlib import Path
from unittest.mock import patch

from scripts import profile_refresh as p


class ProfileRefreshTests(unittest.TestCase):
    def test_escaped_markup(self):
        svg = p.panel('<unsafe>', 'Text & context', [('<first>', '<second>')], 'ok')
        self.assertIn('&lt;unsafe&gt;', svg)
        self.assertNotIn('<unsafe>', svg)
        self.assertIn('&amp;', svg)

    def test_event_description_does_not_invent_commit_details(self):
        self.assertEqual(p.event_label({'type': 'PushEvent', 'payload': {}}), 'Pushed code')
        self.assertEqual(
            p.event_label({'type': 'IssuesEvent', 'payload': {'action': 'opened'}}),
            'Issue: opened',
        )

    def test_snapshot_filters_private_and_other_owners(self):
        user = {'followers': 5}
        repos = [
            {'name': 'Open', 'owner': {'login': 'Armanasq'}, 'private': False,
             'fork': False, 'language': 'Python', 'stargazers_count': 7,
             'html_url': 'https://github.com/Armanasq/Open', 'pushed_at': '2026-10-10T10:00:00Z'},
            {'name': 'Secret', 'owner': {'login': 'Armanasq'}, 'private': True,
             'fork': False, 'language': 'Python', 'stargazers_count': 999},
            {'name': 'Other', 'owner': {'login': 'Another'}, 'private': False,
             'fork': False, 'language': 'Python', 'stargazers_count': 99},
        ]
        events = [{'type': 'PushEvent', 'created_at': '2026-10-11T10:00:00Z',
                   'repo': {'name': 'Armanasq/Open'}, 'payload': {}}]
        with patch.object(p, 'fetch_json', side_effect=[user, repos, events]):
            snap = p.build_snapshot('Armanasq', [{'name': 'Open', 'area': 'Research'}])
        self.assertEqual(snap['statistics']['original_public_repositories'], 1)
        self.assertEqual(snap['statistics']['stars_on_original_public_repositories'], 7)
        self.assertNotIn('Secret', json.dumps(snap))
        self.assertEqual(len(snap['events']), 1)

    def test_written_svgs_and_digest_are_valid(self):
        snap = {
            'schema_version': 1, 'generated_at_utc': '2026-11-09T12:00:00+00:00',
            'login': 'Armanasq', 'statistics': {
                'public_repositories': 1, 'original_public_repositories': 1,
                'stars_on_original_public_repositories': 4, 'public_followers': 3,
            }, 'events': [], 'events_status': 'unavailable',
            'featured': [{'name': 'Open', 'area': 'Robotics', 'pushed_at': None, 'stars': 4}],
            'recent_public_repository_pushes': [{'name': 'Open', 'date': None}],
        }
        with tempfile.TemporaryDirectory() as temp:
            folder = Path(temp)
            p.write_profile(snap, folder / 'assets', folder / 'data' / 'snapshot.json')
            for name in ['overview', 'activity', 'research-radar', 'lineage']:
                output = (folder / 'assets' / (name + '.svg')).read_text()
                self.assertTrue(output.startswith('<svg'))
                self.assertIn('</svg>', output)
            self.assertEqual(json.loads((folder / 'data' / 'snapshot.json').read_text())['login'], 'Armanasq')


if __name__ == '__main__':
    unittest.main()
