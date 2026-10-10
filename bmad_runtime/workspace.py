"""Additive workspace bootstrap and explicit, non-destructive legacy migration."""
import argparse
import json
from pathlib import Path
import shutil

from .config import AGENT_PHASES, effective_config, materialize_config
from .context import add_project_arguments, resolve_context
from .errors import BMADRuntimeError, ConfigurationError
from .state import project_lock

ENGINE_ROOT = Path(__file__).resolve().parents[1]


def write_new(path, content):
    path.parent.mkdir(parents=True, exist_ok=True)
    try:
        with path.open('x', encoding='utf-8') as handle:
            handle.write(content)
    except FileExistsError:
        pass


def bootstrap(context, *, config_path=None):
    if context.legacy:
        raise ConfigurationError('Bootstrap requires an explicit workspace and project identity.')
    context.validate(require_exists=False)
    context.workspace_root.mkdir(parents=True, exist_ok=True)
    with project_lock(context, 'bootstrap'):
        identity = {'schema_version': 1, 'project_id': context.project_id, 'config': {}}
        write_new(context.output('project.json'), json.dumps(identity, indent=2) + '\n')
        # Recheck identity under the lock, including racing initializations.
        resolve_context(context.engine_root, workspace=context.workspace_root, project=context.project_id,
                        config_path=config_path)
        for folder in ('docs', 'app', 'handoffs', 'state', 'logs', 'temp', 'specs', '.specify/memory'):
            context.output(folder).mkdir(parents=True, exist_ok=True)
        for role in AGENT_PHASES:
            context.output(f'docs/{role}').mkdir(parents=True, exist_ok=True)
        context.output('docs/business-analyst/HUs-stakeholders').mkdir(parents=True, exist_ok=True)
        write_new(context.output('handoffs/tracker_bmad.md'), '')
        # Only tool scaffolding, never project memory, installed skills or agents.
        for folder in ('scripts', 'templates'):
            source = context.engine_root / '.specify' / folder
            if source.exists():
                for src in sorted(source.rglob('*')):
                    if src.is_file():
                        if not src.resolve().is_relative_to(context.engine_root):
                            raise ConfigurationError('Shared scaffold escapes ENGINE_ROOT.')
                        dst = context.output('.specify/' + src.relative_to(context.engine_root / '.specify').as_posix())
                        write_new(dst, src.read_text(encoding='utf-8-sig'))
        template = context.engine_root / 'utils/readme-specs.template.md'
        if template.is_file():
            write_new(context.output('specs/README.md'), template.read_text(encoding='utf-8-sig'))
        from .technical_context import initialize_constitution
        initialize_constitution(context)
        write_new(context.output('AGENTS.md'), context.instructions())
        raw = effective_config(context, config_path)
        if not context.output('state/config_bmad.json').exists():
            materialize_config(context, raw)
    return context


def migration_plan(context):
    if context.legacy:
        raise ConfigurationError('Migration requires a separate workspace.')
    rows = []
    # Utility source code stays shared. Only known project payloads are migrated.
    mappings = [('docs', 'docs'), ('app', 'app'), ('specs', 'specs'),
                ('.specify/memory', '.specify/memory'), ('.specify/feature.json', '.specify/feature.json'),
                ('utils', 'handoffs')]
    for old, new in mappings:
        source = context.engine_root / old
        files = sorted(source.rglob('*')) if source.is_dir() else [source]
        for src in files:
            if not src.is_file():
                continue
            if not src.resolve().is_relative_to(context.engine_root):
                raise ConfigurationError('Migration source escapes ENGINE_ROOT.')
            relative = src.relative_to(source) if source.is_dir() else Path(src.name)
            if any(part in {'node_modules', '.git', '.venv', '__pycache__'} for part in relative.parts):
                continue
            if old == 'utils' and not (src.name == 'tracker_bmad.md' or 'handoff' in src.name.lower()):
                continue
            target = Path(new) / relative if source.is_dir() else Path(new)
            if src.name == 'tracker_bmad.md':
                target = Path('handoffs/tracker_bmad.md')
            dst = context.output(target)
            rows.append({'source': str(src), 'destination': str(dst), 'conflict': dst.exists(), 'bytes': src.stat().st_size})
    counts = {}
    for row in rows:
        counts[row['destination']] = counts.get(row['destination'], 0) + 1
    for row in rows:
        row['conflict'] |= counts[row['destination']] > 1
    return rows


def migrate(context, *, confirm=False, config_path=None):
    rows = migration_plan(context)
    if not confirm:
        return rows
    context.workspace_root.mkdir(parents=True, exist_ok=True)
    with project_lock(context, 'bootstrap'), project_lock(context, 'watcher'), project_lock(context, 'fleet'), project_lock(context, 'speckit'):
        rows = migration_plan(context)
        if any(row['conflict'] for row in rows):
            raise ConfigurationError('Migration conflicts detected; no payloads copied. Choose an empty destination.')
        for row in rows:
            dst = context.output(Path(row['destination']).relative_to(context.workspace_root))
            dst.parent.mkdir(parents=True, exist_ok=True)
            with Path(row['source']).open('rb') as src, dst.open('xb') as out:
                shutil.copyfileobj(src, out)
        write_new(context.output('logs/migration.json'), json.dumps(rows, ensure_ascii=False, indent=2))
    bootstrap(context, config_path=config_path)
    return rows


def main(argv=None):
    parser = argparse.ArgumentParser(description=__doc__)
    parser.add_argument('action', choices=['init', 'migrate', 'context'])
    add_project_arguments(parser)
    parser.add_argument('--config', type=Path)
    parser.add_argument('--confirm', action='store_true', help='Authorize copying legacy payloads (never overwrites).')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--role', default='solutions-architect', choices=list(AGENT_PHASES))
    parser.add_argument('--record', action='store_true', help='Record observed stack metadata, never approved decisions.')
    args = parser.parse_args(argv)
    try:
        if args.confirm and args.dry_run:
            parser.error('--confirm and --dry-run are mutually exclusive')
        if args.record and (args.action != 'context' or args.dry_run):
            parser.error('--record requires context without --dry-run')
        context = resolve_context(ENGINE_ROOT, workspace=args.workspace, project=args.project,
                                  config_path=args.config, initialize=args.action in {'init', 'migrate'})
        if args.action == 'context':
            from .technical_context import assemble, discover
            result = {'context': assemble(context, role=args.role), 'discovery': discover(context)}
            if args.record:
                path = context.output('docs/architecture/stack-observations.json')
                path.parent.mkdir(parents=True, exist_ok=True)
                path.write_text(json.dumps(result['discovery'], ensure_ascii=False, indent=2) + '\n', encoding='utf-8')
        elif args.action == 'migrate':
            result = migrate(context, confirm=args.confirm, config_path=args.config)
        elif args.dry_run:
            result = context.environment()
        else:
            result = bootstrap(context, config_path=args.config).environment()
        print(json.dumps(result, ensure_ascii=False, indent=2))
        return 0
    except (BMADRuntimeError, OSError) as exc:
        print(f'ERROR: {exc}')
        return 1


if __name__ == '__main__':
    raise SystemExit(main())
