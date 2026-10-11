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


class DeliveryRejected(CommandError):
    """Herdr refused the prompt before sending any input; nothing reached the agent."""


class DeliveryUncertain(ReconciliationRequired):
    """Input may have reached the agent; inspect before any new attempt, never retry automatically."""


class AgentBlocked(ReconciliationRequired):
    """The agent shows a dialog (e.g. workspace trust) that only a human may answer; nothing was sent."""
