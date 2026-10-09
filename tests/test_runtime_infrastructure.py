import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import patch

from bmad_runtime.commands import Command, CommandRunner, Result
from bmad_runtime.config import RuntimeConfig
from bmad_runtime.errors import ConfigurationError, UnsupportedCapability
from bmad_runtime.providers import default_registry
from bmad_runtime.registry import ProviderFactory


class InfrastructureTests(unittest.TestCase):
    def config(self, root, ai):
        (root / 'config_bmad.json').write_text(json.dumps({'ai': ai}), encoding='utf-8')
        return RuntimeConfig.load(root)

    def test_precedence_and_no_cross_provider_flags(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            config = self.config(root, {'defaults': {'provider': 'claude', 'model': 'chosen', 'options': {'effort': 'low'}},
                                       'phases': {'M': {'provider': 'codex'}},
                                       'agents': {'business-analyst': {'provider': 'gemini'}},
                                       'speckit': {'implement': {'provider': 'codex'}}})
            self.assertEqual(config.resolve(agent='business-analyst').provider, 'gemini')
            self.assertEqual(config.resolve(agent='product-manager').model, None)
            self.assertEqual(config.resolve(operation='implement').options, {})

    def test_unknown_provider_and_options_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            root = Path(directory)
            for ai in [{'defaults': {'provider': 'missing'}}, {'defaults': {'options': {'shell': True}}}]:
                config = self.config(root, ai)
                with self.assertRaises(ConfigurationError):
                    ProviderFactory(config, default_registry()).resolve(agent='business-analyst')

    def test_gemini_fails_explicitly(self):
        provider = default_registry().create('gemini', 'gemini')
        with self.assertRaises(UnsupportedCapability):
            provider.verify(None, Path('.'), headless=True)

    def test_native_flags_and_quoted_paths(self):
        with tempfile.TemporaryDirectory(prefix='BMAD espacio ñ ') as directory:
            root = Path(directory)
            profile = root / 'AGENTS.md'
            profile.write_text('perfil', encoding='utf-8')
            config = self.config(root, {'speckit': {'implement': {'provider': 'codex'}}})
            selection, provider = ProviderFactory(config, default_registry()).resolve(operation='implement')
            cmd = provider.headless(selection, root, 'texto " & | $(nada)', profile, {})
            self.assertEqual(cmd.argv[1], 'exec')
            self.assertNotIn('--effort', cmd.argv)
            self.assertIn('texto " & | $(nada)', cmd.stdin)

    def test_process_utf8_literal_stdin_and_exit(self):
        runner = CommandRunner(timeout=5)
        value = 'á " & | $() 漢字'
        cmd = Command((sys.executable, '-c', 'import sys; sys.stdout.buffer.write(sys.stdin.buffer.read())'), Path.cwd(), stdin=value)
        result = runner.run(cmd)
        self.assertEqual((result.returncode, result.stdout), (0, value))

    def test_timeout_and_output_limit(self):
        runner = CommandRunner(timeout=0.1, max_output_bytes=100)
        result = runner.run(Command((sys.executable, '-c', 'import time; time.sleep(5)'), Path.cwd()))
        self.assertEqual(result.error, 'timeout')
        result = runner.run(Command((sys.executable, '-c', 'print("x" * 1000)'), Path.cwd()), timeout=5)
        self.assertEqual(result.error, 'output_limit')
        self.assertLessEqual(len(result.stdout), 100)

    def test_missing_cli_and_env_restriction(self):
        runner = CommandRunner()
        self.assertEqual(runner.run(Command(('definitely-not-an-installed-cli',), Path.cwd())).returncode, 127)
        with self.assertRaises(ConfigurationError):
            runner.run(Command((sys.executable,), Path.cwd(), env={'PATH': 'untrusted'}))

    def test_quota_is_not_success(self):
        provider = default_registry().create('claude', 'claude')
        self.assertEqual(provider.classify(Result(0, 'usage limit reached')), 'quota')

    def test_sanitized_command(self):
        self.assertEqual(Command(('cli', '--prompt', 'secret'), Path('.'), sensitive=frozenset({2})).sanitized(), ['cli', '--prompt', '<redacted>'])


if __name__ == '__main__':
    unittest.main()
