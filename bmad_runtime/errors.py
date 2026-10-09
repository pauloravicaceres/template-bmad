class BMADRuntimeError(RuntimeError):
    """Actionable error; callers must not report the operation as successful."""


class ConfigurationError(BMADRuntimeError):
    pass


class UnsupportedCapability(BMADRuntimeError):
    pass


class CommandError(BMADRuntimeError):
    pass


class ReconciliationRequired(BMADRuntimeError):
    pass
