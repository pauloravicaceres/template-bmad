"""Reasoning effort contracts; no real agents or project configuration writes."""
import io
import json
from pathlib import Path
import sys
import tempfile
import unittest
from unittest.mock import Mock, patch

from bmad_runtime.commands import Command, CommandRunner, Result
from bmad_runtime.config import RuntimeConfig, Selection
from bmad_runtime.errors import ConfigurationError, UnsupportedCapability
from bmad_runtime.herdr import HerdrGateway
from bmad_runtime.providers import ClaudeProvider, CodexProvider, default_registry
from bmad_runtime.registry import ProviderFactory
from bmad_runtime.services import SpecKitExecutor


class CodexEffortTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='BMAD effort espacio ')
        self.addCleanup(self.temp.cleanup)
        self.root = Path(self.temp.name)
        self.profile = self.root / 'role' / 'AGENTS.md'
        self.profile.parent.mkdir()
        self.profile.write_text('Complete role instructions.', encoding='utf-8')
        self.provider = CodexProvider()

    def selection(self, effort):
        return Selection('codex', 'gpt-6-astra', {'effort': effort})

    def config(self, ai):
        (self.root / 'config_bmad.json').write_text(json.dumps({'ai': ai}), encoding='utf-8')
        return RuntimeConfig.load(self.root)

    def assert_effort(self, command, effort):
        index = command.argv.index('-c')
        self.assertEqual(command.argv[index + 1], f'model_reasoning_effort={effort}')
        self.assertEqual(command.argv.count('-c'), 1)
        for flag in ('--effort', '--permission-mode', '--permission-prompts',
                     '--append-system-prompt-file', '--max-budget-usd', '-p'):
            self.assertNotIn(flag, command.argv)

    def test_all_requested_levels_interactive_and_headless(self):
        for effort in ('low', 'medium', 'high', 'xhigh', 'max'):
            with self.subTest(effort=effort):
                selection = self.selection(effort)
                self.provider.validate(selection)
                interactive = self.provider.interactive(selection, self.root, self.profile)
                headless = self.provider.headless(selection, self.root, '$speckit-implement', self.profile, {})
                for command in (interactive, headless):
                    self.assert_effort(command, effort)
                    self.assertEqual(command.argv[command.argv.index('--model') + 1], 'gpt-6-astra')
                    self.assertEqual(command.argv[command.argv.index('--sandbox') + 1], 'workspace-write')
                self.assertEqual(interactive.cwd, self.profile.parent)
                self.assertEqual(interactive.argv[interactive.argv.index('--cd') + 1], str(self.profile.parent))
                self.assertEqual(interactive.argv[interactive.argv.index('--add-dir') + 1], str(self.root))
                self.assertEqual(interactive.argv[interactive.argv.index('--ask-for-approval') + 1], 'on-request')
                self.assertIn(self.profile.as_posix(), interactive.argv[-1])
                self.assertEqual(interactive.sanitized()[-1], '<redacted>')
                self.assertEqual(headless.argv[:2], ('codex', 'exec'))
                self.assertEqual(headless.argv[-2:], ('--ephemeral', '-'))
                self.assertEqual(headless.cwd, self.root)
                self.assertIn(self.profile.as_posix(), headless.stdin)

    def test_no_effort_preserves_cli_default(self):
        selection = Selection('codex')
        for command in (self.provider.interactive(selection, self.root, self.profile),
                        self.provider.headless(selection, self.root, 'prompt', None, {})):
            self.assertNotIn('-c', command.argv)
            self.assertNotIn('--model', command.argv)
            self.assertFalse(any('model_reasoning_effort' in arg for arg in command.argv))

    def test_invalid_efforts_rejected_before_command_construction(self):
        for effort in ('', 'HIGH', 'ultra', 'none', 'minimal', 'high --sandbox danger-full-access',
                       'low\nmodel=other', 'high; whoami', None, True, 1, [], {}):
            with self.subTest(effort=effort):
                selection = self.selection(effort)
                for operation in (lambda: self.provider.validate(selection),
                                  lambda: self.provider.interactive(selection, self.root, self.profile),
                                  lambda: self.provider.headless(selection, self.root, 'prompt', None, {})):
                    with self.assertRaises(ConfigurationError):
                        operation()

    def test_max_requires_verified_explicit_model(self):
        for model in (None, 'unknown-model', 'gpt-6-astra-unverified-snapshot'):
            with self.subTest(model=model), self.assertRaises(ConfigurationError):
                self.provider.validate(Selection('codex', model, {'effort': 'max'}))

    def test_arbitrary_options_and_unsafe_sandbox_remain_rejected(self):
        for options in ({'profile': 'custom'}, {'config': 'untrusted=1'},
                        {'permission_mode': 'manual'}, {'sandbox': 'danger-full-access'}):
            with self.subTest(options=options), self.assertRaises(ConfigurationError):
                self.provider.validate(Selection('codex', options=options))
        selection = Selection('codex', options={'sandbox': 'read-only', 'effort': 'low'})
        command = self.provider.headless(selection, self.root, 'prompt', None, {})
        self.assertEqual(command.argv[command.argv.index('--sandbox') + 1], 'read-only')

    def test_herdr_forwards_the_exact_native_argument_vector(self):
        native = self.provider.interactive(self.selection('medium'), self.root, self.profile)
        gateway = HerdrGateway(Mock(), self.root)
        wrapped = gateway.start_command('solutions-architect', 'pane-id', self.provider, native)
        split = wrapped.argv.index('--')
        self.assertEqual(wrapped.argv[:split], ('herdr', 'agent', 'start', 'solutions-architect',
                                              '--kind', 'codex', '--pane', 'pane-id', '--timeout', '30000'))
        self.assertEqual(wrapped.argv[split + 1:], native.argv[1:])
        self.assertEqual(wrapped.cwd, native.cwd)
        self.assertEqual(wrapped.sanitized()[-1], '<redacted>')
        self.assert_effort(wrapped, 'medium')

    def test_speckit_prepare_preserves_effort_stdin_directive_and_env(self):
        for folder in ('.github', '.agents'):
            skill = self.root / folder / 'skills' / 'speckit-implement'
            skill.mkdir(parents=True)
            (skill / 'SKILL.md').write_text('---\nname: speckit-implement\n---\nImplement.', encoding='utf-8')
        config = self.config({'defaults': {'provider': 'codex', 'model': 'gpt-6-astra'},
                              'phases': {'D': {'options': {'effort': 'low'}}},
                              'speckit': {'implement': {'options': {'effort': 'high'}}}})
        executor = SpecKitExecutor(config, ProviderFactory(config, default_registry()), Mock(), None)
        env = {'SPECIFY_FEATURE_DIRECTORY': 'specs/feature'}
        _, _, command = executor.prepare('implement', 'literal & | input', self.profile, env)
        self.assert_effort(command, 'high')
        self.assertTrue(command.stdin.startswith('$speckit-implement literal & | input'))
        self.assertIn(self.profile.as_posix(), command.stdin)
        self.assertEqual(command.env, env)
        self.assertEqual(command.argv[-1], '-')

    def test_claude_keeps_native_effort_syntax(self):
        provider = ClaudeProvider()
        selection = Selection('claude', options={'effort': 'medium'})
        for command in (provider.interactive(selection, self.root, self.profile),
                        provider.headless(selection, self.root, 'prompt', self.profile, {})):
            self.assertEqual(command.argv[command.argv.index('--effort') + 1], 'medium')
            self.assertNotIn('-c', command.argv)
            self.assertNotIn('--sandbox', command.argv)
            self.assertIn('--append-system-prompt-file', command.argv)

    def test_config_precedence_and_options_replacement(self):
        config = self.config({'defaults': {'provider': 'codex', 'model': 'gpt-6-astra',
                                           'options': {'effort': 'low', 'sandbox': 'read-only'}},
                              'phases': {'A': {'options': {'effort': 'medium'}}},
                              'agents': {'solutions-architect': {'options': {'effort': 'high'}}},
                              'speckit': {'plan': {'options': {'effort': 'xhigh'}}}})
        factory = ProviderFactory(config, default_registry())
        for target, effort in (({'agent': 'product-manager'}, 'low'),
                               ({'agent': 'data-architect'}, 'medium'),
                               ({'agent': 'solutions-architect'}, 'high'),
                               ({'operation': 'tasks'}, 'medium'),
                               ({'operation': 'plan'}, 'xhigh')):
            with self.subTest(target=target):
                selection, _ = factory.resolve(**target)
                self.assertEqual(selection.options['effort'], effort)
                if effort != 'low':
                    self.assertNotIn('sandbox', selection.options)

    def test_provider_switch_discards_incompatible_model_and_options(self):
        config = self.config({'defaults': {'provider': 'claude', 'model': 'claude-model',
                                           'options': {'effort': 'high', 'permission_mode': 'plan'}},
                              'phases': {'A': {'provider': 'codex'}},
                              'agents': {'business-analyst': {'provider': 'codex', 'options': {'effort': 'low'}}},
                              'speckit': {'implement': {'provider': 'codex'}}})
        factory = ProviderFactory(config, default_registry())
        for target in ({'agent': 'data-architect'}, {'operation': 'implement'}):
            selection, _ = factory.resolve(**target)
            self.assertEqual(selection, Selection('codex'))
        selection, _ = factory.resolve(agent='business-analyst')
        self.assertEqual(selection, Selection('codex', options={'effort': 'low'}))

    def test_verify_requires_config_flag_in_both_modes(self):
        for headless in (False, True):
            runner = Mock()
            help_text = '--model --sandbox --cd --add-dir --ephemeral --ask-for-approval'
            runner.run.return_value = Result(0, help_text)
            with self.assertRaises(UnsupportedCapability):
                self.provider.verify(runner, self.root, headless=headless)
            runner.run.return_value = Result(0, help_text + ' --config')
            self.provider.verify(runner, self.root, headless=headless)

    def test_runner_uses_argument_list_without_shell(self):
        process = Mock()
        process.stdout, process.stderr = io.BytesIO(), io.BytesIO()
        process.poll.return_value = process.returncode = 0
        command = Command((sys.executable, '-c', 'model_reasoning_effort=medium'), self.root)
        with patch('bmad_runtime.commands.subprocess.Popen', return_value=process) as popen:
            CommandRunner().run(command).require_success()
        self.assertIs(popen.call_args.kwargs['shell'], False)
        self.assertIsInstance(popen.call_args.args[0], list)
        self.assertEqual(popen.call_args.args[0][1:], list(command.argv[1:]))
