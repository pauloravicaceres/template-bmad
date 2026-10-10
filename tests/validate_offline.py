"""Offline CLI, documentation and workspace checks; no agents or reports."""
import hashlib
import importlib
import json
import os
from pathlib import Path
import re
import secrets
import subprocess
import sys
from urllib.parse import unquote

sys.dont_write_bytecode = True
ROOT = Path(__file__).resolve().parents[1]
sys.path.insert(0, str(ROOT))
from bmad_runtime.config import AGENT_PHASES, OPERATIONS, RuntimeConfig
from bmad_runtime.context import resolve_context
from bmad_runtime.fleet import FleetOrchestrator
from bmad_runtime.providers import default_registry
from bmad_runtime.registry import ProviderFactory
from bmad_runtime.runtime import Runtime
from bmad_runtime.workspace import bootstrap

DOCS = ['README.md', 'GUIDE.md', 'SETUP.md', 'ARCHITECTURE.md',
        'AGENTS.md', 'bmad_runtime/README.md',
        'bmad-control-center/backend/README.md', 'bmad-control-center/frontend/README.md']
DOCS += [f'{role}/README.md' for role in AGENT_PHASES]
DOCS += ['constitution.md']



def snapshot(path):
    return {p.relative_to(path).as_posix(): hashlib.sha256(p.read_bytes()).hexdigest()
            for p in path.rglob('*') if p.is_file()}


class NoProcesses:
    def run(self, *args, **kwargs):
        raise AssertionError('Offline matrix must never execute an external process')


def main():
    base = ROOT / '.test-tmp/offline' / ('smoke-' + secrets.token_hex(10))
    base.mkdir(parents=True)
    results = {'fixture': str(base.relative_to(ROOT)), 'imports': [], 'cli_help': [],
               'matrix': [], 'examples': [], 'markdown_links': []}
    env = dict(os.environ, PYTHONDONTWRITEBYTECODE='1', BMAD_TEST_REAL_CLI='0', PYTHONUTF8='1')
    for key in ('BMAD_WORKSPACE', 'BMAD_PROJECT', 'SPECIFY_INIT_DIR', 'SPECIFY_FEATURE', 'SPECIFY_FEATURE_DIRECTORY'):
        env.pop(key, None)
    for path in sorted((ROOT / 'bmad_runtime').glob('*.py')):
        importlib.import_module('bmad_runtime.' + path.stem)
        results['imports'].append(path.name)
    for script in ['init_bmad.py', 'watcher_bmad.py', 'utils/start_agents.py', 'utils/stop_agents.py',
                   'utils/manage_workspace.py', 'utils/approve_step.py', 'utils/response_sa.py']:
        completed = subprocess.run([sys.executable, str(ROOT / script), '--help'], cwd=base,
                                   env=env, capture_output=True, text=True, encoding='utf-8', timeout=20)
        assert completed.returncode == 0, (script, completed.stderr)
        assert 'usage:' in completed.stdout
        results['cli_help'].append({'script': script, 'status': 'PASS', 'output': completed.stdout})
    contexts = [bootstrap(resolve_context(ROOT, workspace=base / name, project=identity,
                                         initialize=True, environ={}))
                for name, identity in [('Proyecto A', 'audit-a'), ('Proyecto B ñ', 'audit-b')]]
    for context in contexts:
        for relative in ('docs/marker.txt', 'app/marker.txt', 'handoffs/marker.txt',
                         'state/marker.txt', 'logs/marker.txt', 'temp/marker.txt', 'specs/marker.txt'):
            context.output(relative).write_text(context.project_id, encoding='utf-8')
    a, b = contexts
    assert a.session_name('business-analyst') != b.session_name('business-analyst')
    for context, other in [(a, b), (b, a)]:
        other_before = snapshot(other.workspace_root)
        for provider in ('claude', 'codex', 'gemini'):
            selection = {'provider': provider, 'model': None, 'options': {}}
            if provider != 'gemini':
                selection['options'] = {'effort': 'high'}
            context.output('project.json').write_text(json.dumps({
                'schema_version': 1, 'project_id': context.project_id,
                'config': {'ai': {'defaults': selection,
                                  'phases': {phase: selection for phase in ('B', 'M', 'A', 'D')},
                                  'agents': {role: selection for role in AGENT_PHASES},
                                  'speckit': {op: selection for op in OPERATIONS}}}}), encoding='utf-8')
            before = snapshot(context.workspace_root)
            rt = Runtime(ROOT, context=context, persist=False, runner=NoProcesses())
            rows = FleetOrchestrator(rt).plan()
            assert rows and all(row['provider'] == provider for row in rows)
            assert all(row['status'] == ('pending' if provider == 'gemini' else 'verified_cli_contract') for row in rows)
            if provider != 'gemini':
                assert all(row['cwd'] == str(context.workspace_root) for row in rows)
            for operation in OPERATIONS:
                if provider == 'gemini':
                    from bmad_runtime.errors import UnsupportedCapability
                    try:
                        rt.spec.prepare(operation)
                    except UnsupportedCapability:
                        pass
                    else:
                        raise AssertionError('Gemini must not construct executable commands')
                else:
                    _, _, command = rt.spec.prepare(operation)
                    assert command.cwd == context.workspace_root
                    assert command.env['BMAD_TRACKER'] == str(context.tracker_path)
                    native = ('--effort', 'high') if provider == 'claude' else ('-c', 'model_reasoning_effort=high')
                    index = command.argv.index(native[0])
                    assert command.argv[index:index + 2] == native
            rt.close()
            assert snapshot(context.workspace_root) == before
            assert snapshot(other.workspace_root) == other_before
            results['matrix'].append({'project': context.project_id, 'provider': provider,
                                      'status': 'PASS', 'panels': len(rows), 'commands_executed': 0})
    for context in contexts:
        context.output('project.json').write_text(json.dumps({
            'schema_version': 1, 'project_id': context.project_id, 'config': {}}), encoding='utf-8')
        before = snapshot(context.workspace_root)
        for script in ('utils/start_agents.py', 'watcher_bmad.py'):
            completed = subprocess.run([sys.executable, str(ROOT / script), '--workspace',
                str(context.workspace_root), '--project', context.project_id, '--dry-run'],
                cwd=base, env=env, capture_output=True, text=True, encoding='utf-8', timeout=20)
            assert completed.returncode == 0, (script, completed.stderr)
            rows = json.loads(completed.stdout)
            assert rows and all(row['status'] == 'verified_cli_contract' for row in rows)
            assert all(row['cwd'] == str(context.workspace_root) for row in rows)
            if script == 'watcher_bmad.py':
                assert all(row['tracker'] == str(context.tracker_path) for row in rows)
            else:
                assert all(row['workspace'] == str(context.workspace_root) for row in rows)
            results.setdefault('cli_dry_runs', []).append({'project': context.project_id, 'script': script})
        assert snapshot(context.workspace_root) == before
    # Existing JSON examples: schema, all selectors and native option validation, no CLI verification.
    examples = list((ROOT / 'examples').glob('*.json'))
    for path in examples:
        data = json.loads(path.read_text(encoding='utf-8-sig'))
        if 'project_id' in data:
            # Validate actual project example against a new local identity, never its configured external path.
            context = bootstrap(resolve_context(ROOT, workspace=base / path.stem,
                                project=data['project_id'], initialize=True, environ={}))
            context.output('project.json').write_text(json.dumps(data), encoding='utf-8')
            config = RuntimeConfig.load(ROOT, context=context)
        else:
            config = RuntimeConfig.load(ROOT, path)
        factory = ProviderFactory(config, default_registry())
        for role in AGENT_PHASES:
            factory.resolve(agent=role)
        for operation in OPERATIONS:
            factory.resolve(operation=operation)
        results['examples'].append({'path': path.relative_to(ROOT).as_posix(), 'status': 'PASS'})
    for name in DOCS:
        text = (ROOT / name).read_text(encoding='utf-8')
        assert 'BMAD_HISTORICAL_START' not in text, name
        for link in re.findall(r'\[[^\]]*\]\(([^)]+)\)', text):
            if re.match(r'^[a-z]+://', link) or link.startswith('#'):
                continue
            target = unquote(link.split('#')[0].strip('<>'))
            assert (ROOT / name).parent.joinpath(target).exists(), (name, target)
            results['markdown_links'].append({'source': name, 'target': target})
        for index, snippet in enumerate(re.findall(r'```json\s*\n(.*?)```', text, re.S)):
            data = json.loads(snippet)
            target = base / f'doc-example-{Path(name).stem}-{index}.json'
            target.write_text(json.dumps(data), encoding='utf-8')
            factory = ProviderFactory(RuntimeConfig.load(ROOT, target), default_registry())
            for role in AGENT_PHASES:
                factory.resolve(agent=role)
            for operation in OPERATIONS:
                factory.resolve(operation=operation)
    print(json.dumps({key: len(value) for key, value in results.items() if isinstance(value, list)}))


if __name__ == '__main__':
    main()
