from .errors import ConfigurationError


class ProviderRegistry:
    def __init__(self):
        self._adapters = {}

    def register(self, identifier, adapter):
        if identifier in self._adapters:
            raise ConfigurationError(f'Provider already registered: {identifier}')
        self._adapters[identifier] = adapter

    def create(self, identifier, executable):
        try:
            return self._adapters[identifier](executable)
        except KeyError as exc:
            raise ConfigurationError(f'Unknown provider: {identifier}') from exc


class ProviderFactory:
    def __init__(self, config, registry):
        self.config, self.registry = config, registry

    def resolve(self, **target):
        selection = self.config.resolve(**target)
        try:
            executable = self.config.data['providers'][selection.provider]['executable']
        except KeyError as exc:
            raise ConfigurationError(f'Provider is not configured: {selection.provider}') from exc
        provider = self.registry.create(selection.provider, executable)
        provider.validate(selection)
        return selection, provider
