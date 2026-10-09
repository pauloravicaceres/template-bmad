import argparse
import json
import sys
from pathlib import Path

from .config import OPERATIONS
from .errors import BMADRuntimeError
from .fleet import FleetOrchestrator
from .runtime import Runtime
from .context import add_project_arguments


def launcher_main(root, argv=None):
    if hasattr(sys.stdout, 'reconfigure'):
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    parser = argparse.ArgumentParser(description='Launch the BMAD fleet with per-agent provider configuration.')
    parser.add_argument('--dry-run', action='store_true', help='Print a sanitized plan without processes or state writes.')
    parser.add_argument('--config', type=Path)
    add_project_arguments(parser)
    args = parser.parse_args(argv)
    rt = None
    try:
        rt = Runtime(root, config_path=args.config, persist=not args.dry_run,
                     workspace=args.workspace, project=args.project)
        fleet = FleetOrchestrator(rt)
        if args.dry_run:
            print(json.dumps(fleet.plan(), ensure_ascii=False, indent=2))
        else:
            print(f'Flota iniciada: {fleet.launch()} agentes.')
        return 0
    except BMADRuntimeError as exc:
        print(f'ERROR: {exc}')
        return 1
    finally:
        if rt:
            rt.close()


def spec_plan(root, config_path=None, context=None):
    rt = Runtime(root, config_path=config_path, persist=False, context=context)
    rows = []
    for operation in OPERATIONS:
        selection, _ = rt.factory.resolve(operation=operation)
        row = {'operation': operation, 'provider': selection.provider, 'model': selection.model}
        try:
            _, _, command = rt.spec.prepare(operation)
            row.update(status='verified_cli_contract', command=command.sanitized(), stdin='<skill and arguments>',
                       project_id=rt.context.project_id, cwd=str(command.cwd), tracker=str(rt.context.tracker_path))
        except BMADRuntimeError as exc:
            row.update(status='pending', command=None, reason=str(exc))
        rows.append(row)
    return rows
