"""Project-local transactional metadata; no prompts or credentials are persisted."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import time
import uuid

from .errors import ReconciliationRequired
from .context import ProjectContext


def state_directory(root):
    return root.state_dir if isinstance(root, ProjectContext) else Path(root).resolve() / '.bmad-runtime'


class StateStore:
    def __init__(self, root):
        self.root = root.workspace_root if isinstance(root, ProjectContext) else Path(root).resolve()
        directory = state_directory(root)
        directory.mkdir(parents=True, exist_ok=True)
        if isinstance(root, ProjectContext):
            root.output(str((directory / 'state.sqlite3').relative_to(root.workspace_root)))
        self.db = sqlite3.connect(directory / 'state.sqlite3', timeout=5)
        self.db.execute('CREATE TABLE IF NOT EXISTS records (id TEXT PRIMARY KEY, data TEXT NOT NULL)')
        self.db.commit()

    def close(self):
        self.db.close()

    def get(self, key):
        row = self.db.execute('SELECT data FROM records WHERE id=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, key, data):
        with self.db:
            self.db.execute('INSERT OR REPLACE INTO records VALUES (?, ?)', (key, json.dumps(data, ensure_ascii=False)))

    def claim(self, key, metadata=None):
        data = {'run_id': str(uuid.uuid4()), 'state': 'in_flight', 'attempt': 1,
                'time': time.time(), **(metadata or {})}
        with self.db:
            changed = self.db.execute('INSERT OR IGNORE INTO records VALUES (?, ?)', (key, json.dumps(data))).rowcount
        if changed:
            return True
        existing = self.get(key)
        if existing['state'] == 'done':
            return False
        raise ReconciliationRequired(f'Operation {key[:40]} is {existing["state"]}; inspect partial work before authorizing a new handoff.')

    def finish(self, key, state):
        data = self.get(key)
        if data is None:
            raise ReconciliationRequired('Missing operation metadata.')
        self.put(key, {**data, 'state': state, 'updated': time.time()})

    @staticmethod
    def fingerprint(*parts):
        return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode('utf-8')).hexdigest()


@contextmanager
def project_lock(root, name):
    """OS releases the advisory lock on crash; never delete someone else's lock."""
    path = state_directory(root) / f'{name}.lock'
    if isinstance(root, ProjectContext):
        path = root.output(path.relative_to(root.workspace_root))
    path.parent.mkdir(parents=True, exist_ok=True)
    with path.open('a+b') as handle:
        handle.seek(0, 2)
        if handle.tell() == 0:
            handle.write(b'0')
            handle.flush()
        handle.seek(0)
        try:
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError as exc:
            raise ReconciliationRequired(f'Another {name} instance owns this project.') from exc
        try:
            yield
        finally:
            handle.seek(0)
            if os.name == 'nt':
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)


def main(argv=None):
    import argparse
    from .context import add_project_arguments, resolve_context
    parser = argparse.ArgumentParser(description='Inspect/reconcile metadata without replaying model operations.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1], help='Engine root (legacy alias).')
    add_project_arguments(parser)
    parser.add_argument('--acknowledge', help='Mark an inspected uncertain event as handled; does not retry it.')
    parser.add_argument('--confirm', action='store_true')
    args = parser.parse_args(argv)
    context = resolve_context(args.root, workspace=args.workspace, project=args.project)
    with project_lock(context, 'watcher'), project_lock(context, 'fleet'), project_lock(context, 'speckit'):
        store = StateStore(context)
        try:
            if args.acknowledge:
                if not args.confirm or not args.acknowledge.startswith(('event:', 'dispatch:', 'queued:')):
                    parser.error('Acknowledgement requires --confirm and an event/dispatch/queued ID.')
                store.finish(args.acknowledge, 'done')
            for key, raw in store.db.execute('SELECT id,data FROM records ORDER BY id'):
                data = json.loads(raw)
                if data.get('state') != 'done':
                    print(json.dumps({'id': key, **data}, ensure_ascii=False))
        finally:
            store.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
