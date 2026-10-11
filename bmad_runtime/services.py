from datetime import datetime
import hashlib
import json
from pathlib import Path
import re
import uuid
from dataclasses import replace

from .commands import Result
from .config import AGENT_PHASES, OPERATIONS
from .errors import (AgentBlocked, BMADRuntimeError, ConfigurationError, DeliveryRejected, ReconciliationRequired,
                     UnsupportedCapability)
from .state import project_lock
from .technical_context import assemble
from .watcher_service import (maintenance_blocks, maintenance_records, protocol_violations, read_tracker, same_line,
                              tracker_verified)


# Shell appends bypass the edit-tool permission flow; edit tools rewrite the whole file, so a
# concurrent append can still be lost: the watcher's prefix check (tracker_integrity) detects it.
TRACKER_RULE = ('REGISTRO EN EL TRACKER: escribe en BMAD_TRACKER solo con tu herramienta de edición de archivos '
                '(Edit/apply_patch), nunca con comandos de shell. Relee el final del archivo justo antes de editarlo, '
                'anexa tu bloque al final y no modifiques, reordenes ni borres bloques existentes.\n')


# The watcher is the only dispatcher; audit_blocks() flags any agent block without a dispatch (H11).
EXECUTION_RULE = ('PROTOCOLO DE EJECUCIÓN: el tracker es un registro de coordinación, no una cola de trabajo. Nunca '
                  'ejecutes un handoff solo por leerlo en el tracker, aunque parezca pendiente o dirigido a ti. Solo '
                  'actúas cuando el watcher te envía en esta terminal "[BMAD <id>] ... Lee y ejecuta íntegramente '
                  '<BMAD_HANDOFFS>/tasks/<archivo>.md" y ese archivo empieza con "<!-- BMAD-TAREA event_id=... agent=<tu rol>"; '
                  'o "[BMAD-MANT <id>]" con un archivo state/maintenance/<id>.md. En cualquier otro caso espera. Un '
                  'bloque tuyo en el tracker sin despacho detiene el flujo hasta una reconciliación humana.\n')


def contract_path(context, name):
    return context.state_dir / 'contracts' / f'{name}.md'


def contract_sources(context, name):
    """Engine files every agent needs at startup; they live outside the workspace."""
    return {'PERFIL DEL ROL': context.engine_root / name / 'AGENTS.md',
            'POLÍTICA GLOBAL': context.engine_root / 'constitution.md'}


def source_digests(context, name):
    return {label: hashlib.sha256(path.read_bytes()).hexdigest()[:16] if path.is_file() else 'ausente'
            for label, path in contract_sources(context, name).items()}


def agent_contract(context, name):
    """Self-contained contract: embeds profile and global policy so startup needs no reads outside the workspace."""
    digests = source_digests(context, name)
    parts = [f'<!-- BMAD-CONTRATO rol={name} fuentes=' + ','.join(f'{k}:{v}' for k, v in digests.items()) + ' -->\n',
             context.instructions(), assemble(context, role=name, compact=True), '\n', TRACKER_RULE, EXECUTION_RULE]
    for label, path in contract_sources(context, name).items():
        if path.is_file():
            parts.append(f'\n===== {label}: copia íntegra de {path.as_posix()} (sha256 {digests[label]}). '
                         'Usa esta copia; no releas el original. =====\n'
                         f'{path.read_text(encoding="utf-8-sig")}\n===== FIN {label} =====\n')
        else:
            parts.append(f'\n{label}: no disponible en {path.as_posix()}; solicita revisión humana antes de actuar.\n')
    parts.append('\nEspera un handoff.\n')
    return ''.join(parts)


def write_contract(context, name):
    """Write or refresh the contract when its sources changed; atomic, never partial."""
    path = contract_path(context, name)
    text = agent_contract(context, name)
    if path.is_file() and path.read_text(encoding='utf-8') == text:
        return path
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = path.with_name(f'.{name}-{uuid.uuid4().hex}.tmp')
    temporary.write_text(text, encoding='utf-8')
    temporary.replace(path)
    return path


def interactive_command(config, provider, selection, name):
    """Native launch command; references the contract file written by write_contract (no writes here)."""
    context = config.context
    if context is None:
        return provider.interactive(selection, config.root, config.root / name / 'AGENTS.md')
    profile = context.engine_root / name / 'AGENTS.md'
    contract = contract_path(context, name)
    command = provider.interactive(selection, context.workspace_root, profile)
    args = list(command.argv)
    if '--cd' in args:
        args[args.index('--cd') + 1] = str(context.workspace_root)
    # Every argument stays single-line. No reliance on Herdr server env.
    # The tracker is never presented as a queue: a relaunched agent must not pick up handoffs by itself (H11).
    waiting = ('Espera una tarea [BMAD ...] del watcher en esta terminal; no ejecutes handoffs leídos en el tracker '
               f'({context.tracker_path}).')
    instruction = (f'Lee y sigue íntegramente tu contrato {contract.as_posix()}: incluye tu perfil '
                   f'({profile.as_posix()}) y la política global; no leas esos originales del motor. {waiting}')
    if provider.identifier == 'codex':
        args[-1] = instruction
    elif provider.identifier == 'claude':
        # The contract (with profile and policy) becomes part of the system prompt: nothing to read at startup.
        args[args.index('--append-system-prompt-file') + 1] = str(contract)
        args.append(f'Tu perfil ({profile.as_posix()}) y la política global ya están íntegros en tu contrato; '
                    f'no releas esos archivos. {waiting}')
    else:
        args.append(instruction)
    return replace(command, argv=tuple(args), cwd=context.workspace_root, env=context.environment())


PROBE_MARKER = 'BMAD-VERIFICACION'


def probe_text(context, name, nonce):
    """Maintenance verification request; the reply proves role, project, workspace, current profile and memory state."""
    contract = contract_path(context, name).relative_to(context.workspace_root).as_posix()
    return (f'<!-- {PROBE_MARKER} op={nonce} agent={name} -->\n'
            'Verificación de mantenimiento de sesión. No es un handoff: no escribas en el tracker, no modifiques '
            'archivos ni ejecutes comandos.\n'
            f'1. Lee íntegramente tu contrato vigente {contract} y adopta sus instrucciones; reemplazan cualquier '
            'versión anterior que tengas.\n'
            '2. Responde con una única línea exacta, sin Markdown, comillas ni texto adicional:\n'
            f'{PROBE_MARKER} op={nonce} rol=<valor rol= de la primera línea del contrato> proyecto=<PROJECT_ID> '
            'workspace=<WORKSPACE_ROOT> fuentes=<valor fuentes= de la primera línea del contrato> '
            'memoria=<identificador [BMAD ...] de la última tarea recibida antes de esta verificación, o NINGUNA>\n')


def _flat(text):
    # Raw pane output keeps terminal colour sequences; they are not part of the reply.
    return re.sub(r'[\s`*"]+', '', re.sub(r'\x1b\[[0-9;?]*[A-Za-z]', '', text or ''))


def probe_verdict(output, *, nonce, role, project_id, workspace, digests):
    """('verified'|'absent'|'incomplete'|'mismatch', details) for the last reply carrying this nonce."""
    flat = _flat(output)
    marker = f'{PROBE_MARKER}op={nonce}'
    at = flat.rfind(marker)
    if at < 0:
        return 'absent', {}
    segment = flat[at + len(marker):at + len(marker) + 4000]
    match = re.match(r'rol=(.*?)proyecto=(.*?)workspace=(.*?)fuentes=(.*?)memoria=(.*)', segment)
    if not match:
        return 'incomplete', {}
    rol, proyecto, observed_workspace, fuentes, memoria = match.groups()
    path = lambda value: _flat(str(value)).replace('\\', '/').rstrip('/').casefold()
    problems = [name for name, ok in (
        ('role', rol == role), ('project', proyecto == project_id),
        ('workspace', path(observed_workspace) == path(workspace)),
        ('profile_sources', set(re.findall(r'[0-9a-f]{16}|ausente', fuentes)) == set(digests)),
        ('context_not_reset', memoria.upper().startswith('NINGUNA'))) if not ok]
    details = {'role': _clip(rol), 'project': _clip(proyecto), 'workspace': _clip(observed_workspace),
               'sources': _clip(fuentes), 'memory': _clip(memoria[:40]), 'problems': problems}
    return ('mismatch' if problems else 'verified'), details


def clear_supported(provider):
    """/clear keeps the role only where the contract is the system prompt: verified for Claude Code alone."""
    return provider.identifier == 'claude' and provider.capabilities.clear_context


def task_message(message, relative, event_id):
    """Minimal single-line terminal message; the complete handoff lives in the task file.

    Codex drops the submit Enter after longer pastes (agent_prompt_stalled), so only the
    handoff token, the event and the workspace-relative task path travel through the terminal.
    """
    words = message.split()
    token = words[0] if words and re.fullmatch(r'@[A-Z][A-Z-]*:', words[0]) else ''
    return ' '.join(part for part in (f'[BMAD {event_id[:12]}]', token, f'Lee y ejecuta íntegramente {relative}') if part)


class SpecKitExecutor:
    def __init__(self, config, factory, runner, state, guard=None):
        self.config, self.factory, self.runner, self.state = config, factory, runner, state
        self.guard = guard

    def prepare(self, operation, arguments='', directive=None, env=None):
        selection, provider = self.factory.resolve(operation=operation)
        if not provider.capabilities.headless or not provider.capabilities.skills:
            raise UnsupportedCapability(f'{selection.provider}: Spec Kit headless is pending verification.')
        context = self.config.context
        shared_root = context.engine_root if context else self.config.root
        skill = provider.skill(shared_root, operation)
        if directive:
            directive = (self.config.root / directive).resolve()
            if not (directive.is_relative_to(self.config.root) or directive.is_relative_to(shared_root)):
                raise ConfigurationError('Directive must belong to this project.')
        prompt = skill + (' ' + arguments if arguments else '')
        environment = dict(env or {})
        if context and not context.legacy:
            if set(environment) - {'SPECIFY_FEATURE_DIRECTORY'}:
                raise ConfigurationError('Only SPECIFY_FEATURE_DIRECTORY may override the project environment.')
            context.validate()
            from .context import read_json
            feature_state = context.output('.specify/feature.json')
            if feature_state.exists():
                stored = read_json(feature_state).get('feature_directory', '')
                if not stored or not context.output(stored).is_relative_to(context.specs_dir):
                    raise ConfigurationError('Stored feature directory must remain inside workspace/specs.')
            feature = environment.get('SPECIFY_FEATURE_DIRECTORY')
            if feature:
                if not context.output(feature).is_relative_to(context.specs_dir):
                    raise ConfigurationError('Feature directory must remain inside workspace/specs.')
            # Do not rely on provider slash-command discovery from a different cwd.
            folder = '.agents' if provider.identifier == 'codex' else '.claude'
            resource = shared_root / folder / 'skills' / f'speckit-{operation}' / 'SKILL.md'
            prompt = context.instructions() + f'\nLee y ejecuta íntegramente la skill compartida {resource.as_posix()}.\nArgumentos: {arguments}'
            environment.update(context.environment())
        if context:
            prompt = assemble(context, operation=operation) + prompt
        command = provider.headless(selection, self.config.root, prompt, directive, environment)
        if self.structured(provider):
            command = provider.structured_headless(command)
        return selection, provider, command

    def structured(self, provider):
        """Usage capture is opt-in (guard.headless_usage) and only where the CLI documents a structured result."""
        return bool((self.config.data.get('guard') or {}).get('headless_usage')) and \
            hasattr(provider, 'structured_headless') and bool(getattr(provider, 'headless_usage', None))

    def execute(self, operation, arguments='', directive=None, env=None):
        with project_lock(self.config.context or self.config.root, 'speckit'):
            return self._execute(operation, arguments, directive, env)

    def _execute(self, operation, arguments='', directive=None, env=None):
        selection, provider, command = self.prepare(operation, arguments, directive, env)
        provider.verify(self.runner, self.config.root, headless=True)
        key = 'run:' + str(uuid.uuid4())
        self.state.claim(key, {'agent_id': 'speckit.' + operation, 'provider': selection.provider,
                               'model': selection.model, 'pane_id': None, 'phase': OPERATIONS[operation]})
        timeout = self.config.operation_timeout(operation)
        try:
            result = self.runner.run(command, timeout=timeout)
            usage = None
            if self.structured(provider):
                # Callers keep reading the text answer; unparseable output stays raw and usage unavailable.
                result, usage = provider.read_headless_usage(result)
            status = provider.classify(result)
            # Text output exposes no usage data: record it as unavailable, never estimated.
            record = {'cost_usd': 'no_disponible', 'turns': 'no_disponible'}
            if usage:
                record = {'usage': usage, 'cost_usd': usage['cost_usd']['value'], 'turns': usage['turns']['value']}
            self.state.put(key, {**self.state.get(key), 'returncode': result.returncode, 'error': result.error,
                                 'duration_ms': result.duration_ms, 'timeout_s': timeout, **record})
            self.state.finish(key, 'done' if status == 'success' else status)
            if self.guard:
                self.guard.on_headless(operation, key, status)
            if status != 'success' and result.returncode == 0:
                return Result(1, result.stdout, result.stderr, status, result.duration_ms)
            return result
        except BaseException:
            self.state.finish(key, 'uncertain')
            if self.guard:
                self.guard.on_headless(operation, key, 'uncertain')
            raise


class AgentDispatcher:
    def __init__(self, config, factory, gateway, state):
        self.config, self.factory, self.gateway, self.state = config, factory, gateway, state

    def info(self, name):
        owned = self.state.get('agent:' + name)
        if not owned or owned['state'] != 'ready':
            return None, None
        identity = owned.get('session_name') or (self.config.context.session_name(name) if self.config.context else name)
        for agent in self.gateway.list_agents():
            if agent.get('name') == identity and agent.get('pane_id') == owned['pane_id']:
                return agent['pane_id'], agent.get('agent_status', 'unknown')
        return None, None

    def provider(self, name):
        selection, provider = self.factory.resolve(agent=name)
        owned = self.state.get('agent:' + name)
        if not owned or (owned['provider'], owned['model']) != (selection.provider, selection.model):
            raise ReconciliationRequired(f'{name}: no matching owned session; launch/reconcile before dispatch.')
        return selection, provider

    def blocker(self, provider, pane):
        """Dialog on the agent's current screen that only a human may answer (e.g. 'trust_dialog')."""
        detect = getattr(provider, 'interaction_blocker', None)
        if detect is None:
            return None
        screen = self.gateway.read(pane, 60, source='visible')
        return detect(screen) if isinstance(screen, str) else None

    def dispatch(self, name, pane, message, event_id):
        selection, provider = self.provider(name)
        actual, status = self.info(name)
        if actual != pane or status not in {'idle', 'done'}:
            raise ReconciliationRequired(f'{name}: target is not an owned idle agent.')
        blocker = self.blocker(provider, pane)
        if blocker:
            # Herdr reports this agent idle, but an Enter would answer the dialog: nothing is sent.
            self.state.put('agent:' + name, {**self.state.get('agent:' + name), 'state': 'awaiting_trust',
                                              'blocker': blocker})
            raise AgentBlocked(f'{name}: {blocker} on screen; answer it manually in pane {pane}, then run '
                               f'python -m bmad_runtime.maintenance --reconcile {name} --confirm.')
        key = 'dispatch:' + event_id
        if not self.state.claim(key, {'agent_id': name, 'provider': selection.provider,
                                     'model': selection.model, 'pane_id': pane, 'phase': AGENT_PHASES[name]}):
            return False
        context = self.config.context
        try:
            if context:
                # Refresh the contract if profile/policy changed; running agents compare the source digests.
                contract = write_contract(context, name).relative_to(context.workspace_root).as_posix()
                digests = ','.join(f'{k}:{v}' for k, v in source_digests(context, name).items())
                reference = (f'CONTRATO VIGENTE: {contract} (fuentes {digests}). Si no coincide con las fuentes de '
                             'tu contrato inicial, reléelo antes de actuar.\n')
                # The global policy travels once, inside the contract; the task references it (Phase 4C).
                # Workspace paths, local constitution, observations and tracker rule stay in every task.
                path = self._write_task(name, event_id, self.state.get(key).get('attempt', 1),
                                        context.instructions() + assemble(context, role=name, policy_in_contract=contract)
                                        + TRACKER_RULE + reference + message)
                text = task_message(message, path.relative_to(context.workspace_root).as_posix(), event_id)
            else:
                text = message
        except BaseException:
            # Nothing was sent to the agent.
            self.state.finish(key, 'not_delivered')
            raise
        try:
            self.gateway.prompt(pane, text)
        except DeliveryRejected:
            self.state.finish(key, 'not_delivered')
            raise
        except BaseException:
            # The text may have reached the agent: never retried automatically.
            self.state.finish(key, 'uncertain')
            raise
        self.state.put(key, {**self.state.get(key), 'delivery': 'accepted'})
        self.state.finish(key, 'done')
        return True

    def _write_task(self, name, event_id, attempt, text):
        """One exclusive file per delivery attempt: pending tasks are never overwritten."""
        context = self.config.context
        path = context.handoffs_dir / 'tasks' / f'{event_id[:24]}-{attempt}.md'
        content = f'<!-- BMAD-TAREA event_id={event_id} agent={name} attempt={attempt} -->\n{text}\n'
        path.parent.mkdir(parents=True, exist_ok=True)
        try:
            with path.open('x', encoding='utf-8', newline='\n') as handle:
                handle.write(content)
        except FileExistsError:
            if path.read_text(encoding='utf-8') != content:
                raise ReconciliationRequired(f'Task file {path.name} already exists with different content; it is never overwritten.')
        key = 'dispatch:' + event_id
        self.state.put(key, {**self.state.get(key), 'task_file': path.relative_to(context.workspace_root).as_posix(),
                             'task_sha256': hashlib.sha256(content.encode('utf-8')).hexdigest()})
        return path


# Session lifecycle diagnostics. Reasons in WAIT_REASONS clear by themselves; any other one needs a human.
SESSION_ACTIONS = ('CLEAR', 'ROTATE', 'SKIP', 'MANUAL_REVIEW')
WAIT_REASONS = ('herdr_busy', 'followup_active', 'pending_tasks', 'unconfirmed_tasks', 'headless_active',
                'tracker_changing', 'tracker_unprocessed_lines', 'last_handoff_unconfirmed', 'no_handoff',
                'session_already_fresh')
UNCONFIRMED_STAGES = {'detectado', 'reservado', 'despachado'}
SUMMARY_REQUIRED = ('agent_id', 'project_id', 'workspace', 'task_id', 'phase', 'last_handoff', 'result',
                    'artifacts', 'completed_at', 'session_generation')
_FIELD = re.compile(r'^\s*-\s+\*\*([^*\n]+?):\*\*\s*(.*)$', re.MULTILINE)
_TEXT_LIMIT = 500
_LIST_LIMIT = 20


def _clip(text):
    text = ' '.join(str(text or '').split())
    return text if len(text) <= _TEXT_LIMIT else text[:_TEXT_LIMIT - 3] + '...'


def block_fields(block):
    """Fields of a tracker-logger block, keyed by lowercase name without leading symbols."""
    fields = {}
    for name, value in _FIELD.findall(block or ''):
        fields.setdefault(re.sub(r'^\W+', '', name).strip().lower(), value.strip())
    return fields


def _records(store, prefix):
    rows = store.db.execute('SELECT id,data FROM records WHERE id LIKE ?', (prefix + '%',))
    return [(key, json.loads(data)) for key, data in rows]


class SessionManager:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

    def _artifacts(self, value):
        context = self.dispatcher.config.context
        paths = re.findall(r'`([^`]+)`', value) or re.split(r'[,;]', value)
        artifacts = []
        for path in [p.strip() for p in paths if p.strip()][:_LIST_LIMIT]:
            try:
                exists = context.output(path).is_file()
            except ConfigurationError:
                exists = False
            artifacts.append({'path': _clip(path), 'exists': exists})
        return artifacts

    def record_summary(self, name, event_id, block):
        """Persist a bounded, evidence-only summary of a confirmed handoff before any context rotation."""
        state, context = self.dispatcher.state, self.dispatcher.config.context
        queued = state.get('queued:' + event_id) or {}
        handoff = None
        lines = read_tracker(context.tracker_path).lines
        index = queued.get('line_number')
        if isinstance(index, int) and index < len(lines) and same_line(lines[index], queued.get('line_hash')):
            handoff = lines[index][queued['start']:queued['end']]
        fields = block_fields(block)
        agent = state.get('agent:' + name) or {}
        open_issues = fields.get('puntos abiertos', '')
        decisions = [_clip(value) for key, value in fields.items() if key.startswith('decisi')]
        block = (block or '').strip()
        summary = {
            'agent_id': name, 'provider': agent.get('provider'), 'project_id': context.project_id,
            'workspace': str(context.workspace_root), 'task_id': event_id, 'phase': AGENT_PHASES.get(name),
            'state': queued.get('stage'), 'last_handoff': _clip(handoff) if handoff else None,
            'result': _clip(fields.get('estado')) or None, 'next_handoff': _clip(fields.get('handoff')) or None,
            'artifacts': self._artifacts(fields.get('artefacto generado', '')),
            # Only what the agent recorded; nothing is inferred.
            'decisions': decisions, 'decisions_source': 'tracker_block' if decisions else 'no_registrado',
            'open_issues': [] if open_issues.strip(' .').lower() in {'', 'ninguno', 'ninguna'} else [_clip(open_issues)],
            'completed_at': datetime.now().astimezone().isoformat(timespec='seconds'),
            'session_generation': ({'run_id': agent['run_id'], 'attempt': agent.get('attempt'),
                                    **({'generation': agent['generation']} if 'generation' in agent else {})}
                                   if agent.get('run_id') else None),
            'source': _clip(block.splitlines()[0]) if block else None,
        }
        state.put('session:' + name, summary)
        return summary

    @staticmethod
    def summary_status(summary, event_id, context):
        if not summary:
            return 'missing', ['summary_missing']
        if summary.get('task_id') != event_id:
            return 'stale', ['summary_stale']
        if (summary.get('project_id'), summary.get('workspace')) != (context.project_id, str(context.workspace_root)):
            return 'incomplete', ['summary_workspace_mismatch']
        missing = [key for key in SUMMARY_REQUIRED if not summary.get(key)]
        # Artifacts are the durable memory: they must still exist when a rotation is considered.
        for item in summary.get('artifacts') or []:
            try:
                present = context.output(item.get('path', '')).is_file()
            except ConfigurationError:
                present = False
            if not present:
                missing.append('artifacts_exist')
                break
        return ('incomplete', ['summary_incomplete:' + ','.join(missing)]) if missing else ('complete', [])

    def _workspace_reasons(self, store):
        reasons = []
        problem = tracker_verified(self.dispatcher.config.context, store)
        if problem:
            reasons.append(problem)
        runs = [data for _, data in _records(store, 'run:')]
        if any(run.get('state') == 'in_flight' for run in runs):
            reasons.append('headless_active')
        if any(run.get('state') == 'uncertain' for run in runs):
            reasons.append('headless_uncertain')
        for key, data in _records(store, 'queued:') + _records(store, 'dispatch:'):
            if data.get('acknowledged'):
                continue
            if data.get('state') != 'done':
                # not_delivered: nothing reached the agent; the queued handoff is still pending.
                pending = data.get('state') == 'not_delivered' or (key.startswith('queued:') and data.get('state') == 'queued')
                reasons.append('pending_tasks' if pending else 'uncertain_dispatch')
            elif data.get('stage') in UNCONFIRMED_STAGES:
                reasons.append('unconfirmed_tasks')
            elif data.get('stage') in {'fallido', 'requiere_intervencion'}:
                reasons.append('handoff_' + data['stage'])
        # An interrupted or uncertain maintenance blocks every new intervention until reconciled.
        reasons += ['maintenance_pending:' + agent for agent in maintenance_blocks(store)]
        if protocol_violations(store):
            reasons.append('protocol_violation')
        return sorted(set(reasons))

    def _agent_row(self, name, store, herdr_agents, workspace_reasons):
        dispatcher = self.dispatcher
        context = dispatcher.config.context
        selection, provider = dispatcher.factory.resolve(agent=name)
        reasons = list(workspace_reasons)
        owned = store.get('agent:' + name)
        identity = (owned or {}).get('session_name') or context.session_name(name)
        status = None
        if not owned or owned.get('state') != 'ready':
            reasons.append('not_owned_or_not_ready')
            if owned and owned.get('state') == 'awaiting_trust':
                reasons.append('awaiting_trust')
        if herdr_agents is None:
            reasons.append('herdr_unavailable')
        elif owned:
            entry = next((agent for agent in herdr_agents if agent.get('name') == identity), None)
            if entry is None:
                reasons.append('herdr_agent_absent')
            elif entry.get('pane_id') != owned.get('pane_id'):
                reasons.append('herdr_identity_mismatch')
            else:
                status = entry.get('agent_status')
                if status in {'working', 'blocked'}:
                    reasons.append('herdr_busy:' + status)
                elif status not in {'idle', 'done'}:
                    reasons.append('herdr_status_unknown')
        if name in (store.get('followup') or {}):
            reasons.append('followup_active')
        # Tracker order: line number first, detection time as tie-breaker.
        handoffs = sorted(((data.get('line_number', -1), data.get('stages', {}).get('detectado', 0)),
                           key[len('queued:'):], data)
                          for key, data in _records(store, 'queued:') if data.get('agent_id') == name)
        last_confirmed, summary_state = None, 'not_required'
        if not handoffs:
            reasons.append('no_handoff')
        else:
            _, event_id, last = handoffs[-1]
            if 'stage' not in last:
                reasons.append('last_handoff_untracked')
            elif last['stage'] in UNCONFIRMED_STAGES:
                reasons.append('last_handoff_unconfirmed:' + last['stage'])
            elif last['stage'] != 'confirmado':
                reasons.append('last_handoff_' + last['stage'])
            summary = store.get('session:' + name)
            if last.get('stage') == 'confirmado':
                summary_state, problems = self.summary_status(summary, event_id, context)
                reasons += problems
            else:
                summary_state = 'pending_confirmation'
            confirmed = [(key, data) for _, key, data in handoffs if data.get('stage') == 'confirmado']
            if confirmed:
                key, data = confirmed[-1]
                stamp = data['stages'].get('confirmado')
                last_confirmed = {'task_id': key,
                                  'confirmed_at': datetime.fromtimestamp(stamp).astimezone().isoformat(timespec='seconds') if stamp else None,
                                  'handoff': summary.get('last_handoff') if summary and summary.get('task_id') == key else None}
                # Idempotence: a session refreshed after its last confirmed handoff has nothing to release.
                refreshed = [op['states'].get('COMPLETED', 0) for op in maintenance_records(store)
                             if op.get('agent') == name and op.get('state') == 'COMPLETED'
                             and op.get('kind') in ('CLEAR', 'ROTATE')]   # VERIFY keeps the context
                if stamp and refreshed and max(refreshed) >= stamp:
                    reasons.append('session_already_fresh')
        eligible = not reasons
        if eligible:
            action = 'CLEAR' if clear_supported(provider) else 'ROTATE'
        elif all(reason.split(':')[0] in WAIT_REASONS for reason in reasons):
            action = 'SKIP'
        else:
            action = 'MANUAL_REVIEW'
        return {'agent': name, 'provider': selection.provider, 'model': selection.model,
                'project_id': context.project_id, 'workspace': str(context.workspace_root), 'session_name': identity,
                'pane_id': (owned or {}).get('pane_id'), 'generation': (owned or {}).get('generation', 1),
                'herdr_status': status, 'eligibility': 'ELIGIBLE' if eligible else 'NOT_ELIGIBLE',
                'reasons': reasons or ['all_checks_passed'], 'last_confirmed_task': last_confirmed,
                'summary': summary_state, 'clear_context_verified': clear_supported(provider),
                'proposed_action': action}

    def plan(self, store, names=None):
        """Read-only eligibility report. Never prompts, clears, closes or relaunches a session.

        Clearing or rotating is operator-driven only (python -m bmad_runtime.maintenance --clear/--rotate).
        """
        try:
            herdr_agents = self.dispatcher.gateway.list_agents()
        except (BMADRuntimeError, OSError):
            herdr_agents = None
        workspace_reasons = self._workspace_reasons(store)
        names = names or [name for name in AGENT_PHASES if store.get('agent:' + name)]
        return [self._agent_row(name, store, herdr_agents, workspace_reasons) for name in names]
