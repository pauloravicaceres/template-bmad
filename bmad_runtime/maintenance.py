"""Explicit, ownership-checked session maintenance. No inferred tab deletion."""
import argparse
import json
from pathlib import Path

from .errors import BMADRuntimeError, ReconciliationRequired
from .runtime import Runtime
from .state import project_lock
from .context import add_project_arguments, resolve_context
from .config import AGENT_PHASES


def close_owned_tabs(runtime):
    agents = runtime.gateway.list_agents()
    panes = runtime.gateway.list_panes()
    tabs = runtime.gateway.list_tabs()
    owned_tabs = []
    identities = {runtime.context.session_name(role): role for role in AGENT_PHASES}
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
    add_project_arguments(parser)
    args = parser.parse_args(argv)
    if not args.confirm:
        print('No sessions closed. Inspect Herdr, then pass --confirm to close owned idle tabs.')
        return 0
    rt = None
    try:
        context = resolve_context(root, workspace=args.workspace, project=args.project)
        with project_lock(context, 'watcher'), project_lock(context, 'fleet'):
            rt = Runtime(root, context=context)
            print(f'Closed tabs: {close_owned_tabs(rt)}')
        return 0
    except BMADRuntimeError as exc:
        print(f'ERROR: {exc}')
        return 1
    finally:
        if rt:
            rt.close()
