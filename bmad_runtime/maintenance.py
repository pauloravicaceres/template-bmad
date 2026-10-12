"""Explicit, ownership-checked session maintenance. No inferred tab deletion, no automatic clear or rotation."""
import argparse
import contextlib
from datetime import datetime
import hashlib
import json
import os
from pathlib import Path
import sys
import time
import uuid

from . import pane_state
from .config import AGENT_PHASES
from .context import ROLE_ALIASES, absolute_path, add_project_arguments, resolve_context
from .errors import (AgentBlocked, BMADRuntimeError, ConfigurationError, DeliveryRejected, ReconciliationRequired,
                     UnsupportedCapability)
from .herdr import PANE_PATH_REPAIR, native_pwsh, pane_pwsh_probe, parse_pwsh_probe, store_alias
from .runtime import Runtime
from .services import (clear_supported, contract_path, interactive_command, probe_text, probe_verdict, source_digests,
                       write_contract)
from .state import ProjectLock, StateStore, project_lock
from .watcher_service import (HOLD_STATES, MAINTENANCE_FINAL, SESSION_LOCK, maintenance_blocks, maintenance_records,
                              watcher_participation)

# Persistent state machines; FAILED = verified that nothing changed, REQUIRES_INTERVENTION = uncertain or partial.
# VERIFY checks a live agent (initial launch, recovery, reused pane) and never changes its context.
STEPS = {'ROTATE': ('REQUESTED', 'QUIESCED', 'STOPPING', 'STARTING', 'VERIFYING', 'COMPLETED'),
         'CLEAR': ('REQUESTED', 'QUIESCED', 'CLEARING', 'VERIFYING', 'COMPLETED'),
         'VERIFY': ('REQUESTED', 'VERIFYING', 'COMPLETED')}
FAILURES = ('FAILED', 'REQUIRES_INTERVENTION')
READY = {'idle', 'done'}


def close_owned_tabs(runtime):
    agents = runtime.gateway.list_agents()
    panes = runtime.gateway.list_panes()
    tabs = runtime.gateway.list_tabs()
    owned_tabs = []
    # Prefer the Herdr name recorded at launch; older records fall back to the current naming scheme.
    identities = {(runtime.state.get('agent:' + role) or {}).get('session_name') or runtime.context.session_name(role): role
                  for role in AGENT_PHASES}
    for tab in tabs:
        tab_id = tab['tab_id']
        owned = runtime.state.get('tab:' + tab_id)
        if not owned or owned['project'] != str(runtime.config.root):
            continue
        members = [pane for pane in panes if pane.get('tab_id') == tab_id]
        if not members:
            raise ReconciliationRequired('Cannot verify tab membership; close it manually.')
        for pane in members:
            pane_id = pane['pane_id']
            agent = next((a for a in agents if a.get('pane_id') == pane_id), None)
            role = identities.get(agent['name']) if agent else None
            record = runtime.state.get('agent:' + role) if role else None
            if not record or record['pane_id'] != pane_id or record.get('tab_id') != tab_id:
                raise ReconciliationRequired('Tab contains an unowned terminal; close it manually.')
            if agent.get('agent_status') not in {'idle', 'done'}:
                raise ReconciliationRequired('Tab contains a busy agent; wait before closing it.')
        owned_tabs.append((tab_id, members))
    # Validate every target first, then mutate.
    for tab_id, members in owned_tabs:
        runtime.gateway.close_tab(tab_id)
        for pane in members:
            agent = next(a for a in agents if a.get('pane_id') == pane['pane_id'])
            key = 'agent:' + identities[agent['name']]
            runtime.state.put(key, {**runtime.state.get(key), 'state': 'closed'})
    return len(owned_tabs)


def stop_main(root, argv=None):
    parser = argparse.ArgumentParser(description='Close only verified idle tabs created by this project.')
    parser.add_argument('--confirm', action='store_true', help='Explicitly authorize closing owned idle sessions.')
    parser.add_argument('--config', type=Path, help='Same configuration file as the watcher (default: config_bmad.json).')
    add_project_arguments(parser)
    args = parser.parse_args(argv)
    if not args.confirm:
        print('No sessions closed. Inspect Herdr, then pass --confirm to close owned idle tabs.')
        return 0
    rt = None
    try:
        # The same file resolves --project in its registry and checks project.json: a config of another project fails.
        context = resolve_context(root, workspace=args.workspace, project=args.project, config_path=args.config)
        with project_lock(context, 'maintenance'), project_lock(context, 'watcher'), project_lock(context, 'fleet'):
            rt = Runtime(root, config_path=args.config, context=context)
            pending = maintenance_blocks(rt.state)
            if pending:
                raise ReconciliationRequired('Session maintenance pending for ' + ', '.join(sorted(pending))
                                             + '; reconcile it (maintenance --reconcile) before closing tabs.')
            print(f'Closed tabs: {close_owned_tabs(rt)}')
        return 0
    except BMADRuntimeError as exc:
        print(f'ERROR: {exc}')
        return 1
    finally:
        if rt:
            rt.close()


class Coordination:
    """Cross-process exclusion shared with the watcher. Every lock is an OS lock: a crash releases it.

    Order: maintenance (one operation per workspace), watcher (held only when no watcher runs; a running
    watcher must advertise the protocol), fleet (no concurrent launch), sessions (the watcher takes it on
    every tick, so holding it pauses reading and dispatching). Nothing blocks indefinitely.
    """

    def __init__(self, context, state, *, clock=time.monotonic, sleep=time.sleep, wait_s=10):
        self.context, self.state, self.clock, self.sleep, self.wait_s = context, state, clock, sleep, wait_s
        self.locks, self.watcher = [], None

    def _take(self, name, message):
        lock = ProjectLock(self.context, name)
        if not lock.acquire():
            raise ReconciliationRequired(message)
        self.locks.append(lock)

    def __enter__(self):
        try:
            self._take('maintenance', 'Another session maintenance is running in this workspace.')
            watcher = ProjectLock(self.context, 'watcher')
            if watcher.acquire():
                # No watcher runs; holding its lock keeps one from starting mid-operation.
                self.locks.append(watcher)
                self.watcher = 'stopped'
            else:
                problem = watcher_participation(self.state)
                if problem:
                    raise ReconciliationRequired(
                        f'The watcher lock is held but no watcher takes part in session coordination ({problem}); '
                        'stop that process or update the watcher before maintenance.')
                self.watcher = 'coordinated'
            self._take('fleet', 'A fleet launch is running in this workspace.')
            sessions = ProjectLock(self.context, SESSION_LOCK)
            deadline = self.clock() + self.wait_s
            while not sessions.acquire():
                if self.clock() >= deadline:
                    raise ReconciliationRequired('The watcher kept the sessions lock; retry when its cycle is idle.')
                self.sleep(0.25)
            self.locks.append(sessions)
            return self
        except BaseException:
            self.release()
            raise

    def release(self):
        while self.locks:
            self.locks.pop().release()

    def __exit__(self, *exc):
        self.release()
        return False


def _kind(entry):
    # Herdr 0.8.2 reports the detected CLI as 'agent'.
    return entry.get('agent', entry.get('kind'))


def _same_path(left, right):
    return os.path.normcase(str(Path(left).resolve())).rstrip('\\/') == os.path.normcase(str(Path(right).resolve())).rstrip('\\/')


def probe_nonce():
    """Maintenance probe id without digits: typed into a menu by mistake, a digit selects an option (E5.2)."""
    return uuid.uuid4().hex[:12].translate(str.maketrans('0123456789', 'ghijklmnop'))


def _iso(stamp=None):
    return datetime.fromtimestamp(stamp if stamp is not None else time.time()).astimezone().isoformat(timespec='seconds')


class SessionMaintenance:
    """Operator-confirmed CLEAR (Claude only), ROTATE and VERIFY of one owned agent. Never retries; never falls back."""
    exit_timeout_s = 45
    ready_timeout_s = 120
    verify_timeout_s = 300
    shell_timeout_s = 20
    poll_s = 2

    def __init__(self, runtime, *, clock=time.monotonic, sleep=time.sleep, now=time.time):
        self.rt, self.clock, self.sleep, self.now = runtime, clock, sleep, now
        self.state, self.context, self.gateway = runtime.state, runtime.context, runtime.gateway
        # Same per-pane locks as the dispatcher (they live in the workspace state directory).
        self.gate = pane_state.PaneGate(self.gateway, self.context, sleep=sleep, clock=clock)

    # Persistence -------------------------------------------------------------------------------
    def _put(self, op, *extra):
        op['updated'] = self.now()
        self.state.put_many([('maintenance:' + op['op_id'], op), *extra])

    def _advance(self, op, new_state, *extra, **details):
        sequence = STEPS[op['kind']]
        if new_state not in FAILURES and (op['state'] not in sequence
                                          or sequence.index(new_state) != sequence.index(op['state']) + 1):
            raise ReconciliationRequired(f'Invalid maintenance transition {op["state"]} -> {new_state}.')
        op.update(details)
        op['state'] = new_state
        op['states'][new_state] = self.now()
        self._put(op, *extra)

    def _evidence(self, op, step, **detail):
        op['evidence'].append({'step': step, 'at': _iso(self.now()), **detail})
        self._put(op)

    def _record_failure(self, op, state, error, *, uncertain, hold=None):
        op['errors'].append({'at': _iso(self.now()), 'during': op['state'], 'error': str(error)[:500]})
        op['uncertain'] = uncertain
        op['result'] = 'failed' if state == 'FAILED' else 'requires_intervention'
        owned = self.state.get('agent:' + op['agent']) or {}
        extra = []
        if state == 'FAILED' and owned.get('maintenance_op') == op['op_id']:
            # Verified: nothing reached the agent; the session keeps serving its role.
            extra.append(('agent:' + op['agent'], {**{k: v for k, v in owned.items() if k != 'maintenance_op'},
                                                    'state': 'ready'}))
        elif hold and owned:
            # The watcher holds tasks for agents in HOLD_STATES until --reconcile verifies them.
            extra.append(('agent:' + op['agent'], {**owned, 'state': hold}))
        self._advance(op, state, *extra)

    def _fail(self, op, state, error, *, uncertain, hold=None):
        self._record_failure(op, state, error, uncertain=uncertain, hold=hold)
        raise ReconciliationRequired(f'{op["kind"]} {op["agent"]}: {error}. Operation {op["op_id"]} is {state}; '
                                     + ('nothing changed.' if state == 'FAILED' else
                                        'inspect the pane, then run --reconcile.'))

    def _new_op(self, kind, name, selection, owned, session, coordination, reasons=None, herdr_status=None):
        now = self.now()
        return {'op_id': uuid.uuid4().hex, 'kind': kind, 'project_id': self.context.project_id,
                'workspace': str(self.context.workspace_root), 'agent': name, 'provider': selection.provider,
                'model': selection.model, 'session_name': session, 'pane_id': owned['pane_id'],
                'run_id': owned.get('run_id'),
                'generation_before': owned.get('generation', 1), 'generation_after': None,
                'state': 'REQUESTED', 'states': {'REQUESTED': now}, 'created': _iso(now), 'result': None,
                'summary': None, 'summary_sha256': None, 'contract': None, 'errors': [], 'uncertain': False,
                'resolution': None,
                'evidence': [{'step': 'eligibility', 'at': _iso(now), 'reasons': reasons or [],
                              'herdr_status': herdr_status, 'watcher': coordination}]}

    # Herdr observations ------------------------------------------------------------------------
    def _entry(self, session):
        return next((agent for agent in self.gateway.list_agents() if agent.get('name') == session), None)

    def _shell(self, pane):
        """(at_shell, foreground process names) of a pane."""
        info = self.gateway.process_info(pane)
        processes = info.get('foreground_processes') or []
        names = [str(process.get('name')) for process in processes]
        return bool(processes) and all(process.get('pid') == info.get('shell_pid') for process in processes), names

    def _poll(self, timeout, check):
        deadline = self.clock() + timeout
        while True:
            result = check()
            if result is not None:
                return result
            if self.clock() >= deadline:
                return None
            self.sleep(self.poll_s)

    def _wait_ready(self, op, provider):
        def ready():
            entry = self._entry(op['session_name'])
            if entry and entry.get('pane_id') == op['pane_id']:
                if entry.get('agent_status') == 'blocked':
                    return 'blocked'
                if entry.get('agent_status') in READY:
                    return entry
            return None
        entry = self._poll(self.ready_timeout_s, ready)
        if entry == 'blocked':
            # Herdr may report a trust dialog as 'blocked': name it when the screen shows it.
            self._check_blocker(op, provider)
            self._fail(op, 'REQUIRES_INTERVENTION', 'agent waits for a permission or input dialog; nothing was approved',
                       uncertain=True)
        if entry is None:
            self._fail(op, 'REQUIRES_INTERVENTION', 'agent not ready in its pane before the timeout', uncertain=True)
        if _kind(entry) not in (None, provider.herdr_kind):
            self._fail(op, 'REQUIRES_INTERVENTION', f'unexpected agent kind {_kind(entry)}', uncertain=True)
        return entry

    def _check_blocker(self, op, provider):
        """H10: Herdr reports the CLI ready while it waits for a dialog; nothing is answered automatically."""
        blocker = self.gate.blocker(provider, op['pane_id'])
        if blocker:
            self._evidence(op, 'blocker', blocker=blocker)
            self._fail(op, 'REQUIRES_INTERVENTION',
                       f'{blocker} on screen; answer it manually in pane {op["pane_id"]} (never automated)',
                       uncertain=False, hold='awaiting_trust')

    def _require_ready(self, op, provider, *, status=None, wait=False):
        """Fase 4F-E5.2.1: nothing is written to the pane unless it is READY_VERIFIED (pane_state).

        A dialog holds the agent as 'awaiting_trust'; an exited CLI, a running turn or an ambiguous screen as
        'unverified'. Either way only maintenance --reconcile releases it, after a new verification.
        wait=True (after a launch, /clear or a human decision): a busy or still-rendering screen is read again
        until ready_timeout_s; a dialog or an exited CLI ends the wait at once. Nothing is written meanwhile.
        """
        last = {}

        def settled():
            last['observation'] = self.gate.observe(provider, op['pane_id'], herdr_status=status)
            observation = last['observation']
            done = observation.ready or observation.state in (*pane_state.HUMAN_STATES, pane_state.EXITED)
            return observation if done or not wait else None
        observation = self._poll(self.ready_timeout_s, settled) or last['observation']
        self._evidence(op, 'screen', **observation.as_dict())
        if observation.ready:
            return observation
        if observation.state in pane_state.HUMAN_STATES:
            self._evidence(op, 'blocker', blocker=observation.blocker)
            self._fail(op, 'REQUIRES_INTERVENTION',
                       f'{observation.blocker} on screen; answer it manually in pane {op["pane_id"]} (never automated)',
                       uncertain=False, hold='awaiting_trust')
        self._fail(op, 'REQUIRES_INTERVENTION',
                   f'pane {op["pane_id"]} is not verified ready ({observation.state}: {observation.reason}); '
                   'nothing was written', uncertain=False, hold='unverified')

    # Pane shell (H8) ---------------------------------------------------------------------------
    def _probe_pwsh(self, pane):
        nonce = uuid.uuid4().hex[:8]
        pane_state.require_shell(self.gateway, pane)
        self.gateway.run_in_pane(pane, pane_pwsh_probe(nonce))
        found = self._poll(self.shell_timeout_s,
                           lambda: parse_pwsh_probe(self.gateway.read(pane, 40, source='recent-unwrapped'), nonce))
        if found is None:
            raise ReconciliationRequired(f'pane {pane} shell did not answer the pwsh probe; is it at its prompt?')
        return found

    def prepare_pane(self, pane, provider):
        """Before a sandboxed Codex starts in a pane, its shell must resolve pwsh outside WindowsApps.

        Panes created by the runtime get pane_env_args(); panes restored or reused by Herdr keep the server's
        PATH. The same Store-alias-last ordering is applied to that pane shell only, then checked again.
        Nothing global changes; an incompatible pane is refused with a diagnosis.
        """
        if os.name != 'nt' or not getattr(provider, 'requires_native_pwsh', False):
            return {'checked': False}
        observed = self._probe_pwsh(pane)
        evidence = {'checked': True, 'pane_pwsh': observed or None, 'repaired': False}
        if store_alias(observed):
            pane_state.require_shell(self.gateway, pane)
            self.gateway.run_in_pane(pane, PANE_PATH_REPAIR)
            observed = self._probe_pwsh(pane)
            evidence.update(repaired=True, pane_pwsh_after=observed or None)
            if store_alias(observed):
                raise UnsupportedCapability(
                    f'pane {pane} resolves pwsh only to the Microsoft Store alias ({observed}); the Codex sandbox cannot '
                    'start it (CreateProcessAsUserW failed: 5). Install PowerShell 7 (MSI) or use a pane created by '
                    'the runtime; the sandbox is never disabled.')
        return evidence

    def start_agent(self, session, pane, provider, native):
        """herdr agent start; when it fails because the CLI shows a dialog (Herdr 0.8.2 may report it 'blocked'
        and time out, or 'idle'), the failure is diagnosed as AgentBlocked instead of an uncertain launch."""
        # `herdr agent start` types the launch command into the pane: only into its shell.
        pane_state.require_shell(self.gateway, pane)
        try:
            self.gateway.start(session, pane, provider, native)
        except BMADRuntimeError as exc:
            blocker = self.gate.blocker(provider, pane)
            if blocker:
                raise AgentBlocked(f'{blocker} on screen in pane {pane}; answer it manually (never automated), then run '
                                   'maintenance --reconcile ROL --confirm.') from exc
            raise

    def machine_pwsh(self, provider):
        if os.name == 'nt' and getattr(provider, 'requires_native_pwsh', False):
            found, compatible = native_pwsh()
            if not compatible:
                raise UnsupportedCapability(f'Only the Microsoft Store pwsh alias is installed ({found}); the Codex '
                                            'sandbox cannot start it. Install PowerShell 7 (MSI) before starting Codex.')

    # Identity --------------------------------------------------------------------------------------
    def identity(self, name, owned, provider, selection):
        """Deterministic facts, independent of the model: (problems, evidence). Unavailable data is not a problem."""
        problems, evidence = [], {}
        session = owned.get('session_name') or self.context.session_name(name)
        if not self.context.legacy and session != self.context.session_name(name):
            problems.append('session_name')
        if (owned.get('provider'), owned.get('model')) != (selection.provider, selection.model):
            problems.append('provider_model')
        entry = self._entry(session)
        if not entry or entry.get('pane_id') != owned.get('pane_id'):
            return problems + ['herdr_identity'], evidence
        evidence['herdr'] = {'status': entry.get('agent_status'), 'agent': _kind(entry)}
        if _kind(entry) not in (None, provider.herdr_kind):
            problems.append('agent_kind')
        if not self.context.legacy:
            pane = next((p for p in self.gateway.list_panes() if p.get('pane_id') == owned['pane_id']), None)
            cwd = entry.get('cwd') or (pane or {}).get('cwd')
            if pane is None:
                problems.append('pane_missing')
            elif cwd and not _same_path(cwd, self.context.workspace_root):
                problems.append('workspace')
            evidence['cwd'] = cwd
        info = self.gateway.process_info(owned['pane_id'])
        processes = [p for p in info.get('foreground_processes') or [] if p.get('pid') != info.get('shell_pid')]
        evidence['processes'] = [p.get('name') for p in processes]
        if not processes:
            problems.append('process_absent')
        else:
            argv = ' '.join(' '.join(map(str, p.get('argv') or [p.get('name') or ''])) for p in processes)
            if provider.herdr_kind not in argv.lower():
                problems.append('process_kind')
            if provider.identifier == 'claude' and any(p.get('argv') for p in processes):
                # Claude receives the contract as system prompt file: the running process must reference it.
                loaded = os.path.normcase(str(contract_path(self.context, name))) in os.path.normcase(argv)
                evidence['contract_loaded'] = loaded
                if not loaded:
                    problems.append('contract_not_loaded')
        current = source_digests(self.context, name)
        evidence['contract_current'] = owned.get('contract_sources', current) == current
        generation = owned.get('generation', 1)
        # Generations count within one launch (run_id): a new launch starts again at 1. Operations recorded
        # before 4B.1 carry no run_id and are not attributed to any launch.
        recorded = [op for op in maintenance_records(self.state)
                    if op.get('agent') == name and op.get('generation_after') is not None
                    and op.get('run_id') and op.get('run_id') == owned.get('run_id')]
        if recorded and max(recorded, key=lambda op: op.get('updated', 0))['generation_after'] != generation:
            problems.append('generation')
        evidence['generation'] = generation
        return problems, evidence

    def _require_identity(self, op, provider, selection):
        owned = self.state.get('agent:' + op['agent'])
        problems, evidence = self.identity(op['agent'], owned, provider, selection)
        self._evidence(op, 'identity', problems=problems, **evidence)
        if problems:
            self._fail(op, 'REQUIRES_INTERVENTION', 'deterministic identity check failed: ' + ', '.join(problems),
                       uncertain=True)
        return evidence

    def _target(self, name, kind):
        selection, provider = self.rt.factory.resolve(agent=name)
        if kind == 'CLEAR' and not clear_supported(provider):
            raise UnsupportedCapability(f'{name}: --clear is available only for Claude Code with verified capability; '
                                        f'{selection.provider} supports --rotate only.')
        row = self.rt.sessions.plan(self.state, names=[name])[0]
        if row['eligibility'] != 'ELIGIBLE':
            raise ReconciliationRequired(f'{name} is not eligible: {", ".join(row["reasons"])}.')
        owned = self.state.get('agent:' + name)
        problems, _ = self.identity(name, owned, provider, selection)
        if problems:
            raise ReconciliationRequired(f'{name}: Herdr identity changed since the eligibility check ({", ".join(problems)}).')
        observation = self.gate.observe(provider, owned['pane_id'], herdr_status=row['herdr_status'])
        if observation.state in pane_state.HUMAN_STATES:
            raise ReconciliationRequired(f'{name}: a dialog waits for a human answer in pane {owned["pane_id"]} '
                                         f'({observation.blocker}).')
        if not observation.ready:
            raise ReconciliationRequired(f'{name}: pane {owned["pane_id"]} is not verified ready '
                                         f'({observation.state}: {observation.reason}); nothing was sent.')
        return selection, provider, owned, row

    # Operations --------------------------------------------------------------------------------
    def run(self, kind, name):
        with Coordination(self.context, self.state, clock=self.clock, sleep=self.sleep) as coordination:
            # Re-evaluated under exclusion: the watcher cannot dispatch while the sessions lock is held.
            selection, provider, owned, row = self._target(name, kind)
            if kind == 'ROTATE':
                # Relaunch prerequisites are checked before the old session is stopped.
                provider.verify(self.rt.runner, self.rt.config.root, headless=False)
                self.gateway.verify_provider(provider)
                interactive_command(self.rt.config, provider, selection, name)
                self.machine_pwsh(provider)
            op = self._new_op(kind, name, selection, owned, row['session_name'], coordination.watcher,
                              row['reasons'], row['herdr_status'])
            try:
                self._put(op)
                self._quiesce(op, owned)
                if kind == 'ROTATE':
                    self._rotate(op, provider, selection)
                else:
                    self._clear(op, provider, selection)
                return op
            except BaseException as exc:
                if op['state'] not in (*FAILURES, 'COMPLETED'):
                    # Before STOPPING/CLEARING nothing was sent to the agent.
                    unsent = op['state'] in ('REQUESTED', 'QUIESCED')
                    self._record_failure(op, 'FAILED' if unsent else 'REQUIRES_INTERVENTION',
                                         f'interrupted: {type(exc).__name__}: {exc}', uncertain=not unsent)
                raise

    def _quiesce(self, op, owned):
        name = op['agent']
        summary = self.state.get('session:' + name)
        # Verifiable summary of the outgoing session (validated complete by the plan) and a fresh contract.
        contract = write_contract(self.context, name)
        self._advance(op, 'QUIESCED',
                      ('agent:' + name, {**owned, 'state': 'maintenance', 'maintenance_op': op['op_id']}),
                      summary=summary,
                      summary_sha256=hashlib.sha256(json.dumps(summary, sort_keys=True, ensure_ascii=False).encode()).hexdigest(),
                      contract={'path': contract.relative_to(self.context.workspace_root).as_posix(),
                                'sources': source_digests(self.context, name)})

    def _clear(self, op, provider, selection):
        with self.gate.exclusive(op['pane_id']):
            # An Enter typed into a dialog answers it: /clear goes only to a verified idle composer.
            self._require_ready(op, provider)
            self._advance(op, 'CLEARING')
            try:
                self.gateway.submit(op['pane_id'], provider.clear_instruction())
            except DeliveryRejected as exc:
                self._fail(op, 'FAILED', f'/clear rejected before sending ({exc})', uncertain=False)
            except BMADRuntimeError as exc:
                self._fail(op, 'REQUIRES_INTERVENTION', f'/clear delivery uncertain ({exc})', uncertain=True)
        self._evidence(op, 'clear_submitted', command='/clear')
        self.sleep(self.poll_s)
        # /clear keeps the same CLI process: the agent must still be ours, in the same pane.
        entry = self._wait_ready(op, provider)
        self._require_ready(op, provider, status=entry.get('agent_status'), wait=True)
        self._require_identity(op, provider, selection)
        self._advance(op, 'VERIFYING')
        self._verify(op, provider)
        self._complete(op)

    def _rotate(self, op, provider, selection):
        with self.gate.exclusive(op['pane_id']):
            self._require_ready(op, provider)
            self._advance(op, 'STOPPING')
            try:
                self.gateway.submit(op['pane_id'], '/exit')
            except DeliveryRejected as exc:
                self._fail(op, 'FAILED', f'/exit rejected before sending ({exc})', uncertain=False)
            except BMADRuntimeError as exc:
                # The command may still have arrived; the observed process state decides.
                self._evidence(op, 'exit_delivery_uncertain', error=str(exc)[:300])

        def exited():
            entry = self._entry(op['session_name'])
            if entry and entry.get('pane_id') == op['pane_id'] and entry.get('agent_status') != 'unknown':
                return None
            at_shell, names = self._shell(op['pane_id'])
            return names if at_shell else None
        processes = self._poll(self.exit_timeout_s, exited)
        if processes is None:
            self._fail(op, 'REQUIRES_INTERVENTION', '/exit not confirmed: the agent is still running or the pane is not at its shell',
                       uncertain=True)
        self._evidence(op, 'exited_to_shell', foreground=processes)
        self._advance(op, 'STARTING')
        try:
            # H8: the reused pane keeps its own environment; check (and fix for this pane only) before launching.
            self._evidence(op, 'pane_shell', **self.prepare_pane(op['pane_id'], provider))
        except BMADRuntimeError as exc:
            self._fail(op, 'REQUIRES_INTERVENTION', f'pane shell not compatible: {exc}', uncertain=False)
        try:
            native = interactive_command(self.rt.config, provider, selection, op['agent'])
            self.start_agent(op['session_name'], op['pane_id'], provider, native)
        except AgentBlocked as exc:
            self._fail(op, 'REQUIRES_INTERVENTION', f'relaunch waits for a dialog: {exc}', uncertain=False,
                       hold='awaiting_trust')
        except BMADRuntimeError as exc:
            self._fail(op, 'REQUIRES_INTERVENTION', f'relaunch failed ({exc})', uncertain=True)
        entry = self._wait_ready(op, provider)
        self._evidence(op, 'relaunched', herdr_status=entry.get('agent_status'))
        self._require_ready(op, provider, status=entry.get('agent_status'), wait=True)
        self._require_identity(op, provider, selection)
        self._advance(op, 'VERIFYING')
        self._verify(op, provider)
        self._complete(op)

    def verify(self, name, *, initial=False, coordinated=True):
        """VERIFY a live agent: deterministic identity and dialogs first, then its reply. Changes no context.

        initial=True is the post-launch check of the fleet (it holds the fleet lock and the agent is not
        dispatchable yet): the reply must also show an empty memory.
        """
        coordination = (Coordination(self.context, self.state, clock=self.clock, sleep=self.sleep)
                        if coordinated else contextlib.nullcontext())
        with coordination as held:
            selection, provider = self.rt.factory.resolve(agent=name)
            owned = self.state.get('agent:' + name)
            if not owned or owned.get('state') in ('closed', 'uncertain'):
                raise ReconciliationRequired(f'{name}: no owned session to verify.')
            if name in maintenance_blocks(self.state):
                raise ReconciliationRequired(f'{name}: maintenance pending; use --reconcile.')
            if not initial and name in (self.state.get('followup') or {}):
                raise ReconciliationRequired(f'{name}: a dispatched task is in progress; verify when it is confirmed.')
            session = owned.get('session_name') or self.context.session_name(name)
            op = self._new_op('VERIFY', name, selection, owned, session,
                              held.watcher if coordinated else 'fleet_launch')
            try:
                self._put(op)
                return self._run_verify(op, provider, selection, fresh_required=initial)
            except BaseException as exc:
                if op['state'] not in (*FAILURES, 'COMPLETED'):
                    self._record_failure(op, 'REQUIRES_INTERVENTION', f'interrupted: {type(exc).__name__}: {exc}',
                                         uncertain=True, hold='unverified')
                raise

    def _run_verify(self, op, provider, selection, *, fresh_required):
        try:
            entry = self._wait_ready(op, provider)
            self._require_ready(op, provider, status=entry.get('agent_status'), wait=True)
            self._require_identity(op, provider, selection)
            self._advance(op, 'VERIFYING')
            write_contract(self.context, op['agent'])
            self._verify(op, provider, allow_previous_context=not fresh_required)
        except ReconciliationRequired:
            owned = self.state.get('agent:' + op['agent']) or {}
            if owned.get('state') == 'ready':
                # Not verified: held until --reconcile.
                self.state.put('agent:' + op['agent'], {**owned, 'state': 'unverified'})
            raise
        return self._complete(op)

    def _verify(self, op, provider, *, allow_previous_context=False):
        """Ask the agent to reload its current contract and prove role, project, workspace, profile and memory."""
        name, nonce = op['agent'], probe_nonce()
        path = self.context.state_dir / 'maintenance' / f'{nonce}.md'
        path.parent.mkdir(parents=True, exist_ok=True)
        with path.open('x', encoding='utf-8', newline='\n') as handle:
            handle.write(probe_text(self.context, name, nonce))
        relative = path.relative_to(self.context.workspace_root).as_posix()
        with self.gate.exclusive(op['pane_id']):
            # Final check right before writing (E5.2: the probe was typed into a Codex trust menu).
            self._require_ready(op, provider)
            try:
                self.gateway.prompt(op['pane_id'], f'[BMAD-MANT {nonce}] Lee y ejecuta íntegramente {relative}')
            except BMADRuntimeError as exc:
                self._fail(op, 'REQUIRES_INTERVENTION', f'verification request not delivered ({exc})', uncertain=True)
        expected = {'nonce': nonce, 'role': name, 'project_id': self.context.project_id,
                    'workspace': str(self.context.workspace_root),
                    'digests': list(source_digests(self.context, name).values())}
        last = {}

        def answered():
            entry = self._entry(op['session_name'])
            if not entry or entry.get('pane_id') != op['pane_id']:
                return ('lost', {})
            if entry.get('agent_status') == 'blocked':
                return ('blocked', {})
            verdict, details = probe_verdict(self.gateway.read(op['pane_id'], 200), **expected)
            last.update(verdict=verdict, details=details)
            if entry.get('agent_status') in READY and verdict in {'verified', 'mismatch'}:
                return verdict, details
            return None
        outcome = self._poll(self.verify_timeout_s, answered)
        verdict, details = outcome or (last.get('verdict', 'absent'), last.get('details', {}))
        problems = details.get('problems', [])
        if verdict == 'mismatch' and allow_previous_context and problems == ['context_not_reset']:
            verdict = 'verified_previous_context'
        self._evidence(op, 'verification', request=relative, verdict=verdict, **details)
        if verdict == 'lost':
            self._fail(op, 'REQUIRES_INTERVENTION', 'agent identity lost during verification', uncertain=True)
        if verdict == 'blocked':
            self._fail(op, 'REQUIRES_INTERVENTION', 'agent asked for a permission during verification; nothing was approved',
                       uncertain=True)
        if verdict not in {'verified', 'verified_previous_context'}:
            reason = ('verification reply not observed before the timeout' if outcome is None else
                      'verification failed: ' + ', '.join(problems))
            self._fail(op, 'REQUIRES_INTERVENTION', reason, uncertain=True)
        return verdict == 'verified'

    def _complete(self, op, *, fresh=True, resolution=None):
        owned = self.state.get('agent:' + op['agent'])
        # VERIFY never changes the context, so it never changes the generation.
        bump = fresh and op['kind'] != 'VERIFY'
        generation = op['generation_before'] + 1 if bump else owned.get('generation', 1)
        agent = {**{k: v for k, v in owned.items() if k not in ('maintenance_op', 'blocker')}, 'state': 'ready',
                 'generation': generation, 'last_maintenance': op['op_id'],
                 # The verified agent re-read this contract: later identity checks compare against it.
                 'contract_sources': source_digests(self.context, op['agent']), 'verified_at': _iso(self.now())}
        if bump:
            agent['session_refreshed_at'] = _iso(self.now())
        update = ('agent:' + op['agent'], agent)
        # Generation, agent record and final state change in one transaction, only after verification.
        if resolution:
            op.update(resolution=resolution, generation_after=generation)
            self._put(op, update)
        else:
            op['result'] = 'success'
            self._advance(op, 'COMPLETED', update, generation_after=generation)
        return op

    def reconcile(self, name):
        """After inspecting the pane: verify the live agent and release the block. Never relaunches or retries."""
        with Coordination(self.context, self.state, clock=self.clock, sleep=self.sleep) as held:
            selection, provider = self.rt.factory.resolve(agent=name)
            pending = [op for op in maintenance_records(self.state)
                       if op.get('agent') == name and op.get('state') not in MAINTENANCE_FINAL and not op.get('resolution')]
            if not pending:
                owned = self.state.get('agent:' + name) or {}
                if owned.get('state') not in HOLD_STATES:
                    return None
                # Held without an operation (e.g. a dialog seen at dispatch): verify it as a new VERIFY.
                op = self._new_op('VERIFY', name, selection, owned,
                                  owned.get('session_name') or self.context.session_name(name), held.watcher)
                self._put(op)
                return self._run_verify(op, provider, selection, fresh_required=False)
            op = max(pending, key=lambda item: item['states'].get('REQUESTED', 0))
            if op['state'] not in FAILURES:
                # The process that ran it ended before a final state (crash or kill).
                self._record_failure(op, 'REQUIRES_INTERVENTION', f'interrupted during {op["state"]}', uncertain=True)
            entry = self._entry(op['session_name'])
            if not entry or entry.get('pane_id') != op['pane_id']:
                native = interactive_command(self.rt.config, provider, selection, name)
                command = self.gateway.start_command(op['session_name'], op['pane_id'], provider, native).sanitized()
                write_contract(self.context, name)
                shell = (' For Codex on Windows the pane shell must resolve pwsh outside WindowsApps '
                         '(see SETUP.md, Arranque y entrega en Herdr).' if getattr(provider, 'requires_native_pwsh', False) else '')
                raise ReconciliationRequired(f'{name} is not running in pane {op["pane_id"]}. Check the pane is at its shell, '
                                             f'relaunch it manually with: {command} ; then run --reconcile again.{shell}')
            if entry.get('agent_status') not in READY:
                raise ReconciliationRequired(f'{name} is {entry.get("agent_status")}; wait or inspect before reconciling.')
            # A human decision (e.g. trust granted by hand) only enables this new check; it never implies ready.
            self._require_ready(op, provider, status=entry.get('agent_status'), wait=True)
            self._require_identity(op, provider, selection)
            write_contract(self.context, name)
            fresh = self._verify(op, provider, allow_previous_context=True)
            return self._complete(op, fresh=fresh, resolution={
                'at': _iso(self.now()), 'by': 'operator',
                'outcome': 'fresh_context_verified' if fresh else 'previous_context_verified'})


def _role(value):
    if value in AGENT_PHASES:
        return value
    aliases = {alias: role for role, alias in ROLE_ALIASES.items()}
    if value in aliases and aliases[value] in AGENT_PHASES:
        return aliases[value]
    raise ConfigurationError(f'Unknown agent role: {value}')


def _report(op):
    return {key: op.get(key) for key in ('op_id', 'kind', 'agent', 'provider', 'project_id', 'workspace', 'state',
                                         'result', 'generation_before', 'generation_after', 'resolution')}


def main(root, argv=None):
    """Session lifecycle CLI: --plan-clear never writes; --clear/--rotate/--reconcile change one agent with --confirm."""
    parser = argparse.ArgumentParser(description='Operator-driven session lifecycle: read-only plan, or a confirmed '
                                                 'CLEAR (Claude only), ROTATE or reconciliation of one owned agent.')
    action = parser.add_mutually_exclusive_group(required=True)
    action.add_argument('--plan-clear', action='store_true', help='Report eligibility of every owned agent; changes nothing.')
    action.add_argument('--clear', metavar='ROL', help='Send /clear to an eligible Claude Code agent and verify its role.')
    action.add_argument('--rotate', metavar='ROL', help='Exit and relaunch an eligible agent in its pane and verify it.')
    action.add_argument('--reconcile', metavar='ROL', help='After inspection, verify the live agent of an interrupted or '
                                                           'uncertain operation (or one held by a dialog) and release its block.')
    action.add_argument('--verify', metavar='ROL', help='Check identity of a live, idle agent (deterministic checks and its '
                                                        'reply); changes no context.')
    parser.add_argument('--confirm', action='store_true', help='Explicitly authorize --clear, --rotate, --reconcile or --verify.')
    parser.add_argument('--config', type=Path, help='Same configuration file as the watcher (default: config_bmad.json).')
    add_project_arguments(parser)
    args = parser.parse_args(argv)
    if args.plan_clear and args.confirm:
        parser.error('--plan-clear is read-only and takes no --confirm.')
    try:
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass
    store = rt = None
    try:
        context = resolve_context(root, workspace=args.workspace, project=args.project, config_path=args.config)
        role = None if args.plan_clear else _role(args.clear or args.rotate or args.reconcile or args.verify)
        if args.plan_clear or not args.confirm:
            # Read-only: no locks, no state writes, no prompts to agents.
            report = {'mode': 'dry_run', 'project_id': context.project_id, 'workspace': str(context.workspace_root),
                      'config': str(absolute_path(args.config, root)) if args.config else 'default', 'agents': []}
            store = StateStore.open_readonly(context)
            if store is None:
                report['reason'] = 'state_missing'
            else:
                report['agents'] = Runtime(root, config_path=args.config, context=context, persist=False).sessions.plan(
                    store, names=[role] if role else None)
            if role:
                report['note'] = 'Nothing changed. Re-run with --confirm to authorize this operation.'
            print(json.dumps(report, ensure_ascii=False, indent=2))
            return 0
        rt = Runtime(root, config_path=args.config, context=context)
        maintenance = SessionMaintenance(rt)
        if args.reconcile:
            op = maintenance.reconcile(role)
            print(json.dumps(_report(op) if op else {'agent': role, 'result': 'nothing_to_reconcile'},
                             ensure_ascii=False, indent=2))
        elif args.verify:
            print(json.dumps(_report(maintenance.verify(role)), ensure_ascii=False, indent=2))
        else:
            print(json.dumps(_report(maintenance.run('CLEAR' if args.clear else 'ROTATE', role)), ensure_ascii=False, indent=2))
        return 0
    except BMADRuntimeError as exc:
        print(f'ERROR: {exc}')
        return 1
    finally:
        if store:
            store.close()
        if rt:
            rt.close()


# Earlier name of the read-only entry point.
plan_main = main


if __name__ == '__main__':
    raise SystemExit(main(Path(__file__).resolve().parents[1]))
