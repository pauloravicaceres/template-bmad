"""Only this gateway knows Herdr verbs and response envelopes."""
import json
import os
from pathlib import Path
import shutil

from .commands import Command
from .errors import CommandError, ConfigurationError, DeliveryRejected, DeliveryUncertain, UnsupportedCapability

# Herdr 0.8.2 error codes returned before any input reaches the agent.
PRE_SEND_ERRORS = frozenset({'agent_blocked', 'agent_not_found', 'agent_not_ready', 'invalid_agent_name',
                             'invalid_agent_argument', 'invalid_target'})
# Runner failures that happen before the herdr process could send anything.
PRE_SPAWN_ERRORS = frozenset({'cli_missing', 'native_executable_required', 'spawn_failed', 'process_limit'})
PROMPT_TIMEOUT_MS = 30000


def store_alias_last(path_value):
    """Order PATH so Microsoft Store execution aliases (WindowsApps) resolve after real executables.

    Codex's Windows sandbox starts commands with CreateProcessAsUserW and a restricted token, which
    cannot activate packaged Store apps: WindowsApps\\pwsh.exe fails with ERROR_ACCESS_DENIED (5).
    Reordering grants nothing; it only makes the installed non-packaged executable win.
    """
    entries = [entry for entry in path_value.split(os.pathsep) if entry]
    aliases = [entry for entry in entries if os.path.normcase(entry).rstrip('\\/').endswith(os.path.normcase(r'Microsoft\WindowsApps'))]
    return os.pathsep.join([entry for entry in entries if entry not in aliases] + aliases)


def pane_env_args(environ=None, platform=None):
    """Per-pane environment for agent panes; never changes user or machine settings."""
    environ = os.environ if environ is None else environ
    if (platform or os.name) != 'nt' or not environ.get('PATH'):
        return ()
    ordered = store_alias_last(environ['PATH'])
    return () if ordered == environ['PATH'] else ('--env', f'PATH={ordered}')


def store_alias(path):
    return bool(path) and os.path.normcase(str(Path(path).parent)).rstrip('\\/').endswith(os.path.normcase(r'Microsoft\WindowsApps'))


def native_pwsh(environ=None):
    """pwsh that a Store-alias-last PATH resolves to in this machine: (path or None, compatible)."""
    environ = os.environ if environ is None else environ
    found = shutil.which('pwsh', path=store_alias_last(environ.get('PATH', '')))
    return found, not store_alias(found)


# Pane shell probe (Windows PowerShell): the shell Herdr restores or reuses may have a PATH that never
# received pane_env_args(). The marker is concatenated so the echoed command never matches the output.
def pane_pwsh_probe(nonce):
    return (f"Write-Output ('BMAD' + '-PWSH {nonce} ' + "
            "[string](Get-Command pwsh -CommandType Application -ErrorAction SilentlyContinue | Select-Object -First 1).Source)")


# Same ordering as store_alias_last, applied to the pane shell process only (inherited by the agent it starts).
PANE_PATH_REPAIR = (r"$env:Path = (@($env:Path -split ';' | Where-Object { $_ -and $_ -notmatch 'Microsoft\\WindowsApps\\?$' }) + "
                    r"@($env:Path -split ';' | Where-Object { $_ -match 'Microsoft\\WindowsApps\\?$' })) -join ';'")


def parse_pwsh_probe(text, nonce):
    """None while the probe output is absent; otherwise the resolved pwsh path ('' when there is none)."""
    marker = f'BMAD-PWSH {nonce} '
    for line in reversed((text or '').splitlines()):
        if line.lstrip().startswith(marker.rstrip()):
            return line.split(marker.rstrip(), 1)[1].strip()
    return None


def herdr_error_code(result):
    for stream in (result.stderr, result.stdout):
        for line in (stream or '').splitlines():
            try:
                error = json.loads(line).get('error')
            except (ValueError, AttributeError):
                continue
            if isinstance(error, dict) and error.get('code'):
                return error['code']
    return None


class HerdrGateway:
    def __init__(self, runner, root, executable='herdr'):
        self.runner, self.root, self.executable = runner, Path(root), executable

    def command(self, *args, sensitive=frozenset()):
        return Command((self.executable, *args), self.root, sensitive=sensitive)

    def _json(self, *args):
        result = self.runner.run(self.command(*args)).require_success()
        try:
            data = json.loads(result.stdout)
            if data.get('ok') is False or data.get('error'):
                raise CommandError('Herdr rejected the operation.')
            return data['result']
        except (KeyError, TypeError, ValueError) as exc:
            raise CommandError('Invalid Herdr response envelope.') from exc

    def verify_provider(self, provider):
        text = self.runner.run(self.command('agent', 'start', '--help')).require_success().stdout
        if provider.herdr_kind not in text.replace(',', ' ').split():
            raise UnsupportedCapability(f'Herdr kind not verified: {provider.herdr_kind}')
        # Herdr starts its canonical executable, not an arbitrary executable from config.
        canonical = shutil.which(provider.herdr_kind)
        configured = shutil.which(provider.executable)
        if not canonical or not configured or Path(canonical).resolve() != Path(configured).resolve():
            raise UnsupportedCapability('Herdr canonical executable differs from configured provider executable.')

    def list_agents(self):
        return self._json('agent', 'list')['agents']

    def list_tabs(self):
        return self._json('tab', 'list')['tabs']

    def list_panes(self):
        return self._json('pane', 'list')['panes']

    def close_tab(self, tab_id):
        self.runner.run(self.command('tab', 'close', tab_id)).require_success()

    def create_tab(self, label, cwd):
        data = self._json('tab', 'create', '--label', label, '--cwd', str(cwd), *pane_env_args())
        try:
            return data['tab']['tab_id'], data['root_pane']['pane_id']
        except KeyError as exc:
            raise CommandError('Herdr tab response lacks IDs.') from exc

    def split(self, pane, direction, cwd):
        data = self._json('pane', 'split', '--pane', pane, '--direction', direction, '--cwd', str(cwd),
                          *pane_env_args())
        pane_id = data.get('pane', data.get('root_pane', {})).get('pane_id')
        if not pane_id:
            raise CommandError('Herdr split response lacks pane_id.')
        return pane_id

    def rename(self, pane, name):
        self.runner.run(self.command('pane', 'rename', pane, name)).require_success()

    def focus(self, tab):
        self.runner.run(self.command('tab', 'focus', tab)).require_success()

    def start_command(self, name, pane, provider, native):
        # Herdr launches agents through the pane shell (PowerShell on Windows) and rejects
        # multi-line arguments; long contracts travel as files.
        if any('\n' in arg or '\r' in arg for arg in native.argv):
            raise ConfigurationError('Agent launch arguments must be single-line; pass long contracts as files.')
        prefix = ('agent', 'start', name, '--kind', provider.herdr_kind, '--pane', pane,
                  '--timeout', '30000', '--')
        args = (self.executable, *prefix, *native.argv[1:])
        offset = len(prefix)
        return Command(args, native.cwd, env=native.env, sensitive=frozenset(i + offset for i in native.sensitive))

    def start(self, name, pane, provider, native):
        self.runner.run(self.start_command(name, pane, provider, native)).require_success()

    def prompt(self, pane, text, timeout_ms=PROMPT_TIMEOUT_MS):
        """Submit and wait only for the agent to accept it (first lifecycle change), not for the turn.

        agent prompt checks that the target is an agent; pane run would also type tracker content
        into a shell after a CLI crashes. Herdr 0.8.2 accepts --timeout only together with --wait.
        """
        return self._delivery(self.runner.run(self.command('agent', 'prompt', pane, text, '--wait',
                                                           '--until', 'working', '--until', 'idle', '--until', 'done',
                                                           '--until', 'blocked', '--timeout', str(timeout_ms),
                                                           sensitive=frozenset({4}))))

    def submit(self, pane, text):
        """Submit a slash command (/clear, /exit) without waiting: the agent may leave the pane.

        The caller verifies the outcome by polling list_agents()/process_info().
        """
        return self._delivery(self.runner.run(self.command('agent', 'prompt', pane, text)))

    def process_info(self, pane):
        return self._json('pane', 'process-info', '--pane', pane)['process_info']

    def _delivery(self, result):
        if result.returncode == 0 and not result.error:
            return result
        code = herdr_error_code(result)
        if result.error in PRE_SPAWN_ERRORS or code in PRE_SEND_ERRORS:
            raise DeliveryRejected(f'Herdr rejected the prompt before sending it ({code or result.error}).')
        if result.returncode == 2 and code is None and (result.stderr or '').lstrip().startswith('error:'):
            # Argument parsing failed before Herdr contacted the agent.
            raise DeliveryRejected('Herdr rejected the prompt arguments before sending them.')
        # agent_prompt_stalled, timeout or unknown failures: the text may sit in the agent input.
        raise DeliveryUncertain(f'Prompt delivery uncertain ({code or result.error or "exit " + str(result.returncode)}); '
                                'inspect the agent pane before authorizing another attempt.')

    def read(self, pane, lines=40, source='recent'):
        """source='visible' is the current screen only (dialogs); 'recent-unwrapped' joins wrapped lines."""
        return self.runner.run(self.command('pane', 'read', pane, '--source', source,
                                           '--lines', str(lines), '--raw')).require_success().stdout

    def run_in_pane(self, pane, command):
        """Type one command into a pane that is at its shell prompt (never into an agent)."""
        if '\n' in command or '\r' in command:
            raise ConfigurationError('Pane commands must be single-line.')
        self.runner.run(self.command('pane', 'run', pane, command)).require_success()
