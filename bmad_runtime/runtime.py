"""Composition root; external providers register here through dependency injection."""
from .commands import CommandRunner
from .config import RuntimeConfig, AGENT_PHASES, OPERATIONS, materialize_config
from .herdr import HerdrGateway
from .providers import default_registry
from .registry import ProviderFactory
from .services import AgentDispatcher, SessionManager, SpecKitExecutor
from .state import StateStore
from .context import resolve_context


class Runtime:
    def __init__(self, root, *, config_path=None, registry=None, runner=None, gateway=None, persist=True,
                 context=None, workspace=None, project=None):
        self.context = context or resolve_context(root, workspace=workspace, project=project, config_path=config_path)
        self.config = RuntimeConfig.load(self.context.workspace_root, config_path, self.context)
        limits = self.config.data['limits']
        self.runner = runner or CommandRunner(limits['command_timeout'], limits['max_output_bytes'], limits['max_processes'])
        self.factory = ProviderFactory(self.config, registry or default_registry())
        for identifier, settings in self.config.data['providers'].items():
            self.factory.registry.create(identifier, settings['executable'])
        # Validate all configured selections before creating any processes/panes.
        for agent in AGENT_PHASES:
            self.factory.resolve(agent=agent)
        for operation in OPERATIONS:
            self.factory.resolve(operation=operation)
        self.gateway = gateway or HerdrGateway(self.runner, self.config.root)
        if persist:
            materialize_config(self.context, self.config.raw)
        self.state = StateStore(self.context) if persist else None
        self.spec = SpecKitExecutor(self.config, self.factory, self.runner, self.state)
        self.dispatcher = AgentDispatcher(self.config, self.factory, self.gateway, self.state)
        self.sessions = SessionManager(self.dispatcher)

    def close(self):
        if self.state:
            self.state.close()
