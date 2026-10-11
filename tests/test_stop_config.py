import io
import json
from contextlib import redirect_stdout
from pathlib import Path
import tempfile
import unittest
from unittest.mock import Mock, patch

from bmad_runtime import maintenance


class StopConfigTests(unittest.TestCase):
    """B2: stop_agents uses the watcher's --config both to resolve the project and to build the runtime."""

    def setUp(self):
        self.temp = tempfile.TemporaryDirectory()
        base = Path(self.temp.name)
        self.engine, self.workspace = base / 'engine', base / 'ws'
        self.engine.mkdir()
        self.workspace.mkdir()
        (self.workspace / 'project.json').write_text(json.dumps({'schema_version': 1, 'project_id': 'demo'}),
                                                     encoding='utf-8')
        self.config = base / 'alt.json'
        self.config.write_text(json.dumps({'projects': {'demo': 'ws'}}), encoding='utf-8')

    def tearDown(self):
        self.temp.cleanup()

    def stop(self, *argv):
        runtime = Mock()
        with patch.object(maintenance, 'Runtime', return_value=runtime) as built, \
                patch.object(maintenance, 'maintenance_blocks', return_value={}), \
                patch.object(maintenance, 'close_owned_tabs', return_value=0) as close, \
                patch.dict('os.environ', {'BMAD_WORKSPACE': '', 'BMAD_PROJECT': ''}), \
                redirect_stdout(io.StringIO()) as output:
            code = maintenance.stop_main(self.engine, ['--confirm', *argv])
        return code, built, close, output.getvalue()

    def test_selected_config_resolves_the_registered_project(self):
        code, built, close, _ = self.stop('--project', 'demo', '--config', str(self.config))
        self.assertEqual(code, 0)
        _, kwargs = built.call_args
        self.assertEqual(kwargs['config_path'], self.config)
        self.assertEqual((kwargs['context'].project_id, kwargs['context'].workspace_root),
                         ('demo', self.workspace.resolve()))
        close.assert_called_once()

    def test_default_config_does_not_know_the_project(self):
        code, built, close, output = self.stop('--project', 'demo')
        self.assertEqual(code, 1)
        self.assertIn("Project 'demo' has no configured workspace", output)
        built.assert_not_called()
        close.assert_not_called()

    def test_project_must_match_the_selected_workspace(self):
        code, built, close, output = self.stop('--workspace', str(self.workspace), '--project', 'otro',
                                               '--config', str(self.config))
        self.assertEqual(code, 1)
        self.assertIn('differs from project.json', output)
        built.assert_not_called()
        close.assert_not_called()

    def test_without_confirm_nothing_is_resolved(self):
        with patch.object(maintenance, 'resolve_context') as resolve, redirect_stdout(io.StringIO()):
            self.assertEqual(maintenance.stop_main(self.engine, ['--config', str(self.config)]), 0)
        resolve.assert_not_called()


if __name__ == '__main__':
    unittest.main()
