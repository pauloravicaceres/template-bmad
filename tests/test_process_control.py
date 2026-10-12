import json
from pathlib import Path
import sys
import tempfile
import time
import types
import unittest
from unittest.mock import Mock, patch

from bmad_runtime import commands
from bmad_runtime.commands import Command, CommandRunner, Result
from bmad_runtime.config import RuntimeConfig
from bmad_runtime.errors import ConfigurationError
from bmad_runtime.providers import Capabilities, default_registry
from bmad_runtime.runtime import Runtime

# Parent spawns a grandchild that appends a heartbeat until killed (max ~20 s).
HEARTBEAT = ('import sys, time\n'
             'for _ in range(400):\n'
             '    with open(sys.argv[1], "a") as handle: handle.write(".")\n'
             '    time.sleep(0.05)\n')
PARENT = ('import subprocess, sys, time\n'
          'subprocess.Popen([sys.executable, "-c", sys.argv[1], sys.argv[2]],'
          ' stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)\n'
          'time.sleep(30)\n')


def tree_command(heartbeat):
    return Command((sys.executable, '-c', PARENT, HEARTBEAT, str(heartbeat)), Path.cwd())


def started(path):
    return path.exists() and path.stat().st_size > 0


def assert_stopped(test, heartbeat):
    time.sleep(0.5)
    before = heartbeat.stat().st_size
    time.sleep(0.6)
    test.assertEqual(heartbeat.stat().st_size, before, 'grandchild process kept running')


class FakeProvider:
    identifier = 'fake'
    herdr_kind = 'fake'
    screen_profile = 'claude'   # pane_state: idle Claude-like composer
    capabilities = Capabilities(True, True, True, True)

    def __init__(self, executable):
        self.executable = executable

    def validate(self, selection):
        pass

    def verify(self, *args, **kwargs):
        pass

    def headless(self, selection, root, prompt, directive, env):
        return Command((self.executable, 'headless'), root, stdin=prompt, env=env)

    def skill(self, root, operation):
        return 'fake-skill:' + operation

    def classify(self, result):
        return result.error or ('success' if result.returncode == 0 else 'cli_error')


class ProcessTreeTests(unittest.TestCase):
    def run_interrupted(self, exception):
        """Raise inside the runner's wait loop once the grandchild is alive."""
        with tempfile.TemporaryDirectory() as directory:
            heartbeat = Path(directory) / 'heartbeat.txt'
            real_sleep = time.sleep

            def sleep(seconds):
                if started(heartbeat):
                    raise exception
                real_sleep(seconds)

            fake_time = types.SimpleNamespace(monotonic=time.monotonic, sleep=sleep)
            with patch.object(commands, 'time', fake_time), self.assertRaises(type(exception)):
                CommandRunner(timeout=30).run(tree_command(heartbeat))
            assert_stopped(self, heartbeat)

    def test_cancellation_kills_process_tree(self):
        self.run_interrupted(KeyboardInterrupt())

    def test_unexpected_error_kills_process_tree(self):
        self.run_interrupted(RuntimeError('boom'))

    def test_timeout_kills_process_tree(self):
        with tempfile.TemporaryDirectory() as directory:
            heartbeat = Path(directory) / 'heartbeat.txt'
            begin = time.monotonic()
            # Long enough for the grandchild to exist before the deadline.
            result = CommandRunner(timeout=30).run(tree_command(heartbeat), timeout=3)
            self.assertEqual((result.returncode, result.error), (124, 'timeout'))
            self.assertLess(time.monotonic() - begin, 20)
            self.assertTrue(started(heartbeat))
            assert_stopped(self, heartbeat)

    def test_slot_released_after_cancellation(self):
        runner = CommandRunner(timeout=5, max_processes=1)
        fake_time = types.SimpleNamespace(monotonic=time.monotonic, sleep=Mock(side_effect=KeyboardInterrupt))
        with patch.object(commands, 'time', fake_time), self.assertRaises(KeyboardInterrupt):
            runner.run(Command((sys.executable, '-c', 'import time; time.sleep(5)'), Path.cwd()))
        result = runner.run(Command((sys.executable, '-c', 'print("ok")'), Path.cwd()))
        self.assertEqual((result.returncode, result.stdout.strip()), (0, 'ok'))


class DurationTests(unittest.TestCase):
    def test_duration_reported_for_success_and_timeout(self):
        runner = CommandRunner(timeout=5)
        result = runner.run(Command((sys.executable, '-c', 'import time; time.sleep(0.2)'), Path.cwd()))
        self.assertEqual(result.returncode, 0)
        self.assertGreaterEqual(result.duration_ms, 150)
        result = runner.run(Command((sys.executable, '-c', 'import time; time.sleep(5)'), Path.cwd()), timeout=0.2)
        self.assertEqual(result.error, 'timeout')
        self.assertIsInstance(result.duration_ms, int)

    def test_duration_absent_when_nothing_spawned(self):
        result = CommandRunner().run(Command(('definitely-not-an-installed-cli',), Path.cwd()))
        self.assertEqual((result.returncode, result.duration_ms), (127, None))

    def test_existing_result_interface_unchanged(self):
        self.assertEqual(Result(0, 'out'), Result(0, 'out', duration_ms=42))
        self.assertEqual(Result(1, 'o', 'e', 'quota').error, 'quota')
        self.assertIsNone(Result(0).duration_ms)


class OperationTimeoutTests(unittest.TestCase):
    def config(self, root, ai):
        (root / 'config_bmad.json').write_text(json.dumps({'ai': ai}), encoding='utf-8')
        return RuntimeConfig.load(root)

    def test_defaults_preserve_headless_timeout(self):
        with tempfile.TemporaryDirectory() as directory:
            self.assertEqual(self.config(Path(directory), {}).operation_timeout('implement'), 1800)
            config = self.config(Path(directory), {'limits': {'headless_timeout': 900}})
            self.assertEqual(config.operation_timeout('clarify'), 900)

    def test_per_operation_override(self):
        with tempfile.TemporaryDirectory() as directory:
            config = self.config(Path(directory), {'limits': {'operation_timeouts': {'implement': 3600}}})
            self.assertEqual(config.operation_timeout('implement'), 3600)
            self.assertEqual(config.operation_timeout('clarify'), 1800)

    def test_invalid_operation_timeouts_rejected(self):
        with tempfile.TemporaryDirectory() as directory:
            for value in [{'unknown': 10}, {'implement': 0}, {'implement': 86401}, {'implement': '60'},
                          {'implement': True}, []]:
                with self.subTest(value=value), self.assertRaises(ConfigurationError):
                    self.config(Path(directory), {'limits': {'operation_timeouts': value}})

    def test_repository_config_still_loads(self):
        config = RuntimeConfig.load(Path(__file__).resolve().parents[1])
        self.assertEqual(config.operation_timeout('implement'), config.data['limits']['headless_timeout'])


class SpecKitExecutionMetadataTests(unittest.TestCase):
    def setUp(self):
        self.temp = tempfile.TemporaryDirectory(prefix='BMAD pruebas ñ ')
        root = Path(self.temp.name)
        (root / 'config_bmad.json').write_text(json.dumps({'ai': {
            'defaults': {'provider': 'fake'}, 'providers': {'fake': {'executable': 'fake-cli'}},
            'limits': {'operation_timeouts': {'implement': 3600}}}}))
        registry = default_registry()
        registry.register('fake', FakeProvider)
        self.runner = Mock()
        self.rt = Runtime(root, registry=registry, gateway=Mock(), runner=self.runner)

    def tearDown(self):
        self.rt.close()
        self.temp.cleanup()

    def runs(self):
        return [json.loads(data) for _, data in self.rt.state.db.execute("SELECT id,data FROM records WHERE id LIKE 'run:%'")]

    def test_operation_timeout_and_metadata_recorded(self):
        self.runner.run.return_value = Result(0, 'done', duration_ms=1234)
        self.assertEqual(self.rt.spec.execute('implement').duration_ms, 1234)
        self.assertEqual(self.runner.run.call_args.kwargs['timeout'], 3600)
        self.rt.spec.execute('clarify')
        self.assertEqual(self.runner.run.call_args.kwargs['timeout'], 1800)
        record = next(run for run in self.runs() if run['agent_id'] == 'speckit.implement')
        self.assertEqual((record['state'], record['duration_ms'], record['timeout_s'], record['returncode']),
                         ('done', 1234, 3600, 0))
        self.assertEqual((record['cost_usd'], record['turns']), ('no_disponible', 'no_disponible'))

    def test_failure_keeps_status_and_duration(self):
        self.runner.run.return_value = Result(124, error='timeout', duration_ms=50)
        result = self.rt.spec.execute('implement')
        self.assertEqual((result.returncode, result.error, result.duration_ms), (124, 'timeout', 50))
        self.assertEqual(self.runs()[0]['state'], 'timeout')

    def test_cancellation_marks_run_uncertain(self):
        self.runner.run.side_effect = KeyboardInterrupt
        with self.assertRaises(KeyboardInterrupt):
            self.rt.spec.execute('implement')
        self.assertEqual(self.runs()[0]['state'], 'uncertain')


if __name__ == '__main__':
    unittest.main()
