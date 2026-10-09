"""Bounded subprocess execution. Never log prompts, environment or raw stderr."""
from dataclasses import dataclass, field
import os
from pathlib import Path
import shutil
import signal
import subprocess
import threading
import time

from .errors import CommandError, ConfigurationError


@dataclass(frozen=True)
class Command:
    argv: tuple[str, ...]
    cwd: Path
    stdin: str | None = field(default=None, repr=False)
    env: dict[str, str] = field(default_factory=dict, repr=False)
    sensitive: frozenset[int] = frozenset()

    def sanitized(self):
        return ['<redacted>' if i in self.sensitive else arg for i, arg in enumerate(self.argv)]


@dataclass(frozen=True)
class Result:
    returncode: int
    stdout: str = field(default='', repr=False)
    stderr: str = field(default='', repr=False)
    error: str | None = None

    def require_success(self):
        if self.returncode:
            raise CommandError(f'Command failed: {self.error or "exit"} ({self.returncode}); inspect the CLI locally.')
        return self


class CommandRunner:
    def __init__(self, timeout=120, max_output_bytes=1_048_576, max_processes=1):
        self.timeout = timeout
        self.max_output_bytes = max_output_bytes
        self._slots = threading.BoundedSemaphore(max_processes)

    def run(self, command: Command, *, timeout=None) -> Result:
        if not command.argv or not all(isinstance(a, str) and '\0' not in a for a in command.argv):
            raise ConfigurationError('Commands require nonempty argument lists without NUL.')
        if set(command.env) - {'SPECIFY_FEATURE_DIRECTORY', 'SPECIFY_INIT_DIR', 'ENGINE_ROOT', 'WORKSPACE_ROOT',
                               'PROJECT_ID', 'BMAD_PROJECT', 'BMAD_WORKSPACE', 'BMAD_TRACKER', 'BMAD_DOCUMENTS',
                               'BMAD_APP', 'BMAD_HANDOFFS', 'BMAD_STATE', 'BMAD_LOGS', 'BMAD_TEMP', 'BMAD_CONFIG', 'TEMP', 'TMP', 'TMPDIR'}:
            raise ConfigurationError('Environment override not allowed.')
        executable = shutil.which(command.argv[0])
        if not executable:
            return Result(127, error='cli_missing')
        # Batch/PowerShell launchers need shell parsing on Windows; reject rather than
        # passing model instructions through cmd.exe implicitly.
        if os.name == 'nt' and Path(executable).suffix.lower() in {'.bat', '.cmd', '.ps1'}:
            return Result(126, error='native_executable_required')
        duration = self.timeout if timeout is None else timeout
        if not self._slots.acquire(timeout=duration):
            return Result(124, error='process_limit')
        try:
            return self._execute(command, executable, duration)
        finally:
            self._slots.release()

    def _execute(self, command, executable, duration):
        try:
            environment = dict(os.environ)
            if 'WORKSPACE_ROOT' in command.env:
                for key in ('SPECIFY_FEATURE', 'SPECIFY_FEATURE_DIRECTORY', 'SPECIFY_INIT_DIR',
                            'GIT_DIR', 'GIT_WORK_TREE', 'GIT_INDEX_FILE'):
                    environment.pop(key, None)
            process = subprocess.Popen(
                [executable, *command.argv[1:]], cwd=command.cwd,
                env={**environment, **command.env}, shell=False,
                stdin=subprocess.PIPE if command.stdin is not None else subprocess.DEVNULL,
                stdout=subprocess.PIPE, stderr=subprocess.PIPE,
                start_new_session=os.name != 'nt',
                creationflags=subprocess.CREATE_NO_WINDOW if os.name == 'nt' else 0,
            )
        except OSError:
            return Result(126, error='spawn_failed')
        buffers = [bytearray(), bytearray()]
        overflow = threading.Event()

        def drain(stream, index):
            try:
                while chunk := stream.read(4096):
                    remaining = self.max_output_bytes - len(buffers[index])
                    buffers[index].extend(chunk[:max(0, remaining)])
                    if len(chunk) > remaining:
                        overflow.set()
            finally:
                stream.close()

        def feed():
            try:
                process.stdin.write(command.stdin.encode('utf-8'))
                process.stdin.flush()
            except (BrokenPipeError, OSError):
                pass
            finally:
                process.stdin.close()

        threads = [threading.Thread(target=drain, args=(process.stdout, 0), daemon=True),
                   threading.Thread(target=drain, args=(process.stderr, 1), daemon=True)]
        if command.stdin is not None:
            threads.append(threading.Thread(target=feed, daemon=True))
        for thread in threads:
            thread.start()
        deadline = time.monotonic() + duration
        error = None
        while process.poll() is None:
            if overflow.is_set() or time.monotonic() >= deadline:
                error = 'output_limit' if overflow.is_set() else 'timeout'
                self._terminate(process)
                break
            time.sleep(0.02)
        process.wait()
        for thread in threads:
            thread.join(timeout=1)
        if any(thread.is_alive() for thread in threads):
            error = error or 'output_pipe_open'
        error = error or ('output_limit' if overflow.is_set() else None)
        return Result(124 if error else process.returncode,
                      buffers[0].decode('utf-8', errors='replace'),
                      buffers[1].decode('utf-8', errors='replace'), error)

    @staticmethod
    def _terminate(process):
        if os.name == 'nt':
            # Kill descendants of this specific spawned PID, never a process name.
            try:
                subprocess.run(['taskkill.exe', '/PID', str(process.pid), '/T', '/F'],
                               stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL,
                               timeout=5, shell=False, creationflags=subprocess.CREATE_NO_WINDOW)
            except (OSError, subprocess.TimeoutExpired):
                pass
        else:
            try:
                os.killpg(process.pid, signal.SIGKILL)
            except ProcessLookupError:
                pass
        if process.poll() is None:
            process.kill()
