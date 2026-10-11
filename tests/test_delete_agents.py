import io
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import patch

from utils import delete_agents


class DeleteAgentsTests(unittest.TestCase):
    """B1: AGENTS.md may hold uncommitted edits; removing them needs an explicit --confirm."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        self.root = Path(self.temp.name)
        self.profiles = []
        for name in ('business-analyst', 'product-manager'):
            (self.root / name / 'agents').mkdir(parents=True)
            profile = self.root / name / 'AGENTS.md'
            profile.write_text('perfil', encoding='utf-8')
            self.profiles.append(profile)

    def tearDown(self):
        self.temp.cleanup()

    def run_main(self, argv):
        output = io.StringIO()
        with redirect_stdout(output), patch.dict('os.environ', {}, clear=False) as env:
            env.pop('BMAD_WORKSPACE', None)
            env.pop('WORKSPACE_ROOT', None)
            code = delete_agents.main(argv, root=self.root)
        return code, output.getvalue()

    def test_without_confirm_nothing_is_deleted(self):
        code, output = self.run_main([])
        self.assertEqual(code, 0)
        self.assertTrue(all(profile.is_file() for profile in self.profiles))
        self.assertIn('No se eliminó nada. 2 AGENTS.md', output)
        self.assertIn('--confirm', output)

    def test_confirm_deletes_only_generated_profiles(self):
        code, output = self.run_main(['--confirm'])
        self.assertEqual(code, 0)
        self.assertFalse(any(profile.exists() for profile in self.profiles))
        self.assertTrue(all((profile.parent / 'agents').is_dir() for profile in self.profiles))
        self.assertIn('[OK] AGENTS.md eliminado en: business-analyst', output)

    def test_project_context_is_refused_before_anything_else(self):
        with patch.dict('os.environ', {'BMAD_WORKSPACE': str(self.root)}), self.assertRaises(SystemExit):
            delete_agents.main(['--confirm'], root=self.root)
        with self.assertRaises(SystemExit):
            delete_agents.main(['--project', 'demo', '--confirm'], root=self.root)
        self.assertTrue(all(profile.is_file() for profile in self.profiles))


if __name__ == '__main__':
    unittest.main()
