"""Persistence and provider-neutral boundaries used by the legacy BMAD workflow."""
from .errors import ReconciliationRequired
from .state import StateStore


class WatcherService:
    def __init__(self, runtime):
        self.runtime = runtime

    def read_lines(self):
        path = self.runtime.context.tracker_path
        if not path.exists():
            return []
        return [line for line in path.read_text(encoding='utf-8').splitlines(keepends=True) if line.strip()]

    def begin_line(self, number, line):
        key = 'event:' + StateStore.fingerprint(number, line)
        return key, self.runtime.state.claim(key)

    def complete_line(self, key):
        self.runtime.state.finish(key, 'done')

    def restore_cursor(self, lines, fallback):
        saved = self.runtime.state.get('tracker_cursor')
        if saved is None:
            return fallback
        count = saved['count']
        if count > len(lines) or StateStore.fingerprint(*lines[:count]) != saved['prefix_hash']:
            raise ReconciliationRequired('Tracker history changed before the saved cursor; reconcile instead of replaying old work.')
        return count

    def save_cursor(self, lines, count):
        self.runtime.state.put('tracker_cursor', {'count': count, 'prefix_hash': StateStore.fingerprint(*lines[:count])})

    def pending_tasks(self, lines):
        tasks = []
        for key, data in self.runtime.state.db.execute("SELECT id,data FROM records WHERE id LIKE 'queued:%'"):
            import json
            event = json.loads(data)
            if event['state'] == 'done':
                continue
            index = event['line_number']
            if index >= len(lines) or StateStore.fingerprint(lines[index]) != event['line_hash']:
                raise ReconciliationRequired('Queued tracker line changed; reconcile before restarting.')
            # Only dispatch instructions are persisted by reference. Never re-run
            # extraction (which includes non-idempotent SDD/Git operations).
            text = lines[index][event['start']:event['end']].strip()
            tasks.append({'agente': event['agent_id'], 'mensaje': text, 'event_id': key[7:]})
        return tasks

    def enqueue(self, line_number, line, task):
        event_id = StateStore.fingerprint(line_number, task['agente'], task['mensaje'])
        key = 'queued:' + event_id
        if self.runtime.state.get(key) is None:
            start = line.find(task['mensaje'])
            if start < 0:
                raise ReconciliationRequired('Task must reference the exact tracker line.')
            self.runtime.state.put(key, {'state': 'queued', 'agent_id': task['agente'],
                                        'line_number': line_number, 'line_hash': StateStore.fingerprint(line),
                                        'start': start, 'end': start + len(task['mensaje'])})
        return {**task, 'event_id': event_id}

    def dispatched(self, task):
        self.runtime.state.finish('queued:' + task['event_id'], 'done')
