"""Fase 4F-E5.2.1 test doubles: panes that render an idle composer and run the expected CLI.

The runtime writes to a pane only when pane_state classifies its visible screen READY_VERIFIED and the provider CLI
is the pane's foreground process. Mock gateways return Mock objects for both, which is (correctly) never ready, so
tests that exercise a normal delivery configure their double with ready_pane().
"""

# Shapes of the idle composer (Claude Code 2.x, Codex CLI); nothing here comes from a live pane.
CLAUDE_READY = ('● Listo. Espero una tarea del watcher.\n\n'
                '────────────────────────────────────────\n'
                '❯ \n'
                '────────────────────────────────────────\n'
                '  ⏵⏵ accept edits on (shift+tab to cycle)\n')
CODEX_READY = ('• Contrato leído. Espero un handoff del watcher.\n\n'
               '› Ask Codex to do anything\n\n'
               '  100% context left · ? for shortcuts\n')
READY = {'claude': CLAUDE_READY, 'codex': CODEX_READY}
SHELL = 'PS C:\\ws> '


def foreground(kind):
    """process_info of a pane whose foreground process is the `kind` CLI."""
    return {'shell_pid': 1, 'foreground_processes': [{'pid': 2, 'name': f'{kind}.exe', 'argv': [kind]}]}


def at_shell():
    return {'shell_pid': 1, 'foreground_processes': [{'pid': 1, 'name': 'pwsh.exe'}]}


def ready_pane(gateway, provider=None, *, kind='fake', profile='claude', screens=None):
    """Configure a Mock gateway: every pane shows the idle `profile` composer (or `screens[pane]`) and runs `kind`.

    With `provider`, kind and profile are the provider's (herdr_kind, screen_profile)."""
    if provider is not None:
        kind, profile = provider.herdr_kind, getattr(provider, 'screen_profile', None) or 'claude'
    screens = {} if screens is None else screens

    def read(pane, lines=40, source='recent'):
        return screens.get(pane, READY[profile]) if source == 'visible' else ''

    gateway.read.side_effect = read
    gateway.process_info.side_effect = lambda pane: foreground(kind)
    return screens
