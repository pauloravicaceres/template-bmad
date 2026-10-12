"""Fase 4F-E5 §11: consistencia de la configuración efectiva entre el watcher y el resto de componentes.

El watcher puede arrancar con `--config <archivo>`; el Control Center y las CLI calculan la configuración efectiva
por defecto (config_bmad.json del motor + project.json). El watcher persiste al arrancar las políticas que aplica
(`watcher_policy` en el SQLite del proyecto) para que los demás puedan detectar diferencias. Solo diagnóstico: nunca
modifica configuración. Las entregas del outbox no dependen de esta comparación: el único que las acepta o rechaza
es el watcher, y el canal de cada despacho queda persistido.
"""
import os
import time

RECORD = 'watcher_policy'


def effective(data):
    """Policies that decide what a component accepts, from a loaded RuntimeConfig.data."""
    outbox = data.get('outbox') or {}
    return {'outbox': outbox.get('mode', 'direct'), 'outbox_agents': list(outbox.get('agents') or []),
            'hu_lifecycle': (data.get('hu_lifecycle') or {}).get('mode', 'observe'),
            'artifacts': (data.get('artifacts') or {}).get('mode', 'warn'),
            'guard': (data.get('guard') or {}).get('mode', 'observe')}


def record(rt):
    """Persist the running watcher's effective policies (called once at watcher start)."""
    saved = {'config_source': str(rt.config.source) if rt.config.source else None,
             'policies': effective(rt.config.data), 'pid': os.getpid(), 'time': time.time()}
    rt.state.put(RECORD, saved)
    return saved


def default_policies(context, config_path=None):
    from .config import RuntimeConfig
    return effective(RuntimeConfig.load(context.workspace_root, config_path, context).data)


def differences(left, right):
    return [{'setting': key, 'watcher': left.get(key), 'local': right.get(key)}
            for key in sorted(set(left) | set(right)) if left.get(key) != right.get(key)]


def running_policies(store, now=None):
    """Policies of a watcher that is running now (fresh heartbeat), or None."""
    from .watcher_service import watcher_participation
    if store is None:
        return None
    saved = store.get(RECORD)
    if not saved or watcher_participation(store, now) is not None:
        return None
    return saved.get('policies')


def divergence(context, store, *, config_path=None):
    """Read-only comparison between the last watcher policies and this component's effective configuration."""
    from .watcher_service import watcher_participation
    saved = store.get(RECORD) if store is not None else None
    if not saved:
        return {'watcher': None, 'differences': []}
    try:
        local = default_policies(context, config_path)
    except Exception as exc:              # unreadable config: reported, never treated as "no difference"
        return {'watcher': saved, 'error': type(exc).__name__, 'differences': None}
    return {'watcher': saved, 'watcher_running': watcher_participation(store) is None,
            'differences': differences(saved.get('policies') or {}, local)}


def startup_report(rt):
    """Differences between the watcher's effective configuration and the default one (what the CC computes)."""
    if rt.config.source is None:
        return []
    try:
        return differences(effective(rt.config.data), default_policies(rt.context))
    except Exception as exc:
        return [{'setting': 'default_config', 'watcher': 'loaded', 'local': type(exc).__name__}]
