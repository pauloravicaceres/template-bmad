import json
import uuid

import ux_routing
from .config import AGENT_PHASES
from .errors import ReconciliationRequired, UnsupportedCapability
from .state import project_lock
from .services import interactive_command


TABS_CONFIG = {
    'Negocio y Producto': [
        {'name': 'business-storyteller'},
        {'name': 'product-manager', 'target': 'business-storyteller', 'direction': 'right'},
        {'name': 'business-analyst', 'target': 'product-manager', 'direction': 'right'},
        {'name': 'product-analyst', 'target': 'business-storyteller', 'direction': 'down'},
        {'name': 'qa-documental', 'target': 'product-manager', 'direction': 'down'},
        {'name': 'designer-ux', 'target': 'business-analyst', 'direction': 'down'},
    ],
    'Arquitectura e Ingeniería': [
        {'name': 'solutions-architect'},
        {'name': 'data-architect', 'target': 'solutions-architect', 'direction': 'right'},
        {'name': 'api-architect', 'target': 'solutions-architect', 'direction': 'down'},
        {'name': 'qa-tech', 'target': 'data-architect', 'direction': 'down'},
    ],
    'Desarrollo y Despliegue': [
        {'name': 'qa-auto'},
        {'name': 'code-review', 'target': 'qa-auto', 'direction': 'right'},
        {'name': 'devops', 'target': 'code-review', 'direction': 'right'},
    ],
}


class FleetOrchestrator:
    def __init__(self, runtime):
        self.runtime = runtime

    def plan(self):
        rt = self.runtime
        omitted = ux_routing.agentes_omitidos(rt.config.root, config=rt.config.raw)
        rows = []
        for tab, agents in TABS_CONFIG.items():
            for agent in agents:
                name = agent['name']
                if name in omitted:
                    continue
                selection, provider = rt.factory.resolve(agent=name)
                row = {'tab': tab, **agent, 'phase': AGENT_PHASES[name], 'provider': selection.provider,
                       'model': selection.model, 'status': 'verified_cli_contract'}
                try:
                    native = interactive_command(rt.config, provider, selection, name)
                    row.update(project_id=rt.context.project_id, workspace=str(rt.context.workspace_root),
                               cwd=str(native.cwd), session_name=rt.context.session_name(name))
                    row['command'] = rt.gateway.start_command(rt.context.session_name(name), '<pane_id>', provider, native).sanitized()
                except UnsupportedCapability as exc:
                    row.update(status='pending', command=None, reason=str(exc))
                rows.append(row)
        return rows

    def launch(self):
        rt = self.runtime
        with project_lock(rt.context, 'fleet'):
            rows = self.plan()
            for row in rows:
                if row['status'] == 'pending':
                    raise UnsupportedCapability(row['reason'])
            verified = set()
            for row in rows:
                _, provider = rt.factory.resolve(agent=row['name'])
                if provider.identifier not in verified:
                    provider.verify(rt.runner, rt.config.root, headless=False)
                    rt.gateway.verify_provider(provider)
                    verified.add(provider.identifier)
            existing = rt.gateway.list_agents()
            names = {rt.context.session_name(row['name']) for row in rows}
            if any(agent.get('name') in names for agent in existing):
                raise ReconciliationRequired('Matching agent names already exist in Herdr. Inspect existing sessions; no tabs were closed.')
            first_tab = None
            run_id = str(uuid.uuid4())
            for label in TABS_CONFIG:
                agents = [row for row in rows if row['tab'] == label]
                if not agents:
                    continue
                tab_label = label if rt.context.legacy else rt.context.session_name(label)
                cwd = rt.config.root / agents[0]['name'] if rt.context.legacy else rt.config.root
                tab_id, pane_id = rt.gateway.create_tab(tab_label, cwd)
                rt.state.put('tab:' + tab_id, {'project': str(rt.config.root), 'run_id': run_id, 'label': label})
                first_tab = first_tab or tab_id
                panes = {}
                for index, row in enumerate(agents):
                    name = row['name']
                    if index:
                        cwd = rt.config.root / name if rt.context.legacy else rt.config.root
                        pane_id = rt.gateway.split(panes.get(row.get('target'), pane_id), row.get('direction', 'right'), cwd)
                    panes[name] = pane_id
                    selection, provider = rt.factory.resolve(agent=name)
                    metadata = {'agent_id': name, 'provider': selection.provider, 'model': selection.model,
                                'pane_id': pane_id, 'tab_id': tab_id, 'run_id': run_id,
                                'phase': row['phase'], 'attempt': 1, 'state': 'starting'}
                    rt.state.put('agent:' + name, metadata)
                    try:
                        rt.gateway.rename(pane_id, rt.context.session_name(name))
                        native = interactive_command(rt.config, provider, selection, name)
                        rt.gateway.start(rt.context.session_name(name), pane_id, provider, native)
                        rt.state.put('agent:' + name, {**metadata, 'state': 'ready'})
                    except BaseException:
                        rt.state.put('agent:' + name, {**metadata, 'state': 'uncertain'})
                        raise
            if first_tab:
                rt.gateway.focus(first_tab)
            return len(rows)
