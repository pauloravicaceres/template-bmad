"""Opt-in local CLI help checks: no prompts, authentication or agent launches."""
import os
from pathlib import Path
import unittest

from bmad_runtime.commands import Command, CommandRunner
from bmad_runtime.config import Selection
from bmad_runtime.herdr import HerdrGateway
from bmad_runtime.providers import ClaudeProvider, CodexProvider


@unittest.skipUnless(os.environ.get('BMAD_TEST_REAL_CLI') == '1', 'opt-in local CLI help verification')
class CLIContractTests(unittest.TestCase):
    def test_codex_effort_argument_positions_with_help_only(self):
        runner = CommandRunner(timeout=15)
        root = Path(__file__).resolve().parents[1]
        provider = CodexProvider()
        for effort in ('low', 'medium', 'high', 'xhigh', 'max'):
            selection = Selection('codex', 'gpt-6-astra', {'effort': effort})
            commands = (
                provider.interactive(selection, root, root / 'solutions-architect/AGENTS.md'),
                provider.headless(selection, root, 'not sent', None, {}),
            )
            for native in commands:
                with self.subTest(effort=effort, mode=native.argv[1]):
                    # --help exits the argument parser; no model turn is started.
                    result = runner.run(Command((*native.argv, '--help'), native.cwd))
                    result.require_success()
                    self.assertIn('--config', result.stdout)

    def test_installed_help_and_herdr_kinds(self):
        runner = CommandRunner(timeout=15)
        root = Path(__file__).resolve().parents[1]
        gateway = HerdrGateway(runner, root)
        for provider in (ClaudeProvider(), CodexProvider()):
            provider.verify(runner, root, headless=False)
            provider.verify(runner, root, headless=True)
            gateway.verify_provider(provider)
        # File form is documented and accepted although hidden in the option table.
        runner.run(Command(('claude', '--append-system-prompt-file', str(root / 'business-analyst/AGENTS.md'), '--help'), root)).require_success()
