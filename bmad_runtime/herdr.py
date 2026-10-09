"""Only this gateway knows Herdr verbs and response envelopes."""
import json
from pathlib import Path
import shutil

from .commands import Command
from .errors import CommandError, UnsupportedCapability


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
        data = self._json('tab', 'create', '--label', label, '--cwd', str(cwd))
        try:
            return data['tab']['tab_id'], data['root_pane']['pane_id']
        except KeyError as exc:
            raise CommandError('Herdr tab response lacks IDs.') from exc

    def split(self, pane, direction, cwd):
        data = self._json('pane', 'split', '--pane', pane, '--direction', direction, '--cwd', str(cwd))
        pane_id = data.get('pane', data.get('root_pane', {})).get('pane_id')
        if not pane_id:
            raise CommandError('Herdr split response lacks pane_id.')
        return pane_id

    def rename(self, pane, name):
        self.runner.run(self.command('pane', 'rename', pane, name)).require_success()

    def focus(self, tab):
        self.runner.run(self.command('tab', 'focus', tab)).require_success()

    def start_command(self, name, pane, provider, native):
        prefix = ('agent', 'start', name, '--kind', provider.herdr_kind, '--pane', pane,
                  '--timeout', '30000', '--')
        args = (self.executable, *prefix, *native.argv[1:])
        offset = len(prefix)
        return Command(args, native.cwd, env=native.env, sensitive=frozenset(i + offset for i in native.sensitive))

    def start(self, name, pane, provider, native):
        self.runner.run(self.start_command(name, pane, provider, native)).require_success()

    def prompt(self, pane, text):
        # agent prompt checks that the target is an agent; pane run would also type
        # tracker content into a shell after a CLI crashes.
        return self.runner.run(self.command('agent', 'prompt', pane, text,
                                           '--timeout', '30000', sensitive=frozenset({4}))).require_success()

    def read(self, pane, lines=40):
        return self.runner.run(self.command('pane', 'read', pane, '--source', 'recent',
                                           '--lines', str(lines), '--raw')).require_success().stdout
