"""One source of truth: optional `ai` section in config_bmad.json."""
from dataclasses import dataclass, field
import json
from pathlib import Path
import re

from .errors import ConfigurationError
from .context import read_json, absolute_path
import copy
import uuid


def materialize_config(context, raw):
    """Disposable project-local compatibility view; never edits engine defaults."""
    if context.legacy:
        return
    data = copy.deepcopy(raw)
    data.update(project_id=context.project_id, tracker=str(context.tracker_path),
                context=str(context.output('.specify/memory/constitution.md')),
                routes_bmad={role: str(context.output('docs/' + role)) for role in AGENT_PHASES})
    path = context.output('state/config_bmad.json')
    path.parent.mkdir(parents=True, exist_ok=True)
    temporary = context.output(f'state/config-{uuid.uuid4().hex}.tmp')
    with temporary.open('x', encoding='utf-8') as handle:
        json.dump(data, handle, ensure_ascii=False, indent=2)
    temporary.replace(path)


def merge_config(base, override):
    """Merge sparse project overrides; provider changes discard native model/options."""
    result = copy.deepcopy(base)
    if 'provider' in override and override['provider'] != base.get('provider', override['provider']):
        result.pop('model', None)
        result.pop('options', None)
    for key, value in override.items():
        if key != 'options' and isinstance(value, dict) and isinstance(result.get(key), dict):
            result[key] = merge_config(result[key], value)
        else:
            result[key] = copy.deepcopy(value)
    return result


def effective_config(context, path=None):
    source = absolute_path(path, context.engine_root) if path else context.engine_root / 'config_bmad.json'
    raw = read_json(source)
    if context.legacy:
        return raw
    override = read_json(context.output('project.json')).get('config', {})
    if not isinstance(override, dict) or set(override) - {'ai', 'project_name', 'project_type', 'ux_phase', 'code_dirs'}:
        raise ConfigurationError('Project overrides accept only ai, project_name, project_type, ux_phase and code_dirs.')
    ai = override.get('ai', {})
    if not isinstance(ai, dict) or set(ai) - {'defaults', 'phases', 'agents', 'speckit'}:
        raise ConfigurationError('Project ai overrides accept only defaults, phases, agents and speckit.')
    result = merge_config(raw, override)
    result['project_name'] = override.get('project_name', context.project_id)
    for key in ('tracker', 'context', 'routes_bmad', 'projects'):
        result.pop(key, None)
    # Application layout is project-owned and is never inherited from the engine.
    result['code_dirs'] = override.get('code_dirs', {})
    code_dirs = result['code_dirs']
    if not isinstance(code_dirs, dict) or set(code_dirs) - {'backend', 'frontend'}:
        raise ConfigurationError('Invalid code_dirs.')
    for value in code_dirs.values():
        if not isinstance(value, str) or not value or value == '/':
            raise ConfigurationError('code_dirs must name a source directory inside the workspace.')
        target = context.output(value)
        parts = target.relative_to(context.workspace_root).parts
        first = parts[0] if parts else ''
        if first in {'docs', 'specs', 'handoffs', 'state', 'logs', 'temp'} or first.startswith('.'):
            raise ConfigurationError('code_dirs cannot overlap operational or documentation directories.')
    return result

OPERATIONS = {'specify': 'M', 'clarify': 'M', 'plan': 'A', 'tasks': 'A',
              'analyze': 'A', 'converge': 'D', 'implement': 'D'}
AGENT_PHASES = {
    'business-storyteller': 'B', 'product-analyst': 'B', 'product-manager': 'M',
    'business-analyst': 'M', 'qa-documental': 'M', 'designer-ux': 'A',
    'solutions-architect': 'A', 'data-architect': 'A', 'api-architect': 'A',
    'qa-tech': 'A', 'dev-backend': 'D', 'dev-frontend': 'D', 'qa-auto': 'D',
    'code-review': 'D', 'devops': 'D',
}


# Context budget and loop guard (guard.py). Starts in observation: alerts only, no dispatch is held.
# Usage limits (tokens, cost) stay null unless the provider reports that metric (Guard checks it).
GUARD_MODES = ('off', 'observe', 'enforce')
GUARD_LEVELS = ('warning', 'pause', 'intervention')
GUARD_BUDGET = {'max_operation_seconds': 3600, 'max_attempts': 2, 'max_consecutive_operations': 8,
                'max_operations_per_session': 15, 'max_input_tokens': None, 'max_output_tokens': None,
                'max_cost_usd': None}
GUARD_LOOP = {'repeated_instruction': {'warning': 2, 'pause': 3, 'intervention': 4},
              'handoff_cycle': {'warning': 3, 'pause': 4, 'intervention': 5},
              'repeated_error': {'warning': 2, 'pause': 3, 'intervention': 5},
              'no_progress': {'warning': 2, 'pause': 3, 'intervention': 4},
              'repeated_clarification': {'warning': 2, 'pause': 3, 'intervention': 4}}


def _budget(value, name):
    _object(value, name)
    if set(value) - set(GUARD_BUDGET):
        raise ConfigurationError(f'Unknown {name} fields: {set(value) - set(GUARD_BUDGET)}')
    for key, item in value.items():
        if key == 'max_cost_usd':
            if item is not None and (type(item) not in {int, float} or not 0 < item <= 10_000):
                raise ConfigurationError(f'{name}.{key} must be null or a positive amount up to 10000.')
        elif key.endswith('_tokens'):
            if item is not None and (type(item) is not int or not 1 <= item <= 100_000_000):
                raise ConfigurationError(f'{name}.{key} must be null or a positive integer.')
        elif type(item) is not int or not 1 <= item <= (86400 if key == 'max_operation_seconds' else 1000):
            raise ConfigurationError(f'{name}.{key} must be a positive integer within its bound.')
    return dict(value)


def _guard(value, providers):
    _object(value, 'guard')
    if set(value) - {'mode', 'window_seconds', 'retention_days', 'budget', 'providers', 'agents', 'loop',
                     'headless_usage'}:
        raise ConfigurationError('Unknown guard field.')
    # headless_usage: Spec Kit runs ask the CLI for its documented structured result (usage, turns, cost).
    # Opt-in: it changes the headless output format; the text answer is extracted back from it.
    result = {'mode': value.get('mode', 'observe'), 'window_seconds': value.get('window_seconds', 21600),
              'retention_days': value.get('retention_days', 14), 'headless_usage': value.get('headless_usage', False),
              'budget': {**GUARD_BUDGET, **_budget(value.get('budget', {}), 'guard.budget')},
              'providers': {}, 'agents': {}, 'loop': copy.deepcopy(GUARD_LOOP)}
    if result['mode'] not in GUARD_MODES:
        raise ConfigurationError('guard.mode must be off, observe or enforce.')
    if type(result['headless_usage']) is not bool:
        raise ConfigurationError('guard.headless_usage must be true or false.')
    for key, top in (('window_seconds', 7 * 86400), ('retention_days', 365)):
        if type(result[key]) is not int or not 1 <= result[key] <= top:
            raise ConfigurationError(f'guard.{key} must be an integer between 1 and {top}.')
    for section, allowed in (('providers', set(providers)), ('agents', set(AGENT_PHASES))):
        entries = _object(value.get(section, {}), f'guard.{section}')
        if set(entries) - allowed:
            raise ConfigurationError(f'Unknown guard.{section} identifiers: {set(entries) - allowed}')
        result[section] = {name: _budget(item, f'guard.{section}.{name}') for name, item in entries.items()}
    loop = _object(value.get('loop', {}), 'guard.loop')
    if set(loop) - set(GUARD_LOOP):
        raise ConfigurationError(f'Unknown guard.loop rules: {set(loop) - set(GUARD_LOOP)}')
    for rule, levels in loop.items():
        if set(_object(levels, f'guard.loop.{rule}')) - set(GUARD_LEVELS):
            raise ConfigurationError(f'guard.loop.{rule} accepts only warning, pause and intervention.')
        merged = {**result['loop'][rule], **levels}
        if any(type(merged[level]) is not int or not 1 <= merged[level] <= 1000 for level in GUARD_LEVELS) or \
                not merged['warning'] <= merged['pause'] <= merged['intervention']:
            raise ConfigurationError(f'guard.loop.{rule} needs integers with warning <= pause <= intervention.')
        result['loop'][rule] = merged
    return result


@dataclass(frozen=True)
class Selection:
    provider: str
    model: str | None = None
    options: dict = field(default_factory=dict)


def _object(value, name):
    if not isinstance(value, dict):
        raise ConfigurationError(f'{name} must be an object.')
    return value


def _selection(value):
    _object(value, 'selection')
    if set(value) - {'provider', 'model', 'options'}:
        raise ConfigurationError('Unknown selection options; native flags are not accepted.')
    if 'provider' in value and (not isinstance(value['provider'], str) or not re.fullmatch(r'[a-z][a-z0-9_-]*', value['provider'])):
        raise ConfigurationError('Invalid provider identifier.')
    model = value.get('model')
    if model is not None and (not isinstance(model, str) or not re.fullmatch(r'[A-Za-z0-9][A-Za-z0-9._:/-]{0,199}', model)):
        raise ConfigurationError('Invalid model identifier; use null for CLI default.')
    _object(value.get('options', {}), 'options')


@dataclass
class RuntimeConfig:
    root: Path
    data: dict
    context: object = None
    raw: dict = field(default_factory=dict)
    source: Path | None = None

    @classmethod
    def load(cls, root, path=None, context=None):
        root = Path(root).resolve()
        try:
            raw = effective_config(context, path) if context else read_json(absolute_path(path, root) if path else root / 'config_bmad.json')
        except (OSError, ValueError) as exc:
            raise ConfigurationError('Cannot read config_bmad.json.') from exc
        _object(raw, 'configuration')
        ai = _object(raw.get('ai', {}), 'ai')
        if set(ai) - {'schema_version', 'defaults', 'providers', 'phases', 'agents', 'speckit', 'limits', 'git', 'tracker',
                      'guard'}:
            raise ConfigurationError('Unknown ai configuration field.')
        if type(ai.get('schema_version', 1)) is not int or ai.get('schema_version', 1) != 1:
            raise ConfigurationError('Only schema_version=1 is supported.')
        data = {'schema_version': 1, 'defaults': {'provider': 'claude', 'model': None},
                'providers': {'claude': {'executable': 'claude'}, 'codex': {'executable': 'codex'},
                              'gemini': {'executable': 'gemini'}},
                'phases': {}, 'agents': {}, 'speckit': {},
                'limits': {'command_timeout': 120, 'headless_timeout': 1800,
                           'max_output_bytes': 1_048_576, 'max_processes': 1,
                           'operation_timeouts': {}},
                'git': {'auto_commit': False},
                # Watcher reading policy: wait for unterminated lines and tolerate transient rewrites.
                'tracker': {'settle_seconds': 4, 'rewrite_grace_seconds': 10}}
        for key, value in ai.items():
            if key in {'defaults', 'providers', 'limits', 'git', 'tracker'}:
                data[key].update(_object(value, key))
            else:
                data[key] = value
        _selection(data['defaults'])
        for section, allowed in [('phases', {'B', 'M', 'A', 'D'}), ('agents', set(AGENT_PHASES)), ('speckit', set(OPERATIONS))]:
            entries = _object(data[section], section)
            if set(entries) - allowed:
                raise ConfigurationError(f'Unknown {section} identifiers: {set(entries) - allowed}')
            for value in entries.values():
                _selection(value)
        for name, settings in data['providers'].items():
            _selection({'provider': name})
            _object(settings, 'provider')
            if set(settings) - {'executable'} or not isinstance(settings.get('executable'), str) or not settings['executable'].strip() or '\0' in settings['executable']:
                raise ConfigurationError('Provider settings accept only an executable path, without arguments.')
            if '/' in settings['executable'] or '\\' in settings['executable']:
                settings['executable'] = str(absolute_path(settings['executable'], context.engine_root if context else root))
        limits = data['limits']
        if set(limits) != {'command_timeout', 'headless_timeout', 'max_output_bytes', 'max_processes', 'operation_timeouts'}:
            raise ConfigurationError('Unknown resource limit.')
        # Optional per-operation headless timeouts; missing operations keep headless_timeout.
        operation_timeouts = _object(limits['operation_timeouts'], 'operation_timeouts')
        if set(operation_timeouts) - set(OPERATIONS):
            raise ConfigurationError(f'Unknown operation_timeouts identifiers: {set(operation_timeouts) - set(OPERATIONS)}')
        for name, value in operation_timeouts.items():
            if type(value) is not int or not 1 <= value <= 86400:
                raise ConfigurationError(f'operation_timeouts.{name} must be an integer between 1 and 86400.')
        for name, value in limits.items():
            if name != 'operation_timeouts' and (type(value) is not int or value < 1):
                raise ConfigurationError(f'{name} must be a positive integer.')
        if limits['max_processes'] > 8 or limits['headless_timeout'] > 86400 or limits['command_timeout'] > 600 or limits['max_output_bytes'] > 16_777_216:
            raise ConfigurationError('Resource limit exceeds the supported bound.')
        if set(data['git']) != {'auto_commit'} or type(data['git']['auto_commit']) is not bool:
            raise ConfigurationError('git accepts only auto_commit (boolean).')
        if set(data['tracker']) != {'settle_seconds', 'rewrite_grace_seconds'}:
            raise ConfigurationError('tracker accepts only settle_seconds and rewrite_grace_seconds.')
        for name, value in data['tracker'].items():
            if type(value) is not int or not 0 <= value <= 3600:
                raise ConfigurationError(f'tracker.{name} must be an integer between 0 and 3600.')
        data['guard'] = _guard(ai.get('guard', {}), data['providers'])
        # Explicit --config file (absolute); None means the engine default config_bmad.json.
        source = absolute_path(path, context.engine_root if context else root) if path else None
        return cls(root, data, context, raw, source)

    def operation_timeout(self, operation):
        limits = self.data['limits']
        return limits['operation_timeouts'].get(operation, limits['headless_timeout'])

    def resolve(self, *, agent=None, operation=None):
        if (agent is None) == (operation is None):
            raise ConfigurationError('Resolve exactly one agent or operation.')
        mapping = AGENT_PHASES if agent is not None else OPERATIONS
        name = agent if agent is not None else operation
        if name not in mapping:
            raise ConfigurationError(f'Unknown target {name}.')
        value = dict(self.data['defaults'])
        for override in (self.data['phases'].get(mapping[name], {}), self.data['agents' if agent is not None else 'speckit'].get(name, {})):
            value = merge_config(value, override)
        return Selection(value['provider'], value.get('model'), value.get('options', {}))
