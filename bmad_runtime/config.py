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

    @classmethod
    def load(cls, root, path=None, context=None):
        root = Path(root).resolve()
        try:
            raw = effective_config(context, path) if context else read_json(absolute_path(path, root) if path else root / 'config_bmad.json')
        except (OSError, ValueError) as exc:
            raise ConfigurationError('Cannot read config_bmad.json.') from exc
        _object(raw, 'configuration')
        ai = _object(raw.get('ai', {}), 'ai')
        if set(ai) - {'schema_version', 'defaults', 'providers', 'phases', 'agents', 'speckit', 'limits', 'git'}:
            raise ConfigurationError('Unknown ai configuration field.')
        if type(ai.get('schema_version', 1)) is not int or ai.get('schema_version', 1) != 1:
            raise ConfigurationError('Only schema_version=1 is supported.')
        data = {'schema_version': 1, 'defaults': {'provider': 'claude', 'model': None},
                'providers': {'claude': {'executable': 'claude'}, 'codex': {'executable': 'codex'},
                              'gemini': {'executable': 'gemini'}},
                'phases': {}, 'agents': {}, 'speckit': {},
                'limits': {'command_timeout': 120, 'headless_timeout': 1800,
                           'max_output_bytes': 1_048_576, 'max_processes': 1},
                'git': {'auto_commit': False}}
        for key, value in ai.items():
            if key in {'defaults', 'providers', 'limits', 'git'}:
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
        if set(limits) != {'command_timeout', 'headless_timeout', 'max_output_bytes', 'max_processes'}:
            raise ConfigurationError('Unknown resource limit.')
        for name, value in limits.items():
            if type(value) is not int or value < 1:
                raise ConfigurationError(f'{name} must be a positive integer.')
        if limits['max_processes'] > 8 or limits['headless_timeout'] > 86400 or limits['command_timeout'] > 600 or limits['max_output_bytes'] > 16_777_216:
            raise ConfigurationError('Resource limit exceeds the supported bound.')
        if set(data['git']) != {'auto_commit'} or type(data['git']['auto_commit']) is not bool:
            raise ConfigurationError('git accepts only auto_commit (boolean).')
        return cls(root, data, context, raw)

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
