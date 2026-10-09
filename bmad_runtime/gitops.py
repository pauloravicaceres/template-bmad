"""Bounded Git operations; no shell strings or forced checkout."""
import subprocess

from .commands import Command
from .errors import ReconciliationRequired


class GitService:
    def __init__(self, runtime):
        self.runtime = runtime

    def run(self, argv, *, check=False, **_legacy_options):
        if not isinstance(argv, (list, tuple)) or argv[0] != 'git':
            raise ValueError('Git requires an argument list.')
        if '-f' in argv or '--force' in argv:
            raise ReconciliationRequired('Forced Git operations are disabled.')
        context = self.runtime.config.context
        if context and not context.legacy and not (context.workspace_root / '.git').exists():
            raise ReconciliationRequired('Workspace has no local Git repository; refusing to use a parent repository.')
        from .context import ProjectContext
        environment = context.environment() if isinstance(context, ProjectContext) and not context.legacy else {}
        result = self.runtime.runner.run(Command(tuple(argv), self.runtime.config.root, env=environment))
        if check and result.returncode:
            # Do not include stdout/stderr (potential credentials) in an exception.
            raise subprocess.CalledProcessError(result.returncode, ['git', argv[1]])
        return result

    def freeze(self):
        # Refuse to commit another person's pre-staged work.
        staged = self.run(['git', 'diff', '--cached', '--name-only'], check=True).stdout.strip()
        if staged:
            raise ReconciliationRequired('Spec freeze requires an empty staging area; preserve and commit existing work first.')
        self.run(['git', 'add', '--', 'specs/', '.specify/'], check=True)
        changed = self.run(['git', 'diff', '--cached', '--quiet'])
        if changed.returncode == 1:
            self.run(['git', 'commit', '-m', 'spec: [SPEC-FREEZE] Ciclo SDD Arquitectura completado'], check=True)
        elif changed.returncode != 0:
            raise ReconciliationRequired('Could not determine staged specification changes.')
