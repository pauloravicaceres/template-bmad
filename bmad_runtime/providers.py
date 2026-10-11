"""Native CLI strategies. No CLI-specific flags escape this module."""
from dataclasses import dataclass, replace
import json
from pathlib import Path
import re
from typing import Protocol

from .commands import Command, Result
from .config import Selection
from .errors import ConfigurationError, UnsupportedCapability
from .guard import HEADLESS_METRICS, metric
from .registry import ProviderRegistry


def _usage(source, values, **qualities):
    """Metrics of one structured result; a value the CLI did not report is unavailable, never zero."""
    return {name: metric(values[name], qualities.get(name, 'measured'), source) if values.get(name) is not None
            else metric(source=source) for name in HEADLESS_METRICS}


@dataclass(frozen=True)
class Capabilities:
    interactive: bool = False
    headless: bool = False
    skills: bool = False
    directives: bool = False
    clear_context: bool = False
    quota_detection: bool = False


class AIProvider(Protocol):
    identifier: str
    executable: str
    herdr_kind: str
    capabilities: Capabilities

    def validate(self, selection: Selection) -> None: ...
    def verify(self, runner, root: Path, *, headless: bool) -> None: ...
    def interactive(self, selection: Selection, root: Path, profile: Path) -> Command: ...
    def headless(self, selection: Selection, root: Path, prompt: str, directive: Path | None, env: dict) -> Command: ...
    def skill(self, root: Path, operation: str) -> str: ...
    def classify(self, result: Result) -> str: ...
    def limit_state(self, text: str) -> str | None: ...
    def clear_instruction(self) -> str: ...


def _require(capability, name):
    if not capability:
        raise UnsupportedCapability(f'{name}: capability pending verification or not supported.')


def _choice(value, allowed, message):
    if not isinstance(value, str) or value not in allowed:
        raise ConfigurationError(message)


def _profile(path):
    path = Path(path).resolve()
    if not path.is_file() or not path.read_text(encoding='utf-8-sig').strip():
        raise ConfigurationError(f'Missing or empty directive: {path.name}')
    return path


def _verified_skill(root, folder, operation, prefix):
    name = f'speckit-{operation}'
    source = root / '.github' / 'skills' / name
    installed = root / folder / 'skills' / name
    if not (source / 'SKILL.md').is_file() or not (installed / 'SKILL.md').is_file():
        raise UnsupportedCapability(f'{name}: install and review the skill in {folder}/skills before execution.')
    # Compare all resources, normalizing line endings only. A name match is not
    # semantic equivalence; different instructions require explicit human review.
    def tree(directory):
        files = {}
        for path in directory.rglob('*'):
            if path.is_file():
                if not path.resolve().is_relative_to(root.resolve()):
                    raise ConfigurationError('Skill resources must remain inside the project.')
                files[path.relative_to(directory).as_posix()] = path.read_bytes().replace(b'\r\n', b'\n')
        return files
    if tree(source) != tree(installed):
        raise UnsupportedCapability(f'{name}: installed skill differs from .github/skills; review and synchronize explicitly.')
    text = (installed / 'SKILL.md').read_text(encoding='utf-8-sig')
    if not re.search(rf'^name:\s*[\"\']?{re.escape(name)}[\"\']?\s*$', text, re.MULTILINE):
        raise ConfigurationError(f'Unexpected skill identity: {name}')
    return prefix + name


class ClaudeProvider:
    identifier = 'claude'
    herdr_kind = 'claude'
    # clear_context: verified live in Herdr; the contract travels as system prompt (--append-system-prompt-file)
    # and survives /clear. Only operator-confirmed maintenance uses it, never the watcher.
    capabilities = Capabilities(True, True, True, True, True, True)
    # Usage the runtime can read from interactive sessions (guard.USAGE_METRICS): the Herdr TUI shows none.
    measured_usage = frozenset()
    # Headless runs with guard.headless_usage: documented `-p --output-format json` result (verified on 2.1.296).
    # Cost is computed by the CLI at list price (costBasis), not billing: an estimate.
    headless_usage = frozenset({'input_tokens', 'cached_input_tokens', 'cache_write_tokens', 'output_tokens',
                                'turns', 'context_window', 'cost_usd'})

    def __init__(self, executable='claude'):
        self.executable = executable

    def validate(self, selection):
        if set(selection.options) - {'effort', 'permission_mode', 'max_budget_usd'}:
            raise ConfigurationError('Unsupported Claude option.')
        _choice(selection.options.get('effort', 'low'), {'low', 'medium', 'high', 'xhigh', 'max'},
                'Invalid Claude effort.')
        _choice(selection.options.get('permission_mode', 'manual'), {'manual', 'plan', 'acceptEdits', 'bypass'},
                'Claude permission_mode must be manual, plan, acceptEdits or bypass.')
        budget = selection.options.get('max_budget_usd', 1)
        if type(budget) not in {int, float} or not 0 < budget <= 1000:
            raise ConfigurationError('Invalid max_budget_usd.')

    def verify(self, runner, root, *, headless):
        text = runner.run(Command((self.executable, '--help'), root)).require_success().stdout
        required = ['--model', '--effort', '--permission-mode', '--append-system-prompt']
        if headless:
            required += ['--print', '--permission-prompts', '--max-budget-usd']
        if any(flag not in text for flag in required):
            raise UnsupportedCapability('Installed Claude CLI lacks required flags.')

    def _options(self, selection, default_mode='manual'):
        self.validate(selection)
        mode = selection.options.get('permission_mode', default_mode)
        # bypass maps to the native flag instead of a permission mode.
        args = ['--dangerously-skip-permissions'] if mode == 'bypass' else ['--permission-mode', mode]
        if selection.model:
            args += ['--model', selection.model]
        if 'effort' in selection.options:
            args += ['--effort', selection.options['effort']]
        return args

    def interactive(self, selection, root, profile):
        profile = _profile(profile)
        # Documented native file form avoids Windows argument-length limits and
        # injects the complete role without overwriting a global CLAUDE.md.
        # Default acceptEdits: file edits inside the allowed directories proceed, shell commands
        # still ask a human. bypass (--dangerously-skip-permissions) only when configured explicitly.
        args = [self.executable, *self._options(selection, 'acceptEdits'), '--add-dir', str(root),
                '--append-system-prompt-file', str(profile)]
        return Command(tuple(args), profile.parent)

    def headless(self, selection, root, prompt, directive, env):
        args = [self.executable, '-p', *self._options(selection), '--permission-prompts', 'none']
        if 'max_budget_usd' in selection.options:
            args += ['--max-budget-usd', str(selection.options['max_budget_usd'])]
        if directive:
            path = _profile(directive)
            args += ['--append-system-prompt-file', str(path)]
        return Command(tuple(args), root, stdin=prompt, env=env)

    def structured_headless(self, command):
        args = list(command.argv)
        at = args.index('-p') + 1
        return replace(command, argv=tuple(args[:at] + ['--output-format', 'json'] + args[at:]))

    def read_headless_usage(self, result):
        """(result whose stdout is the text answer, metrics) of a JSON result; (result, None) for any other output."""
        try:
            data = json.loads(result.stdout or '')
        except ValueError:
            return result, None
        if not isinstance(data, dict) or data.get('type') != 'result':
            return result, None
        source = 'claude --output-format json'
        models = [item for item in (data.get('modelUsage') or {}).values() if isinstance(item, dict)]
        usage = data.get('usage') if isinstance(data.get('usage'), dict) else {}
        values = {'turns': data.get('num_turns') if type(data.get('num_turns')) is int else None}
        # Seen live: a run stopped by --max-budget-usd reports `usage` all zero; only modelUsage holds the counts.
        if models:
            total = lambda key: sum(int(item.get(key) or 0) for item in models)
            counts = (total('inputTokens'), total('cacheReadInputTokens'), total('cacheCreationInputTokens'),
                      total('outputTokens'))
            values['context_window'] = max(int(item.get('contextWindow') or 0) for item in models) or None
            source += ' modelUsage'
        elif not data.get('is_error'):
            counts = tuple(int(usage.get(key) or 0) for key in ('input_tokens', 'cache_read_input_tokens',
                                                                'cache_creation_input_tokens', 'output_tokens'))
        else:
            counts = None
        if counts:
            fresh, cached, written, output = counts
            values.update(input_tokens=fresh + cached + written, cached_input_tokens=cached,
                          cache_write_tokens=written, output_tokens=output)
        cost = data.get('total_cost_usd')
        if type(cost) in (int, float) and models:
            values['cost_usd'] = round(cost, 6)
        metrics = _usage(source, values, cost_usd='estimated')
        if 'cost_usd' in values:
            basis = next((item.get('costBasis') for item in models if item.get('costBasis')), 'unknown')
            metrics['cost_usd']['source'] = f'{source} total_cost_usd (costBasis={basis}; not billing)'
        text = data.get('result') if isinstance(data.get('result'), str) else ''
        stderr = result.stderr or ''
        if data.get('is_error'):
            # classify() keeps reading limits from the error the CLI reported.
            stderr = (stderr + f'\n{data.get("subtype")}: {text or data.get("terminal_reason") or ""}').strip()
        return replace(result, stdout=text, stderr=stderr), metrics

    def skill(self, root, operation):
        return _verified_skill(root, '.claude', operation, '/')

    def limit_state(self, text):
        if re.search(r'usage limit|session limit|limit reached|you.ve hit your|rate.?limit', text, re.I):
            return 'resume' if re.search(r'press enter to continue|has reset', text, re.I) else 'quota'
        return None

    def classify(self, result):
        if result.error:
            return result.error
        if self.limit_state(result.stderr + result.stdout):
            return 'quota'
        return 'success' if result.returncode == 0 else 'cli_error'

    def clear_instruction(self):
        return '/clear'

    def interaction_blocker(self, screen):
        """'trust_dialog' while Claude asks whether to trust the workspace folder.

        Herdr reports the CLI idle and ready during this dialog, and the Enter of a prompt picks the
        highlighted option (observed: 'No, exit'). Never answered automatically.
        """
        text = ' '.join((screen or '').split()).lower()
        if re.search(r'trust (this|the files in this) folder|do you trust', text) and \
                re.search(r'no, exit|enter to confirm|yes, i trust', text):
            return 'trust_dialog'
        return None


class CodexProvider:
    identifier = 'codex'
    herdr_kind = 'codex'
    capabilities = Capabilities(True, True, True, True, False, True)
    # The interactive TUI exposes no usage to the runtime.
    measured_usage = frozenset()
    # Headless runs with guard.headless_usage: documented `exec --json` events (verified on 0.162.0). No cost.
    headless_usage = frozenset({'input_tokens', 'cached_input_tokens', 'cache_write_tokens', 'output_tokens', 'turns'})
    # The Windows sandbox (restricted token) cannot start the Store pwsh alias: the pane shell must
    # resolve pwsh to an installed (MSI) executable before Codex starts in it.
    requires_native_pwsh = True
    # Verified against the installed Codex catalog and official model docs.
    # Extend only with evidence; an unspecified CLI model cannot certify max.
    _max_effort_models = frozenset({'gpt-6-astra'})
    _efforts = frozenset({'low', 'medium', 'high', 'xhigh', 'max'})

    def __init__(self, executable='codex'):
        self.executable = executable

    def validate(self, selection):
        if set(selection.options) - {'sandbox', 'effort', 'approval'}:
            raise ConfigurationError('Unsupported Codex option; only sandbox, approval and effort are supported.')
        _choice(selection.options.get('sandbox', 'workspace-write'), {'read-only', 'workspace-write'},
                'Only read-only and workspace-write sandboxes are supported.')
        _choice(selection.options.get('approval', 'never'), {'on-request', 'never'},
                'Codex approval must be on-request or never.')
        if 'effort' in selection.options:
            effort = selection.options['effort']
            if not isinstance(effort, str) or effort not in self._efforts:
                raise ConfigurationError('Invalid Codex effort; expected low, medium, high, xhigh or max.')
            if effort == 'max' and selection.model not in self._max_effort_models:
                raise ConfigurationError('Codex effort=max requires an explicitly verified model: gpt-6-astra.')

    def verify(self, runner, root, *, headless):
        args = (self.executable, 'exec', '--help') if headless else (self.executable, '--help')
        text = runner.run(Command(args, root)).require_success().stdout
        required = ['--model', '--sandbox', '--cd', '--add-dir', '--config']
        required += ['--ephemeral'] if headless else ['--ask-for-approval']
        if any(flag not in text for flag in required):
            raise UnsupportedCapability('Installed Codex CLI lacks required flags.')

    def _options(self, selection):
        self.validate(selection)
        args = ['--sandbox', selection.options.get('sandbox', 'workspace-write')]
        if selection.model:
            args += ['--model', selection.model]
        if 'effort' in selection.options:
            args += ['-c', f"model_reasoning_effort={selection.options['effort']}"]
        return args

    def interactive(self, selection, root, profile):
        profile = _profile(profile)
        prompt = f'Lee y sigue íntegramente {profile.as_posix()}, incluso si excede el límite de autodescubrimiento. Proyecto: {root.as_posix()}. Espera un handoff del tracker.'
        # Herdr-launched agents never wait for approval unless the selection sets approval=on-request.
        args = [self.executable, *self._options(selection),
                '--ask-for-approval', selection.options.get('approval', 'never'), '--cd', str(profile.parent)]
        # A read-only sandbox admits no extra writable roots: Codex exits if --add-dir is present.
        if selection.options.get('sandbox', 'workspace-write') != 'read-only':
            args += ['--add-dir', str(root)]
        args.append(prompt)
        return Command(tuple(args), profile.parent, sensitive=frozenset({len(args) - 1}))

    def headless(self, selection, root, prompt, directive, env):
        if directive:
            path = _profile(directive)
            prompt += f'\nAntes de actuar, lee y aplica íntegramente la directiva {path.as_posix()}.'
        return Command(tuple([self.executable, 'exec', *self._options(selection), '--cd', str(root), '--ephemeral', '-']),
                       root, stdin=prompt, env=env)

    def structured_headless(self, command):
        args = list(command.argv)
        at = args.index('exec') + 1
        return replace(command, argv=tuple(args[:at] + ['--json'] + args[at:]))

    def read_headless_usage(self, result):
        """(result whose stdout is the last agent message, metrics) of `exec --json`; (result, None) otherwise."""
        events = []
        for line in (result.stdout or '').splitlines():
            try:
                event = json.loads(line) if line.lstrip().startswith('{') else None
            except ValueError:
                event = None
            if isinstance(event, dict) and isinstance(event.get('type'), str):
                events.append(event)
        if not any(event['type'].startswith(('thread.', 'turn.')) for event in events):
            return result, None
        items = [event.get('item') for event in events if event['type'] == 'item.completed']
        messages = [item.get('text') or '' for item in items if isinstance(item, dict) and item.get('type') == 'agent_message']
        errors = [str(event.get('message') or (event.get('error') or {}).get('message') or event['type'])
                  for event in events if event['type'] in ('error', 'turn.failed')]
        turns = [event.get('usage') or {} for event in events if event['type'] == 'turn.completed']
        values = {'turns': len(turns)}
        if turns:
            total = lambda key: sum(int(usage.get(key) or 0) for usage in turns)
            # OpenAI usage: input_tokens already includes the cached share.
            values.update(input_tokens=total('input_tokens'), cached_input_tokens=total('cached_input_tokens'),
                          cache_write_tokens=total('cache_write_input_tokens'), output_tokens=total('output_tokens'))
        stderr = '\n'.join([result.stderr or '', *errors]).strip()
        return (replace(result, stdout=messages[-1] if messages else '', stderr=stderr),
                _usage('codex exec --json turn.completed.usage', values))

    def skill(self, root, operation):
        return _verified_skill(root, '.agents', operation, '$')

    def limit_state(self, text):
        return 'quota' if re.search(r'usage limit|rate.?limit|quota exceeded|too many requests', text, re.I) else None

    def classify(self, result):
        if result.error:
            return result.error
        if self.limit_state(result.stderr + result.stdout):
            return 'quota'
        return 'success' if result.returncode == 0 else 'cli_error'

    def clear_instruction(self):
        # /clear drops the role: Codex receives its contract as the first message, not as system prompt.
        raise UnsupportedCapability('Codex loses its role on /clear; use --rotate.')

    def interaction_blocker(self, screen):
        """'trust_dialog' if Codex asks to trust the working directory; never answered automatically."""
        text = ' '.join((screen or '').split()).lower()
        if re.search(r'trust the (contents of this|files in this) (directory|folder)|do you trust', text):
            return 'trust_dialog'
        return None


class GeminiProvider:
    """Registration exists, but no unverified CLI command is fabricated."""
    identifier = 'gemini'
    herdr_kind = 'gemini'
    capabilities = Capabilities()
    measured_usage = headless_usage = frozenset()

    def __init__(self, executable='gemini'):
        self.executable = executable

    def validate(self, selection):
        if selection.options:
            raise ConfigurationError('Gemini options are pending local CLI verification.')

    def _pending(self, *args, **kwargs):
        raise UnsupportedCapability('Gemini CLI absent during verification; install it and verify help, profiles and skills before enabling the adapter.')

    verify = interactive = headless = skill = clear_instruction = _pending

    def limit_state(self, text):
        return None

    def classify(self, result):
        return 'unverified'


def default_registry():
    registry = ProviderRegistry()
    for provider in (ClaudeProvider, CodexProvider, GeminiProvider):
        registry.register(provider.identifier, provider)
    return registry
