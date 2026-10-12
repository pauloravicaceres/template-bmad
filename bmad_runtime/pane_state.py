"""Fase 4F-E5.2.1: fail-closed classification of an agent pane before any automatic write.

Herdr 0.8.2 reports a CLI idle/ready while it shows a dialog, and keys typed into a dialog answer it: in the E5.2
pilot a digit of a maintenance probe chose an option of the Codex 0.162 trust menu, and an Enter picks the
highlighted option ("Trust and continue" in Codex, "No, exit" in Claude). The runtime therefore writes to a pane
only when its current screen positively shows the provider's empty input composer (READY_VERIFIED), the expected
CLI is the pane's foreground process and two consecutive reads agree. A dialog, a running turn, a missing or
foreign process, or anything ambiguous is not ready: nothing is written, and dialogs are left to a human.

Herdr cannot send "only if the screen is still X": between the last read and `agent prompt` a dialog may still
appear. The window is kept to one read and one Herdr call under a per-pane lock, maintenance probes carry no digits,
and callers re-check the pane after writing (a trust dialog or an exited CLI after a write is reported uncertain).
"""
from contextlib import contextmanager
from dataclasses import dataclass, field
import hashlib
import re
import time
import unicodedata

from .errors import AgentBlocked, BMADRuntimeError, ReconciliationRequired
from .state import ProjectLock

READY_VERIFIED = 'READY_VERIFIED'
AWAITING_TRUST = 'AWAITING_TRUST'
AWAITING_PERMISSION = 'AWAITING_PERMISSION'
AWAITING_SELECTION = 'AWAITING_SELECTION'
BUSY = 'BUSY'
UNKNOWN = 'UNKNOWN'
EXITED = 'EXITED'
STATES = (READY_VERIFIED, AWAITING_TRUST, AWAITING_PERMISSION, AWAITING_SELECTION, BUSY, UNKNOWN, EXITED)
# Only a human may answer these; the agent is held until maintenance --reconcile verifies it again.
HUMAN_STATES = (AWAITING_TRUST, AWAITING_PERMISSION, AWAITING_SELECTION)
# Names kept from Phase 4B.1 (agent records, messages and guard evidence).
BLOCKERS = {AWAITING_TRUST: 'trust_dialog', AWAITING_PERMISSION: 'permission_dialog',
            AWAITING_SELECTION: 'selection_menu'}

SCREEN_LINES = 60      # lines requested from `pane read --source visible`
ACTIVE_LINES = 24      # bottom of the screen where dialogs and the composer render
TAIL_LINES = 10        # bottom region for permission/menu/busy evidence (older transcript is ignored)
FOOTER_AFTER = 5       # lines allowed below the composer (footer, status line); its footer must be among them

_ESCAPES = re.compile(r'\x1b\][^\x07\x1b]*(?:\x07|\x1b\\)'      # OSC (titles, hyperlinks)
                      r'|\x1b[PX^_][^\x1b]*\x1b\\'              # DCS/SOS/PM/APC strings
                      r'|\x1b\[[0-?]*[ -/]*[@-~]'               # CSI (colours, cursor moves)
                      r'|\x9b[0-?]*[ -/]*[@-~]'                 # 8-bit CSI
                      r'|\x1b[ -/]*[0-~]')                      # other two-byte escapes
_CONTROLS = re.compile(r'[\x00-\x08\x0b-\x1f\x7f-\x9f]')
# Box drawing and block elements frame both TUIs; '▌' is kept because older Codex used it as composer glyph.
_FRAMES = re.compile('[─-╿▀-▋▍-▟]')


def _rx(*patterns):
    return re.compile('|'.join(f'(?:{pattern})' for pattern in patterns))


# Any provider. Trust dialogs ask about the folder; their wording changes between versions, so several phrasings
# and the surrounding headers count, anywhere in the active region.
TRUST = _rx(r'\btrust (?:this|the) (?:folder|directory|workspace|project|repo)', r'\btrust the (?:files|contents) (?:in|of)',
            r'\bdo you trust\b', r'\btrust and continue\b', r'\bi trust this\b', r'\bfolder access\b',
            r'\baccessing workspace\b', r'\bquick safety check\b', r'\bis this a project you (?:created|trust)',
            r'\buntrusted (?:folder|directory|workspace)', r'\bwork in this (?:folder|directory)\?')
PERMISSION = _rx(r'\bdo you want to\b', r'\bwould you like to (?:run|make|apply|allow|proceed|execute|create|edit)',
                 r'\ballow (?:once|always|all|for this session|this command|command)\b', r"\bdon'?t ask again\b",
                 r'\byes,? (?:proceed|allow|approve)\b', r'\band tell (?:claude|codex) what to do\b',
                 r'\b(?:approve|approval|permission)\b.*\?', r'\bgrant (?:access|permission)', r'\bescalat',
                 r'\b(?:run|continue) without (?:the )?sandbox')
MENU_HINTS = _rx(r'\benter to (?:confirm|select|continue|submit|choose|accept)', r'\besc to (?:cancel|quit|exit|go back|skip)',
                 r'\benter continue\b', r'\besc quit\b', r'\bpress enter\b', r'↑/↓|↑↓|\bup/down\b|\barrow keys?\b',
                 r'\b(?:select|choose|pick) (?:an|one) (?:option|item)', r'\((?:y/n|yes/no)\)|\[(?:y/n)\]')
OPTION = re.compile(r'^(?:[❯›>▶»→▌]\s*)?\(?(\d{1,2})[.)]\s+\S')
CURSOR_OPTION = re.compile(r'^[❯›>▶»→]\s*(?:\(?\d{1,2}[.)]\s+\S|(?:yes|no|trust|quit|allow|approve|deny|cancel|accept|reject|exit)\b)')
BUSY_MARKERS = _rx(r'\b(?:esc|ctrl\+c) to interrupt\b', r'\bworking \(\d', r'\bthinking(?:…|\.\.\.)', r'\(\d+s\s*[·•]')
SHELL_PROMPT = _rx(r'^ps [a-z]:\\.*>$', r'^[a-z]:\\[^<>|]*>$', r'^\S+@\S+:.*[$#]$', r'^[$#]$')
OPTION_WORDS = re.compile(r'^\(?\d{1,2}[.)]\s|^(?:yes|no|trust|quit|allow|approve|deny|cancel|continue|accept|reject|exit)\b')


@dataclass(frozen=True)
class ScreenProfile:
    """Positive evidence of an idle, empty composer for one CLI."""
    glyphs: tuple
    footer: re.Pattern
    placeholder: re.Pattern | None   # None: any text that is not a menu option


PROFILES = {
    # Claude Code 2.x: '❯' between two rules (older: '│ > │' box), footer with the permission mode or shortcuts.
    'claude': ScreenProfile(('❯', '>'), _rx(r'\? for shortcuts', r'\baccept edits on\b', r'\bbypass permissions on\b',
                                            r'\bplan mode on\b', r'shift\+tab to cycle', r'\bauto-accept edits\b',
                                            r'context left until auto-compact'),
                            re.compile(r'^try ".*"?$')),
    # Codex CLI: '›' composer (older '▌') with a rotating dimmed placeholder and a footer below it.
    'codex': ScreenProfile(('›', '▌'), _rx(r'\bcontext left\b', r'\? for shortcuts', r'(?:ctrl\+j|⌃j) newline',
                                           r'⏎ send', r'\btokens used\b', r'\bshift\+enter newline'), None),
}


def screen_lines(screen):
    """Visible text only: escape sequences, controls and frames removed, NFKC, case-folded, blank lines dropped."""
    text = _ESCAPES.sub('', screen or '').replace('\r\n', '\n').replace('\r', '\n')
    text = unicodedata.normalize('NFKC', _CONTROLS.sub('', text.replace('\t', ' ')))
    lines = (' '.join(_FRAMES.sub(' ', line).split()).casefold() for line in text.split('\n'))
    return [line for line in lines if line]


@dataclass(frozen=True)
class Observation:
    state: str
    reason: str
    digest: str = ''
    evidence: tuple = field(default_factory=tuple)

    @property
    def ready(self):
        return self.state == READY_VERIFIED

    @property
    def blocker(self):
        return BLOCKERS.get(self.state)

    def as_dict(self):
        return {'state': self.state, 'reason': self.reason, 'digest': self.digest, 'evidence': list(self.evidence)}


def _clip(line):
    return line if len(line) <= 80 else line[:77] + '...'


def _composer(lines, profile):
    """Index of the empty composer at the bottom (only its footer below it), or (None, reason).

    A composer glyph higher up is an echoed message of the transcript, not the input line.
    """
    start = max(0, len(lines) - 1 - FOOTER_AFTER)
    for index in range(len(lines) - 1, start - 1, -1):
        line = lines[index]
        glyph = next((g for g in profile.glyphs if line == g or line.startswith(g + ' ')), None)
        if glyph is None:
            continue
        rest = line[len(glyph):].strip()
        if rest and (OPTION_WORDS.search(rest) or (profile.placeholder and not profile.placeholder.search(rest))):
            return None, 'composer_not_empty'
        if any(profile.footer.search(after) for after in lines[index + 1:index + 1 + FOOTER_AFTER]):
            return index, None
        return None, 'footer_missing'
    footer = any(profile.footer.search(line) for line in lines[start:])
    return None, 'composer_missing' if footer else 'no_ready_prompt'


def classify(profile_name, screen, *, herdr_status=None):
    """Observation of one screen read. READY_VERIFIED only with positive composer evidence; never by default."""
    if not isinstance(screen, str):
        return Observation(UNKNOWN, 'screen_unavailable')
    lines = screen_lines(screen)
    active = lines[-ACTIVE_LINES:]
    tail = active[-TAIL_LINES:]
    digest = hashlib.sha256('\n'.join(active).encode('utf-8')).hexdigest()[:16]

    def seen(state, reason, matched=()):
        return Observation(state, reason, digest, tuple(_clip(line) for line in matched[:3]))

    trust = [line for line in active if TRUST.search(line)]
    if trust:
        return seen(AWAITING_TRUST, 'trust_dialog', trust)
    permission = [line for line in tail if PERMISSION.search(line)]
    if permission:
        return seen(AWAITING_PERMISSION, 'permission_dialog', permission)
    hints = [line for line in tail if MENU_HINTS.search(line) or CURSOR_OPTION.search(line)]
    if hints:
        return seen(AWAITING_SELECTION, 'menu_hint', hints)
    options = [(index, line) for index, line in enumerate(tail) if OPTION.search(line)]
    numbers = {OPTION.search(line).group(1) for _, line in options}
    if {'1', '2'} <= numbers:
        # A numbered list is transcript only when the provider's composer renders below it.
        profile = PROFILES.get(profile_name)
        below, _ = _composer(tail, profile) if profile else (None, None)
        if below is None or below < options[-1][0]:
            return seen(AWAITING_SELECTION, 'numbered_menu', [line for _, line in options])
    if herdr_status == 'blocked':
        return seen(AWAITING_PERMISSION, 'herdr_blocked')
    busy = [line for line in tail if BUSY_MARKERS.search(line)]
    if busy or herdr_status == 'working':
        return seen(BUSY, 'turn_running' if busy else 'herdr_working', busy)
    if not lines:
        return seen(UNKNOWN, 'empty_screen')
    if SHELL_PROMPT.search(lines[-1]):
        return seen(EXITED, 'shell_prompt', lines[-1:])
    profile = PROFILES.get(profile_name)
    if profile is None:
        return seen(UNKNOWN, 'no_screen_profile')
    index, problem = _composer(active, profile)
    if index is None:
        return seen(UNKNOWN, problem)
    if herdr_status not in (None, 'idle', 'done'):
        return seen(UNKNOWN, f'herdr_{herdr_status}')
    return seen(READY_VERIFIED, 'composer_ready', active[index:index + 1])


class PaneNotReady(BMADRuntimeError):
    """Nothing was written: the pane is not provably ready (busy, ambiguous, locked or without its CLI)."""

    def __init__(self, message, observation):
        super().__init__(message)
        self.observation = observation


def held_state(observation):
    """Agent record state that holds dispatching after a non-ready observation that needs a human."""
    if observation.state in HUMAN_STATES:
        return 'awaiting_trust'
    return 'unverified'


def refuse(name, pane, observation, *, hold):
    """Error for a pane that cannot receive text; AgentBlocked when a human must act before --reconcile."""
    detail = f'{observation.state} ({observation.reason})'
    if hold:
        label = observation.blocker or observation.state.lower()
        return AgentBlocked(f'{name}: pane {pane} shows {label} [{detail}]; nothing was written. Answer or inspect '
                            f'it manually (never automated), then run python -m bmad_runtime.maintenance --reconcile '
                            f'{name} --confirm.')
    return PaneNotReady(f'{name}: pane {pane} is not verified ready [{detail}]; nothing was written.', observation)


class PaneGate:
    """Pre-write check and per-pane exclusion shared by dispatch, reminders, VERIFY, CLEAR, ROTATE and --reconcile."""
    settle_s = 0.2
    lock_wait_s = 5.0
    lock_poll_s = 0.1

    def __init__(self, gateway, lock_root, *, sleep=time.sleep, clock=time.monotonic):
        self.gateway, self.lock_root, self.sleep, self.clock = gateway, lock_root, sleep, clock

    def process(self, provider, pane):
        """'alive' (the provider CLI is in the foreground), 'exited' (only the shell), 'foreign' or 'unknown'."""
        try:
            info = self.gateway.process_info(pane)
            processes = list(info.get('foreground_processes') or [])
        except (BMADRuntimeError, OSError, AttributeError, KeyError, TypeError):
            return 'unknown'
        if not processes:
            return 'unknown'
        others = [process for process in processes if process.get('pid') != info.get('shell_pid')]
        if not others:
            return 'exited'
        text = ' '.join(' '.join(map(str, process.get('argv') or [])) + ' ' + str(process.get('name') or '')
                        for process in others).lower()
        return 'alive' if provider.herdr_kind in text else 'foreign'

    def _read(self, pane):
        try:
            return self.gateway.read(pane, SCREEN_LINES, source='visible')
        except (BMADRuntimeError, OSError):
            return None

    def observe(self, provider, pane, *, herdr_status=None, reads=2):
        """Observation of the pane now: dialogs first, then process, then `reads` agreeing READY screens."""
        profile = getattr(provider, 'screen_profile', None)
        seen = []
        for attempt in range(max(1, reads)):
            if attempt:
                self.sleep(self.settle_s)
            observation = classify(profile, self._read(pane), herdr_status=herdr_status)
            if observation.state in HUMAN_STATES:
                return observation
            seen.append(observation)
            if not observation.ready:
                break
        process = self.process(provider, pane)
        if process == 'exited':
            return Observation(EXITED, 'pane_at_shell', seen[-1].digest)
        if not seen[-1].ready:
            return seen[-1]
        if process != 'alive':
            return Observation(UNKNOWN, 'process_' + process, seen[-1].digest)
        if len({observation.digest for observation in seen}) > 1:
            return Observation(UNKNOWN, 'screen_changing', seen[-1].digest)
        return seen[-1]

    def blocker(self, provider, pane):
        """Name of a dialog only a human may answer ('trust_dialog', ...) or None; one read, no process check."""
        return classify(getattr(provider, 'screen_profile', None), self._read(pane)).blocker

    @contextmanager
    def exclusive(self, pane):
        """One writer per pane across the runtime's processes; refuses (nothing written) when it stays taken."""
        lock = ProjectLock(self.lock_root, 'pane-' + re.sub(r'[^A-Za-z0-9_.-]', '_', str(pane)))
        deadline = self.clock() + self.lock_wait_s
        while not lock.acquire():
            if self.clock() >= deadline:
                raise PaneNotReady(f'pane {pane} is being written by another runtime operation; nothing was written.',
                                   Observation(BUSY, 'pane_locked'))
            self.sleep(self.lock_poll_s)
        try:
            yield
        finally:
            lock.release()


def require_shell(gateway, pane):
    """Commands are typed into a pane only while its shell is the foreground process (never into a CLI or dialog)."""
    try:
        info = gateway.process_info(pane)
    except (BMADRuntimeError, OSError) as exc:
        raise ReconciliationRequired(f'pane {pane}: cannot verify that its shell is in the foreground ({exc}).') from exc
    processes = info.get('foreground_processes') or []
    if not processes or any(process.get('pid') != info.get('shell_pid') for process in processes):
        raise ReconciliationRequired(f'pane {pane} is not at its shell prompt; nothing was typed.')
