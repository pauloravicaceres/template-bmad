"""Fase 4F-E5.2.1: fail-closed pane classification before any automatic write.

Screens are synthetic reproductions (the Codex 0.162 trust menu of the E5.2 pilot, Claude dialogs, composers);
Herdr, Claude and Codex are doubles. Nothing real is launched and no dialog is ever answered.
"""
import os
from pathlib import Path
import re
import tempfile
import threading
import time
import unittest
from unittest.mock import patch

import pytest

from bmad_runtime import maintenance, pane_state, state as state_module
from bmad_runtime.errors import AgentBlocked, CommandError, DeliveryUncertain, ReconciliationRequired
from bmad_runtime.pane_state import (AWAITING_PERMISSION, AWAITING_SELECTION, AWAITING_TRUST, BUSY, EXITED,
                                     READY_VERIFIED, UNKNOWN, PaneGate, PaneNotReady, classify)
from bmad_runtime.providers import ClaudeProvider, CodexProvider
from bmad_runtime.watcher_service import maintenance_blocks
from tests.pane_doubles import CLAUDE_READY, CODEX_READY, foreground
from tests.test_agent_startup import TRUST_SCREEN, StartupCase
from tests.test_session_maintenance import BA, SA

ENGINE = Path(__file__).resolve().parents[1] / 'bmad_runtime'

# The Codex 0.162.0 dialog of the E5.2 pilot, as `pane read --source visible --raw` returns it (colours kept).
CODEX_TRUST = ('\x1b[1m> You are in C:\\Users\\User\\scratchpad\\bmad-e5-pilot\x1b[0m\n\n'
               '  Folder access\n\n'
               '  Trust this folder?\n\n'
               '\x1b[36m› 1. Trust and continue\x1b[0m\n'
               '  2. Quit\n\n'
               '  \x1b[2menter continue · esc quit\x1b[0m\n')
CODEX_TRUST_VARIANTS = {
    'older_wording': ('> You are in C:\\ws\n\n  Do you trust the contents of this directory? Working with untrusted '
                      'contents comes with higher risk of prompt injection.\n\n› 1. Yes, continue\n  2. No, quit\n\n'
                      '  Press enter to continue\n'),
    'upper_case_with_frame': ('╭────────────────────────╮\n│  \x1b[1mTRUST THIS FOLDER?\x1b[0m  │\n'
                              '╰────────────────────────╯\n'),
    'partial_render_header_only': '\x1b[2J\x1b[H  Folder access\n',
    'allow_wording': '  Allow Codex to work in this folder?\n› 1. Allow\n  2. Quit\n',
    'carriage_returns_and_osc': '\x1b]0;codex\x07  Trust this\r\n  folder?\r\n\x1b[7m› 1. Trust and continue\x1b[0m\r\n',
}
# Claude Code: Phase 4B capture (unnumbered options) and the 2.1.296 numbered form.
CLAUDE_TRUST_4B = (' Accessing workspace:\n\n C:\\ws\\bmad-4b-ws\n\n Quick safety check: Is this a project you created '
                   'or one you trust?\n\n Claude Code\'ll be able to read, edit, and execute files here.\n\n'
                   ' Security guide\n\n ❯ No, exit\n   Yes, I trust this folder\n\n Enter to confirm · Esc to cancel\n')
CLAUDE_PERMISSION = (' Bash command\n\n   npm test\n   Run tests\n\n Do you want to proceed?\n ❯ 1. Yes\n'
                     "   2. Yes, and don't ask again for npm test commands in C:\\ws\n"
                     '   3. No, and tell Claude what to do differently (esc)\n')
CODEX_APPROVAL = ('  Would you like to run the following command?\n\n  $ git status --short\n\n'
                  '› 1. Yes, proceed (y)\n  2. No, and tell Codex what to do differently (esc)\n')
CLAUDE_BYPASS_WARNING = (' WARNING: Claude Code running in Bypass Permissions mode\n\n In Bypass Permissions mode, Claude '
                         'Code will not ask for your approval before running potentially dangerous commands.\n\n'
                         ' ❯ 1. No, exit\n   2. Yes, I accept\n\n Enter to confirm · Esc to exit\n')
NUMERIC_MENU = ' Select model\n\n   1. Default (recommended)\n   2. Opus\n   3. Haiku\n'
CODEX_OPTIONS_ONLY = '› 1. Continue\n  2. Quit\n'
CLAUDE_STARTING = ' ✻ Welcome to Claude Code!\n\n   /help for help, /status for your current setup\n\n   cwd: C:\\ws\n'
CLAUDE_BUSY = ('● Leyendo el contrato…\n\n✻ Cogitating… (5s · ↑ 1.2k tokens · esc to interrupt)\n\n'
               '────────────────\n❯ \n────────────────\n  ⏵⏵ accept edits on (shift+tab to cycle)\n')
CODEX_BUSY = '• Working (12s • esc to interrupt)\n\n› Ask Codex to do anything\n\n  100% context left · ? for shortcuts\n'
CLAUDE_OLD_BOX = '╭──────────────────────────╮\n│ > Try "fix lint errors" │\n╰──────────────────────────╯\n  ? for shortcuts\n'
CLAUDE_TRANSCRIPT_LIST = ('● Plan:\n  1. Leer el contrato\n  2. Esperar el handoff\n\n────────\n❯ \n────────\n'
                          '  ⏵⏵ accept edits on (shift+tab to cycle)\n')
CODEX_ANSI_READY = ('\x1b[1m• Contrato leído.\x1b[0m\n\n\x1b[36m›\x1b[0m \x1b[2mAsk Codex to do anything\x1b[0m\n\n'
                    '  \x1b[2m100% context left · ? for shortcuts\x1b[0m\n')
SHELL_SCREEN = 'Codex exited.\nPS C:\\Users\\User\\ws> '
AT_SHELL = {'shell_pid': 1, 'foreground_processes': [{'pid': 1, 'name': 'pwsh.exe'}]}

DIALOGS = {'codex_trust_0.162': (CODEX_TRUST, AWAITING_TRUST), 'claude_trust_4b': (CLAUDE_TRUST_4B, AWAITING_TRUST),
           'claude_trust_numbered': (TRUST_SCREEN, AWAITING_TRUST),
           'claude_permission': (CLAUDE_PERMISSION, AWAITING_PERMISSION),
           'codex_approval': (CODEX_APPROVAL, AWAITING_PERMISSION),
           'claude_bypass_warning': (CLAUDE_BYPASS_WARNING, AWAITING_SELECTION),
           'numeric_menu': (NUMERIC_MENU, AWAITING_SELECTION), 'options_only': (CODEX_OPTIONS_ONLY, AWAITING_SELECTION),
           **{'codex_' + name: (screen, AWAITING_TRUST) for name, screen in CODEX_TRUST_VARIANTS.items()}}


# 1. Classifier -----------------------------------------------------------------------------------------------------
@pytest.mark.parametrize('profile', ['claude', 'codex'])
@pytest.mark.parametrize('name', sorted(DIALOGS))
def test_every_dialog_needs_a_human_whatever_the_provider(profile, name):
    screen, expected = DIALOGS[name]
    observation = classify(profile, screen, herdr_status='idle')
    assert (observation.state, observation.ready) == (expected, False)
    assert observation.blocker


def test_pilot_codex_dialog_was_reported_available_and_now_is_trust():
    # Before E5.2.1 CodexProvider.interaction_blocker returned None here and VERIFY typed its probe into the menu.
    assert CodexProvider().interaction_blocker(CODEX_TRUST) == 'trust_dialog'
    assert classify('codex', CODEX_TRUST, herdr_status='idle').evidence[0] == 'folder access'


@pytest.mark.parametrize('profile,screen', [('claude', CLAUDE_READY), ('codex', CODEX_READY),
                                            ('claude', CLAUDE_OLD_BOX), ('claude', CLAUDE_TRANSCRIPT_LIST),
                                            ('codex', CODEX_ANSI_READY)])
def test_idle_composer_is_ready(profile, screen):
    observation = classify(profile, screen, herdr_status='idle')
    assert observation.state == READY_VERIFIED, observation


@pytest.mark.parametrize('profile,screen,state,reason', [
    ('claude', '', UNKNOWN, 'empty_screen'),
    ('claude', '\x1b[2J\x1b[H\x1b[?25l', UNKNOWN, 'empty_screen'),
    ('claude', None, UNKNOWN, 'screen_unavailable'),
    ('claude', '❯ \n', UNKNOWN, 'footer_missing'),
    ('codex', '› Ask Codex to do anything', UNKNOWN, 'footer_missing'),
    ('claude', '  ⏵⏵ accept edits on\n', UNKNOWN, 'composer_missing'),
    ('claude', CLAUDE_STARTING, UNKNOWN, 'no_ready_prompt'),
    ('claude', 'Lorem ipsum\nsin interfaz conocida\n', UNKNOWN, 'no_ready_prompt'),
    ('codex', CLAUDE_READY, UNKNOWN, 'no_ready_prompt'),        # another CLI's composer is not this one
    (None, CLAUDE_READY, UNKNOWN, 'no_screen_profile'),
    ('claude', CLAUDE_BUSY, BUSY, 'turn_running'),
    ('codex', CODEX_BUSY, BUSY, 'turn_running'),
    ('claude', SHELL_SCREEN, EXITED, 'shell_prompt'),
])
def test_ambiguous_busy_or_exited_screens_are_never_ready(profile, screen, state, reason):
    observation = classify(profile, screen, herdr_status='idle')
    assert (observation.state, observation.reason) == (state, reason)


def test_herdr_status_is_evidence_but_never_proof_of_readiness():
    assert classify('claude', CLAUDE_READY, herdr_status='working').state == BUSY
    assert classify('claude', CLAUDE_READY, herdr_status='blocked').state == AWAITING_PERMISSION
    assert classify('claude', CLAUDE_READY, herdr_status='unknown').state == UNKNOWN
    # 'idle' over a dialog is exactly the Herdr 0.8.2 behaviour seen in the pilot.
    assert classify('codex', CODEX_TRUST, herdr_status='idle').state == AWAITING_TRUST


def test_old_transcript_text_does_not_hide_a_dialog_and_dialog_words_in_old_output_are_ignored():
    # A dialog under a ready-looking history is still a dialog.
    assert classify('claude', CLAUDE_READY + CLAUDE_PERMISSION).state == AWAITING_PERMISSION
    # Permission words far above the composer are transcript, not a dialog.
    history = 'Do you want to proceed?\n' + ''.join(f'línea {n}\n' for n in range(12)) + CLAUDE_READY
    assert classify('claude', history).state == READY_VERIFIED


def test_provider_detectors_keep_their_phase_4b_names():
    claude, codex = ClaudeProvider(), CodexProvider()
    assert claude.interaction_blocker(CLAUDE_TRUST_4B) == 'trust_dialog'
    assert claude.interaction_blocker(CLAUDE_PERMISSION) == 'permission_dialog'
    assert codex.interaction_blocker(NUMERIC_MENU) == 'selection_menu'
    # None only says "no known dialog"; it never means ready.
    assert claude.interaction_blocker(CLAUDE_STARTING) is None
    assert classify(claude.screen_profile, CLAUDE_STARTING).ready is False


# 2. Gate: process, stability and exclusion -------------------------------------------------------------------------
class Pane:
    """Gateway double: a sequence of visible screens (the last one repeats) and one process table."""

    def __init__(self, screens, process=None):
        self.screens, self.process = list(screens), process or foreground('claude')

    def read(self, pane, lines=40, source='recent'):
        return self.screens.pop(0) if len(self.screens) > 1 else self.screens[0]

    def process_info(self, pane):
        if isinstance(self.process, Exception):
            raise self.process
        return self.process


def gate(tmp_path, screens, process=None):
    return PaneGate(Pane(screens, process), tmp_path, sleep=lambda _s: None)


def test_gate_requires_the_expected_cli_in_the_foreground(tmp_path):
    claude = ClaudeProvider()
    assert gate(tmp_path, [CLAUDE_READY]).observe(claude, 'p').state == READY_VERIFIED
    assert gate(tmp_path, [CLAUDE_READY], AT_SHELL).observe(claude, 'p').state == EXITED
    starting = gate(tmp_path, [CLAUDE_READY], {'shell_pid': 1, 'foreground_processes': []}).observe(claude, 'p')
    assert (starting.state, starting.reason) == (UNKNOWN, 'process_unknown')
    assert gate(tmp_path, [CLAUDE_READY], foreground('node')).observe(claude, 'p').reason == 'process_foreign'
    assert gate(tmp_path, [CLAUDE_READY], CommandError('x')).observe(claude, 'p').state == UNKNOWN


def test_gate_detects_a_screen_that_changes_between_reads(tmp_path):
    claude = ClaudeProvider()
    assert gate(tmp_path, [CLAUDE_READY, TRUST_SCREEN]).observe(claude, 'p').state == AWAITING_TRUST
    changed = gate(tmp_path, [CLAUDE_READY, '● Otra salida\n' + CLAUDE_READY]).observe(claude, 'p')
    assert (changed.state, changed.reason) == (UNKNOWN, 'screen_changing')


def test_dialog_is_reported_even_while_the_process_is_unverifiable(tmp_path):
    observation = gate(tmp_path, [CODEX_TRUST], {'shell_pid': 1, 'foreground_processes': []}).observe(CodexProvider(), 'p')
    assert observation.state == AWAITING_TRUST


def test_two_writers_on_one_pane_are_serialized(tmp_path):
    first, second = PaneGate(Pane([CLAUDE_READY]), tmp_path), PaneGate(Pane([CLAUDE_READY]), tmp_path)
    second.lock_wait_s = 0
    with first.exclusive('w1:p3'):
        with pytest.raises(PaneNotReady) as raised:
            with second.exclusive('w1:p3'):
                pass
        assert raised.value.observation.reason == 'pane_locked'
        with second.exclusive('w1:p4'):      # another pane is independent
            pass
    events, waiting = [], PaneGate(Pane([CLAUDE_READY]), tmp_path)
    waiting.lock_wait_s = 5

    def writer(label, pause):
        with (waiting if label == 'b' else first).exclusive('w1:p3'):
            events.append(label + '+')
            time.sleep(pause)
            events.append(label + '-')
    a = threading.Thread(target=writer, args=('a', 0.3))
    a.start()
    while not events:
        time.sleep(0.01)
    b = threading.Thread(target=writer, args=('b', 0))
    b.start()
    a.join()
    b.join()
    assert events == ['a+', 'a-', 'b+', 'b-']


# 3. Dispatch, VERIFY and reconcile on doubles ---------------------------------------------------------------------
class PaneCase(StartupCase):
    def written(self, pane=None):
        return [call for call in self.calls(pane) if call[0] in ('prompt', 'submit', 'run', 'start')]

    def agent(self, name=BA):
        return self.rt.state.get('agent:' + name)


class DispatchGateTests(PaneCase):
    provider = 'fake-codex'

    def test_dispatch_types_nothing_into_any_dialog(self):
        for name, (screen, expected) in sorted(DIALOGS.items()):
            with self.subTest(name):
                self.rt.state.put('agent:' + BA, {**self.agent(), 'state': 'ready'})
                self.gateway.screen['p-' + BA] = screen
                with self.assertRaises(AgentBlocked):
                    self.rt.dispatcher.dispatch(BA, 'p-' + BA, '@BA: tarea 12', 'ev-' + name)
                self.assertEqual(self.written(), [])
                self.assertIsNone(self.rt.state.get('dispatch:ev-' + name))
                self.assertEqual((self.agent()['state'], self.agent()['screen_check']['state']),
                                 ('awaiting_trust', expected))

    def test_unknown_or_busy_screen_defers_then_holds_after_the_limit(self):
        self.rt.dispatcher.unready_limit = 3
        self.gateway.screen['p-' + BA] = CODEX_BUSY
        for _ in range(2):
            with self.assertRaises(PaneNotReady):
                self.rt.dispatcher.dispatch(BA, 'p-' + BA, '@BA: tarea', 'ev-busy')
        self.assertEqual((self.agent()['state'], self.agent()['screen_unready']), ('ready', 2))
        self.gateway.screen['p-' + BA] = CLAUDE_STARTING
        with self.assertRaises(AgentBlocked):
            self.rt.dispatcher.dispatch(BA, 'p-' + BA, '@BA: tarea', 'ev-busy')
        self.assertEqual((self.agent()['state'], self.agent()['blocker']), ('unverified', 'unknown'))
        self.assertEqual((self.written(), self.rt.state.get('dispatch:ev-busy')), ([], None))

    def test_exited_cli_is_never_reused_as_a_live_agent(self):
        self.gateway.process_info = lambda pane: AT_SHELL
        with self.assertRaises(AgentBlocked):
            self.rt.dispatcher.dispatch(BA, 'p-' + BA, '@BA: tarea', 'ev-exit')
        self.assertEqual((self.written(), self.agent()['state']), ([], 'unverified'))

    def test_screen_change_after_preparing_the_task_writes_nothing(self):
        self.rt.config.data['outbox'] = {'mode': 'outbox'}
        original, reads, event = self.gateway.read, [], 'a' * 64

        def read(pane, lines=40, source='recent'):
            if source == 'visible':
                reads.append(pane)
                if len(reads) > 1:       # the pre-check saw the composer; the final check sees a dialog
                    return CODEX_TRUST
            return original(pane, lines, source)
        self.gateway.read = read
        with self.assertRaises(AgentBlocked):
            self.rt.dispatcher.dispatch(BA, 'p-' + BA, '@BA: tarea', event)
        self.assertEqual(self.written(), [])
        dispatch = self.rt.state.get('dispatch:' + event)
        self.assertEqual(dispatch['state'], 'not_delivered')
        expected = self.rt.state.get(dispatch['outbox'])
        self.assertEqual((expected['state'], expected['reason']), ('rejected', 'dispatch_not_delivered'))

    def test_dialog_seen_right_after_the_write_is_uncertain_and_held(self):
        original = self.gateway.prompt

        def prompt(pane, text, timeout_ms=None):
            original(pane, text, timeout_ms)
            self.gateway.screen[pane] = CODEX_TRUST
        self.gateway.prompt = prompt
        with self.assertRaises(DeliveryUncertain):
            self.rt.dispatcher.dispatch(BA, 'p-' + BA, '@BA: tarea', 'ev-after')
        self.assertEqual(self.rt.state.get('dispatch:ev-after')['state'], 'uncertain')
        self.assertEqual(self.agent()['state'], 'awaiting_trust')

    def test_concurrent_runtime_writer_holds_the_pane(self):
        other = PaneGate(self.gateway, self.rt.context)
        self.rt.dispatcher.gate.lock_wait_s = 0
        with other.exclusive('p-' + BA):
            with self.assertRaises(PaneNotReady):
                self.rt.dispatcher.dispatch(BA, 'p-' + BA, '@BA: tarea', 'ev-lock')
        self.assertEqual((self.written(), self.rt.state.get('dispatch:ev-lock')['state']), ([], 'not_delivered'))
        # Released: the explicit new attempt is delivered once.
        self.assertTrue(self.rt.dispatcher.dispatch(BA, 'p-' + BA, '@BA: tarea', 'ev-lock'))
        self.assertEqual(len([c for c in self.written() if c[0] == 'prompt']), 1)

    def test_ready_sessions_of_both_providers_still_accept_tasks(self):
        for provider in ('fake-codex', 'fake-claude'):
            with self.subTest(provider):
                self.configure(provider)
                self.assertTrue(self.rt.dispatcher.dispatch(BA, 'p-' + BA, '@BA: tarea', 'ev-' + provider))
                self.assertEqual([c[0] for c in self.written()], ['prompt'])
                self.assertEqual(self.rt.state.get('dispatch:ev-' + provider)['delivery'], 'accepted')
                self.assertNotIn('screen_unready', self.agent())

    def test_watcher_keeps_the_task_queued_while_the_screen_is_busy(self):
        self.append('### [10-10-2026] Operador humano\n- **Hora:** 09:00:00\n- **Handoff:** fin.\n')
        self.sync_cursor()
        self.gateway.screen['p-' + BA] = CODEX_BUSY
        self.run_watcher([lambda: self.append('- **Handoff:** @BA: Redacta la HU.\n'), lambda: None, lambda: None])
        self.assertEqual(self.prompts('p-' + BA), [])
        self.assertEqual(self.agent()['state'], 'ready')
        del self.gateway.screen['p-' + BA]
        self.run_watcher([lambda: None])
        self.assertEqual(len(self.prompts('p-' + BA)), 1)


class VerifyGateTests(PaneCase):
    provider = 'fake-codex'

    def test_verify_never_types_its_probe_into_a_dialog(self):
        for name, (screen, _) in sorted(DIALOGS.items()):
            with self.subTest(name):
                self.reset_operations()
                self.rt.state.put('agent:' + BA, {**self.agent(), 'state': 'ready'})
                self.gateway.screen['p-' + BA] = screen
                with self.assertRaises(ReconciliationRequired):
                    self.maintenance().verify(BA)
                self.assertEqual(self.written(), [])
                op, = self.ops()
                self.assertEqual((op['state'], op['resolution']), ('REQUIRES_INTERVENTION', None))
                self.assertEqual(self.agent()['state'], 'awaiting_trust')
                screen_evidence = next(e for e in op['evidence'] if e['step'] == 'screen')
                self.assertIn(screen_evidence['state'], pane_state.HUMAN_STATES)

    def test_probe_with_digits_cannot_reach_a_menu(self):
        # The menu appears after the pre-check, while the probe is prepared; the probe is full of option digits.
        # The final check under the pane lock refuses it: the gate, not the text, protects the menu.
        original = maintenance.write_contract

        def dialog_appears(context, name):
            self.gateway.screen['p-' + BA] = CODEX_TRUST
            return original(context, name)
        with patch.object(maintenance, 'probe_nonce', return_value='1212121212'), \
                patch.object(maintenance, 'write_contract', side_effect=dialog_appears), \
                self.assertRaises(ReconciliationRequired):
            self.maintenance().verify(BA)
        self.assertEqual(self.written(), [])
        op, = self.ops()
        self.assertEqual([e['state'] for e in op['evidence'] if e['step'] == 'screen'], [READY_VERIFIED, AWAITING_TRUST])

    def test_probe_carries_no_digits(self):
        self.assertTrue(all(not re.search(r'\d', maintenance.probe_nonce()) for _ in range(500)))
        op = self.maintenance().verify(BA)
        prompt, = [c[2] for c in self.written() if c[0] == 'prompt']
        self.assertEqual((op['state'], re.findall(r'\d', prompt)), ('COMPLETED', []))

    def test_verify_on_unknown_or_starting_screen_holds_without_writing(self):
        for screen in (CLAUDE_STARTING, '', CODEX_BUSY):
            with self.subTest(screen[:20]):
                self.reset_operations()
                self.rt.state.put('agent:' + BA, {**self.agent(), 'state': 'ready'})
                self.gateway.screen['p-' + BA] = screen
                with self.assertRaises(ReconciliationRequired):
                    self.maintenance().verify(BA)
                self.assertEqual((self.written(), self.agent()['state']), ([], 'unverified'))

    def test_verify_waits_while_the_cli_is_still_drawing_its_composer(self):
        original, reads = self.gateway.read, []

        def read(pane, lines=40, source='recent'):
            if source == 'visible':
                reads.append(pane)
                if len(reads) <= 3:      # right after `agent start`: banner first, composer later
                    return CLAUDE_STARTING
            return original(pane, lines, source)
        self.gateway.read = read
        op = self.maintenance().verify(BA)
        self.assertEqual(op['state'], 'COMPLETED')
        self.assertEqual([c[0] for c in self.written()], ['prompt'])
        states = [e['state'] for e in op['evidence'] if e['step'] == 'screen']
        self.assertEqual(states, [READY_VERIFIED, READY_VERIFIED])     # pre-check after the wait, final check

    def test_clear_and_rotate_send_no_slash_command_into_a_dialog(self):
        self.configure('fake-claude')
        self.handoff(BA, '@BA:')
        self.gateway.screen['p-' + BA] = CLAUDE_PERMISSION
        for kind in ('CLEAR', 'ROTATE'):
            with self.subTest(kind), self.assertRaises(ReconciliationRequired):
                self.maintenance().run(kind, BA)
        self.assertEqual(self.written(), [])

    def test_pane_commands_are_typed_only_at_the_shell(self):
        _, provider = self.rt.factory.resolve(agent=BA)
        with self.assertRaises(ReconciliationRequired), patch.object(maintenance.os, 'name', 'nt'):
            self.maintenance().prepare_pane('p-' + BA, provider)     # the CLI is still in the foreground
        self.assertEqual(self.written(), [])


class RecoveryTests(PaneCase):
    """The E5.2 pilot: BA VERIFY completed; SA VERIFY REQUIRES_INTERVENTION after Codex quit."""
    provider = 'fake-codex'

    def pilot_state(self):
        ok = self.maintenance().verify(BA)
        self.assertEqual(ok['state'], 'COMPLETED')
        self.rt.state.put('agent:' + SA, {**self.agent(SA), 'state': 'starting'})
        self.gateway.prompt_error = DeliveryUncertain('agent_prompt_stalled')
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().verify(SA)
        self.gateway.prompt_error = None
        # Codex quit: Herdr no longer lists it and the pane is at its shell.
        self.gateway.agents.pop('p-' + SA)
        op = next(op for op in self.ops() if op['agent'] == SA)
        self.assertEqual(op['state'], 'REQUIRES_INTERVENTION')
        self.gateway.calls.clear()
        return op

    def relaunched(self):
        """The human relaunched Codex in the pane: a fresh CLI with an empty memory."""
        self.gateway.add(SA, 'p-' + SA, 'codex')
        self.gateway.memory['p-' + SA] = None

    def test_acknowledge_never_completes_a_maintenance_operation(self):
        op = self.pilot_state()
        with self.assertRaises(SystemExit), patch('sys.stderr'):
            state_module.main(['--root', str(self.root), '--acknowledge', 'maintenance:' + op['op_id'], '--confirm'])
        again = self.rt.state.get('maintenance:' + op['op_id'])
        self.assertEqual((again['state'], again['resolution']), ('REQUIRES_INTERVENTION', None))
        self.assertIn(SA, maintenance_blocks(self.rt.state))

    def test_reconcile_never_reuses_an_ended_pane_nor_probes_an_unknown_screen(self):
        op = self.pilot_state()
        with self.assertRaises(ReconciliationRequired) as raised:
            self.maintenance().reconcile(SA)
        self.assertIn('relaunch it manually', str(raised.exception))
        # A stale Herdr entry over a pane already at its shell is not a live agent either.
        self.relaunched()
        self.gateway.process_info = lambda pane: AT_SHELL
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().reconcile(SA)
        del self.gateway.process_info
        # Relaunched by the human but still behind its trust dialog: nothing typed.
        self.gateway.screen['p-' + SA] = CODEX_TRUST
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().reconcile(SA)
        self.assertEqual(self.written(), [])
        self.assertIsNone(self.rt.state.get('maintenance:' + op['op_id'])['resolution'])
        self.assertIn(SA, maintenance_blocks(self.rt.state))
        self.assertEqual(self.agent(BA)['state'], 'ready')      # the verified BA is untouched

    def test_human_decision_only_enables_a_new_verification(self):
        op = self.pilot_state()
        self.relaunched()
        # The human granted trust, but the CLI has not drawn its composer yet: still not ready.
        self.gateway.screen['p-' + SA] = CLAUDE_STARTING
        with self.assertRaises(ReconciliationRequired):
            self.maintenance().reconcile(SA)
        self.assertEqual(self.written(), [])
        self.assertTrue(self.rt.dispatcher.info(SA) == (None, None))    # held: the watcher cannot dispatch
        del self.gateway.screen['p-' + SA]
        done = self.maintenance().reconcile(SA)
        self.assertEqual((done['op_id'], done['resolution']['outcome']), (op['op_id'], 'fresh_context_verified'))
        self.assertEqual([c[0] for c in self.written()], ['prompt'])
        self.assertEqual(self.agent(SA)['state'], 'ready')
        self.assertNotIn(SA, maintenance_blocks(self.rt.state))
        # Only now does the next task go out.
        self.assertTrue(self.rt.dispatcher.dispatch(SA, 'p-' + SA, '@SA: plan', 'ev-after-recovery'))


class GlobalTrustTests(PaneCase):
    provider = 'fake-codex'

    def test_dialog_flows_touch_no_global_trust_file(self):
        with tempfile.TemporaryDirectory(prefix='BMAD home ') as home, \
                patch.dict(os.environ, {'HOME': home, 'USERPROFILE': home, 'CODEX_HOME': os.path.join(home, '.codex')}):
            self.gateway.screen['p-' + BA] = CODEX_TRUST
            for action in (lambda: self.rt.dispatcher.dispatch(BA, 'p-' + BA, '@BA: x', 'ev-home'),
                           lambda: self.maintenance().verify(BA), lambda: self.maintenance().reconcile(BA)):
                with self.assertRaises(ReconciliationRequired):
                    action()
            self.assertEqual(os.listdir(home), [])
        self.assertEqual(self.written(), [])

    def test_engine_never_references_global_trust_settings(self):
        for path in ENGINE.glob('*.py'):
            text = path.read_text(encoding='utf-8')
            for needle in ('.claude.json', 'config.toml', 'trust_level', 'hasTrustDialogAccepted'):
                self.assertNotIn(needle, text, f'{path.name} references {needle}')


if __name__ == '__main__':
    unittest.main()
