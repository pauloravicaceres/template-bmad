"""Native CLI strategies. No CLI-specific flags escape this module."""
from dataclasses import dataclass
from pathlib import Path
import re
from typing import Protocol

from .commands import Command, Result
from .config import Selection
from .errors import ConfigurationError, UnsupportedCapability
from .registry import ProviderRegistry


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
    capabilities = Capabilities(True, True, True, True, False, True)

    def __init__(self, executable='claude'):
        self.executable = executable

    def validate(self, selection):
        if set(selection.options) - {'effort', 'permission_mode', 'max_budget_usd'}:
            raise ConfigurationError('Unsupported Claude option.')
        _choice(selection.options.get('effort', 'low'), {'low', 'medium', 'high', 'xhigh', 'max'},
                'Invalid Claude effort.')
        _choice(selection.options.get('permission_mode', 'manual'), {'manual', 'plan', 'acceptEdits'},
                'Claude permission_mode must be manual, plan or acceptEdits; bypass is not supported.')
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

    def _options(self, selection):
        self.validate(selection)
        args = ['--permission-mode', selection.options.get('permission_mode', 'manual')]
        if selection.model:
            args += ['--model', selection.model]
        if 'effort' in selection.options:
            args += ['--effort', selection.options['effort']]
        return args

    def interactive(self, selection, root, profile):
        profile = _profile(profile)
        # Documented native file form avoids Windows argument-length limits and
        # injects the complete role without overwriting a global CLAUDE.md.
        args = [self.executable, *self._options(selection), '--add-dir', str(root), '--append-system-prompt-file', str(profile)]
        return Command(tuple(args), profile.parent)

    def headless(self, selection, root, prompt, directive, env):
        args = [self.executable, '-p', *self._options(selection), '--permission-prompts', 'none']
        if 'max_budget_usd' in selection.options:
            args += ['--max-budget-usd', str(selection.options['max_budget_usd'])]
        if directive:
            path = _profile(directive)
            args += ['--append-system-prompt-file', str(path)]
        return Command(tuple(args), root, stdin=prompt, env=env)

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
        raise UnsupportedCapability('Context clearing and profile reload have not been verified together; rotate the session manually.')


class CodexProvider:
    identifier = 'codex'
    herdr_kind = 'codex'
    capabilities = Capabilities(True, True, True, True, False, True)
    # Verified against the installed Codex catalog and official model docs.
    # Extend only with evidence; an unspecified CLI model cannot certify max.
    _max_effort_models = frozenset({'gpt-6-astra'})
    _efforts = frozenset({'low', 'medium', 'high', 'xhigh', 'max'})

    def __init__(self, executable='codex'):
        self.executable = executable

    def validate(self, selection):
        if set(selection.options) - {'sandbox', 'effort'}:
            raise ConfigurationError('Unsupported Codex option; only sandbox and effort are supported.')
        _choice(selection.options.get('sandbox', 'workspace-write'), {'read-only', 'workspace-write'},
                'Only read-only and workspace-write sandboxes are supported.')
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
        args = [self.executable, *self._options(selection), '--ask-for-approval', 'on-request',
                '--cd', str(profile.parent), '--add-dir', str(root), prompt]
        return Command(tuple(args), profile.parent, sensitive=frozenset({len(args) - 1}))

    def headless(self, selection, root, prompt, directive, env):
        if directive:
            path = _profile(directive)
            prompt += f'\nAntes de actuar, lee y aplica íntegramente la directiva {path.as_posix()}.'
        return Command(tuple([self.executable, 'exec', *self._options(selection), '--cd', str(root), '--ephemeral', '-']),
                       root, stdin=prompt, env=env)

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
        raise UnsupportedCapability('Codex context rotation in Herdr is pending verification; rotate manually.')


class GeminiProvider:
    """Registration exists, but no unverified CLI command is fabricated."""
    identifier = 'gemini'
    herdr_kind = 'gemini'
    capabilities = Capabilities()

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
