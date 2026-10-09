from pathlib import Path
import uuid
from dataclasses import replace

from .commands import Result
from .config import AGENT_PHASES, OPERATIONS
from .errors import ConfigurationError, ReconciliationRequired, UnsupportedCapability
from .state import project_lock
from .technical_context import assemble


def interactive_command(config, provider, selection, name):
    context = config.context
    if context is None:
        return provider.interactive(selection, config.root, config.root / name / 'AGENTS.md')
    profile = context.engine_root / name / 'AGENTS.md'
    command = provider.interactive(selection, context.workspace_root, profile)
    args = list(command.argv)
    if '--cd' in args:
        args[args.index('--cd') + 1] = str(context.workspace_root)
    # Both supported CLIs accept an initial prompt. No reliance on Herdr server env.
    contract = context.instructions() + assemble(context, role=name, compact=True) + f'\nLee el perfil compartido {profile.as_posix()}. Espera un handoff.'
    if provider.identifier == 'codex':
        args[-1] = contract
        sensitive = command.sensitive
    elif provider.identifier == 'claude':
        index = args.index('--append-system-prompt-file')
        args[index:index + 2] = ['--append-system-prompt', contract]
        args.append('Lee el perfil indicado en el contrato y espera un handoff del tracker del proyecto.')
        sensitive = command.sensitive | {index + 1}
    else:
        args.append(contract)
        sensitive = command.sensitive | {len(args) - 1}
    return replace(command, argv=tuple(args), cwd=context.workspace_root,
                   env=context.environment(), sensitive=frozenset(sensitive))


class SpecKitExecutor:
    def __init__(self, config, factory, runner, state):
        self.config, self.factory, self.runner, self.state = config, factory, runner, state

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
        return selection, provider, command

    def execute(self, operation, arguments='', directive=None, env=None):
        with project_lock(self.config.context or self.config.root, 'speckit'):
            return self._execute(operation, arguments, directive, env)

    def _execute(self, operation, arguments='', directive=None, env=None):
        selection, provider, command = self.prepare(operation, arguments, directive, env)
        provider.verify(self.runner, self.config.root, headless=True)
        key = 'run:' + str(uuid.uuid4())
        self.state.claim(key, {'agent_id': 'speckit.' + operation, 'provider': selection.provider,
                               'model': selection.model, 'pane_id': None, 'phase': OPERATIONS[operation]})
        try:
            result = self.runner.run(command, timeout=self.config.data['limits']['headless_timeout'])
            status = provider.classify(result)
            self.state.finish(key, 'done' if status == 'success' else status)
            if status != 'success' and result.returncode == 0:
                return Result(1, result.stdout, result.stderr, status)
            return result
        except BaseException:
            self.state.finish(key, 'uncertain')
            raise


class AgentDispatcher:
    def __init__(self, config, factory, gateway, state):
        self.config, self.factory, self.gateway, self.state = config, factory, gateway, state

    def info(self, name):
        owned = self.state.get('agent:' + name)
        if not owned or owned['state'] != 'ready':
            return None, None
        for agent in self.gateway.list_agents():
            identity = self.config.context.session_name(name) if self.config.context else name
            if agent.get('name') == identity and agent.get('pane_id') == owned['pane_id']:
                return agent['pane_id'], agent.get('agent_status', 'unknown')
        return None, None

    def provider(self, name):
        selection, provider = self.factory.resolve(agent=name)
        owned = self.state.get('agent:' + name)
        if not owned or (owned['provider'], owned['model']) != (selection.provider, selection.model):
            raise ReconciliationRequired(f'{name}: no matching owned session; launch/reconcile before dispatch.')
        return selection, provider

    def dispatch(self, name, pane, message, event_id):
        selection, provider = self.provider(name)
        actual, status = self.info(name)
        if actual != pane or status not in {'idle', 'done'}:
            raise ReconciliationRequired(f'{name}: target is not an owned idle agent.')
        key = 'dispatch:' + event_id
        if not self.state.claim(key, {'agent_id': name, 'provider': selection.provider,
                                     'model': selection.model, 'pane_id': pane, 'phase': AGENT_PHASES[name]}):
            return False
        try:
            context = self.config.context
            prefix = context.instructions() + assemble(context, role=name) if context else ''
            self.gateway.prompt(pane, prefix + message)
            self.state.finish(key, 'done')
            return True
        except BaseException:
            self.state.finish(key, 'uncertain')
            raise


class SessionManager:
    def __init__(self, dispatcher):
        self.dispatcher = dispatcher

    def clear(self, name):
        _, provider = self.dispatcher.provider(name)
        if not provider.capabilities.clear_context:
            raise UnsupportedCapability(f'{name}: context rotation not verified; close and relaunch manually when idle.')
        pane, status = self.dispatcher.info(name)
        if not pane or status not in {'idle', 'done'}:
            raise ReconciliationRequired(f'{name}: session busy or not owned.')
        self.dispatcher.gateway.prompt(pane, provider.clear_instruction())
