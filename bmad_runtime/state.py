"""Project-local transactional metadata; no prompts or credentials are persisted."""
from contextlib import contextmanager
import hashlib
import json
import os
from pathlib import Path
import sqlite3
import sys
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

    @classmethod
    def open_readonly(cls, root):
        """Open existing metadata without creating directories, tables or locks; None when absent."""
        path = state_directory(root) / 'state.sqlite3'
        if not path.is_file():
            return None
        store = cls.__new__(cls)
        store.root = root.workspace_root if isinstance(root, ProjectContext) else Path(root).resolve()
        store.db = sqlite3.connect(path.resolve().as_uri() + '?mode=ro', uri=True, timeout=5)
        return store

    def close(self):
        self.db.close()

    def get(self, key):
        row = self.db.execute('SELECT data FROM records WHERE id=?', (key,)).fetchone()
        return json.loads(row[0]) if row else None

    def put(self, key, data):
        self.put_many([(key, data)])

    def put_many(self, items):
        """Write several records in one transaction: all of them or none."""
        with self.db:
            for key, data in items:
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
        if existing['state'] == 'not_delivered':
            # Nothing reached the target: a new, explicitly started attempt is safe.
            with self.db:
                self.db.execute('UPDATE records SET data=? WHERE id=?',
                                (json.dumps({**data, 'attempt': existing.get('attempt', 1) + 1}), key))
            return True
        raise ReconciliationRequired(f'Operation {key[:40]} is {existing["state"]}; inspect partial work before authorizing a new handoff.')

    def finish(self, key, state):
        data = self.get(key)
        if data is None:
            raise ReconciliationRequired('Missing operation metadata.')
        self.put(key, {**data, 'state': state, 'updated': time.time()})

    @staticmethod
    def fingerprint(*parts):
        return hashlib.sha256(json.dumps(parts, ensure_ascii=False).encode('utf-8')).hexdigest()


class ProjectLock:
    """Non-blocking OS advisory lock; the OS releases it on crash. Never delete someone else's lock."""

    def __init__(self, root, name):
        self.name = name
        path = state_directory(root) / f'{name}.lock'
        if isinstance(root, ProjectContext):
            path = root.output(path.relative_to(root.workspace_root))
        self.path = path
        self.handle = None

    def acquire(self):
        """True when this handle now owns the lock; False when another handle (any process) owns it."""
        if self.handle:
            return True
        self.path.parent.mkdir(parents=True, exist_ok=True)
        handle = self.path.open('a+b')
        try:
            handle.seek(0, 2)
            if handle.tell() == 0:
                handle.write(b'0')
                handle.flush()
            handle.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_NBLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_EX | fcntl.LOCK_NB)
        except OSError:
            handle.close()
            return False
        self.handle = handle
        return True

    def release(self):
        if not self.handle:
            return
        handle, self.handle = self.handle, None
        try:
            handle.seek(0)
            if os.name == 'nt':
                import msvcrt
                msvcrt.locking(handle.fileno(), msvcrt.LK_UNLCK, 1)
            else:
                import fcntl
                fcntl.flock(handle.fileno(), fcntl.LOCK_UN)
        finally:
            handle.close()


@contextmanager
def project_lock(root, name):
    """OS releases the advisory lock on crash; never delete someone else's lock."""
    lock = ProjectLock(root, name)
    if not lock.acquire():
        raise ReconciliationRequired(f'Another {name} instance owns this project.')
    try:
        yield
    finally:
        lock.release()


def main(argv=None):
    import argparse
    from .context import add_project_arguments, resolve_context
    parser = argparse.ArgumentParser(description='Inspect/reconcile metadata without replaying model operations.')
    parser.add_argument('--root', type=Path, default=Path(__file__).resolve().parents[1], help='Engine root (legacy alias).')
    add_project_arguments(parser)
    parser.add_argument('--acknowledge', help='Mark an inspected uncertain event as handled; does not retry it.')
    parser.add_argument('--rebaseline-tracker', action='store_true',
                        help='After inspecting a rewritten tracker, treat its complete lines as processed; never replays them.')
    parser.add_argument('--release-followup', metavar='ROL',
                        help='After acknowledging its queued event, stop following a task that can no longer be '
                             'confirmed (e.g. its pane is gone). Never confirms or retries the task.')
    parser.add_argument('--confirm', action='store_true')
    args = parser.parse_args(argv)
    try:
        # Records carry agent text: a cp1252 console must not fail the listing after the changes were applied.
        sys.stdout.reconfigure(encoding='utf-8', errors='replace')
    except (AttributeError, ValueError):
        pass
    context = resolve_context(args.root, workspace=args.workspace, project=args.project)
    with project_lock(context, 'watcher'), project_lock(context, 'fleet'), project_lock(context, 'speckit'):
        store = StateStore(context)
        try:
            if args.acknowledge:
                if not args.confirm or not args.acknowledge.startswith(('event:', 'dispatch:', 'queued:', 'protocol_violation:')):
                    parser.error('Acknowledgement requires --confirm and an event/dispatch/queued/protocol_violation ID.')
                store.finish(args.acknowledge, 'done')
                # Lets session planning treat the inspected event as resolved; never as confirmed.
                store.put(args.acknowledge, {**store.get(args.acknowledge), 'acknowledged': time.time()})
            if args.release_followup:
                followup = store.get('followup') or {}
                entry = followup.get(args.release_followup)
                if not args.confirm or not entry:
                    parser.error('--release-followup needs --confirm and an agent with an active followup.')
                queued = store.get('queued:' + str(entry.get('event_id'))) or {}
                if not queued.get('acknowledged'):
                    parser.error(f'Inspect the task first and acknowledge it: --acknowledge queued:{entry.get("event_id")} '
                                 '--confirm. The followup is released only for an acknowledged event.')
                # The watcher reads followups at start; it holds the watcher lock, so none runs now.
                store.put('followup', {agent: data for agent, data in followup.items() if agent != args.release_followup})
            if args.rebaseline_tracker:
                if not args.confirm:
                    parser.error('Tracker rebaseline requires --confirm.')
                from .watcher_service import read_tracker
                snapshot = read_tracker(context.tracker_path)
                if not snapshot.stable or snapshot.error:
                    parser.error('Tracker is changing or not valid UTF-8; retry when writers are idle.')
                # An unterminated last line stays pending and is processed once complete.
                store.put('tracker_cursor', {'count': len(snapshot.lines),
                                             'prefix_hash': StateStore.fingerprint(*snapshot.lines)})
                if store.get('tracker_integrity'):
                    store.finish('tracker_integrity', 'done')
            for key, raw in store.db.execute('SELECT id,data FROM records ORDER BY id'):
                data = json.loads(raw)
                if data.get('state') != 'done':
                    print(json.dumps({'id': key, **data}, ensure_ascii=False))
        finally:
            store.close()
    return 0


if __name__ == '__main__':
    raise SystemExit(main())
