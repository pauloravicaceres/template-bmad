"""Read-only, deterministic classification of the artifact a gate cites (Fase 4F-E2).

One classifier for the Control Center, utils/approve_step.py and later consumers. It resolves a declared
reference against the project's workspace (never the process cwd), never writes, never follows a URL and
never invents a path: it only reports what the filesystem and the gate rules prove.

Statuses:
- PRESENT          regular file inside the workspace (empty files carry a warning).
- MISSING          nothing there, or something that is not a regular file (e.g. a directory).
- FUTURE           absent, and an explicit gate rule says the next stage creates exactly that path.
- EXTERNAL_ALLOWED https URL whose exact hostname is in the gate allowlist (no network access).
- OUTSIDE          resolves outside the workspace (.., absolute, UNC, links, other schemes, credentials...).
- OTHER_PROJECT    resolves into another BMAD project (registry entry or project.json), when provable.
- AMBIGUOUS        a bare filename with several matches in the gate directories (or an unprovable unique one).

OUTSIDE, OTHER_PROJECT and AMBIGUOUS are rejections in every mode; `warn` (default) lets MISSING through with
structured warnings. `enforce` is reserved for a later stage and refused by the configuration.
"""
from dataclasses import dataclass, replace
import os
from pathlib import Path, PurePosixPath, PureWindowsPath
import re
import stat
from urllib.parse import urlsplit

from .context import read_json, absolute_path, validate_id
from .errors import ConfigurationError

PRESENT, MISSING, FUTURE = 'PRESENT', 'MISSING', 'FUTURE'
EXTERNAL_ALLOWED, OUTSIDE, OTHER_PROJECT, AMBIGUOUS = 'EXTERNAL_ALLOWED', 'OUTSIDE', 'OTHER_PROJECT', 'AMBIGUOUS'
STATUSES = (PRESENT, MISSING, FUTURE, EXTERNAL_ALLOWED, OUTSIDE, OTHER_PROJECT, AMBIGUOUS)
REJECTED = (OUTSIDE, OTHER_PROJECT, AMBIGUOUS)
MODES = ('off', 'warn')
DEFAULT_SEARCH_DIRS = ('docs', 'specs', '.specify')
MAX_DEPTH = 6                 # directory levels below each search root
MAX_ENTRIES = 10_000          # directory entries visited per bare-name search
_SKIP_DIRS = {'.git', 'node_modules', '__pycache__', '.pytest_cache', '.venv', 'venv'}
_SCHEME = re.compile(r'^([A-Za-z][A-Za-z0-9+.-]+):')          # two or more characters: 'C:' is a drive
_HOST = re.compile(r'^(?=.{1,253}$)[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?(?:\.[a-z0-9](?:[a-z0-9-]{0,61}[a-z0-9])?)+$')


@dataclass(frozen=True)
class GateRule:
    """Where a gate's deliverable may live. `dirs` bound bare-name searches and mark expected locations;
    `external_hosts` is the exact https hostname allowlist (empty: no URL is accepted)."""
    gate: str
    authors: tuple = ()
    dirs: tuple = DEFAULT_SEARCH_DIRS
    external_hosts: tuple = ()


# Real Control Center gates (author of the last block -> deliverable cited by the approval handoff).
GATES = {rule.gate: rule for rule in (
    GateRule('business-storyteller', ('Business Storyteller', 'BS'), ('docs/business-storyteller',)),
    GateRule('product-analyst', ('Product Analyst', 'PA'), ('docs/product-analyst',)),
    GateRule('product-manager', ('Product Manager', 'PM'), ('docs/product-manager',)),
    GateRule('business-analyst', ('Business Analyst', 'BA'), ('docs/business-analyst',)),
    GateRule('qa-documental', ('QA Documental', 'QA'), ('docs/qa-documental', 'specs')),
    GateRule('designer-ux', ('Designer UX', 'UX'), ('docs/designer-ux',), ('figma.com', 'www.figma.com')),
    GateRule('solutions-architect', ('Solutions Architect', 'SA'), ('docs/solutions-architect', 'docs/architecture')),
    GateRule('qa-tech', ('QA-Tech Senior', 'QA-Tech', 'QT'), ('docs/qa-tech',)),
)}
DEFAULT_EXTERNAL_HOSTS = {gate: rule.external_hosts for gate, rule in GATES.items() if rule.external_hosts}


def gate_for_author(author, policy=None):
    return with_policy(next((rule for rule in GATES.values() if author in rule.authors), None), policy)


def rule_for_folder(folder, policy=None):
    """Rule of a utils/approve_step.py option: the gate with that folder, or that docs folder alone."""
    return with_policy(GATES.get(folder) or GateRule(folder, (), (f'docs/{folder}',)), policy)


def with_policy(rule, policy=None):
    if rule is None or policy is None:
        return rule
    return replace(rule, external_hosts=tuple(policy['external_hosts'].get(rule.gate, ())))


# ----------------------------------------------------------------------------- configuration
def policy_from_config(value):
    """`ai.artifacts`: {"mode": "warn"|"off", "external_hosts": {gate: [hostname, ...]}}. Code defaults apply
    when absent (warn; Figma hosts for designer-ux only); `enforce` is refused until it is authorized."""
    value = {} if value is None else value
    if not isinstance(value, dict) or set(value) - {'mode', 'external_hosts'}:
        raise ConfigurationError('ai.artifacts accepts only mode and external_hosts.')
    mode = value.get('mode', 'warn')
    if mode == 'enforce':
        raise ConfigurationError('ai.artifacts.mode=enforce todavía no está habilitado; usa warn u off.')
    if mode not in MODES:
        raise ConfigurationError('ai.artifacts.mode must be warn or off.')
    hosts = {gate: list(items) for gate, items in DEFAULT_EXTERNAL_HOSTS.items()}
    override = value.get('external_hosts', {})
    if not isinstance(override, dict) or set(override) - set(GATES):
        raise ConfigurationError(f'ai.artifacts.external_hosts accepts only the gates {sorted(GATES)}.')
    for gate, items in override.items():
        if not isinstance(items, list) or not all(isinstance(h, str) and _HOST.match(h) for h in items):
            raise ConfigurationError(f'ai.artifacts.external_hosts.{gate} must list exact lowercase hostnames '
                                     '(no scheme, port, path or wildcard).')
        hosts[gate] = items
    return {'mode': mode, 'external_hosts': {gate: tuple(sorted(set(items))) for gate, items in hosts.items()}}


def load_policy(engine_root):
    """Policy from the engine config_bmad.json (read-only); defaults when the file or the section is absent."""
    path = Path(engine_root) / 'config_bmad.json'
    ai = read_json(path).get('ai', {}) if path.exists() else {}
    return policy_from_config(ai.get('artifacts') if isinstance(ai, dict) else None)


def registered_workspaces(engine_root):
    """{project_id: workspace} of the engine registry; unreadable entries are skipped (read-only)."""
    path = Path(engine_root) / 'config_bmad.json'
    try:
        registry = read_json(path).get('projects', {}) if path.exists() else {}
    except ConfigurationError:
        return {}
    found = {}
    for identity, location in (registry.items() if isinstance(registry, dict) else ()):
        try:
            found[validate_id(identity)] = absolute_path(location, path.parent)
        except (ConfigurationError, TypeError, ValueError, OSError):
            continue
    return found


# ----------------------------------------------------------------------------- result
_WARNING_CODES = {'not_found': 'ARTIFACT_MISSING', 'not_a_file': 'ARTIFACT_NOT_A_FILE',
                  'not_accessible': 'ARTIFACT_NOT_ACCESSIBLE', 'empty_reference': 'ARTIFACT_MISSING'}


@dataclass(frozen=True)
class Classification:
    status: str
    reference: str
    reason: str
    detail: str
    gate: str | None = None
    path: str | None = None           # workspace-relative POSIX path, once resolved
    url: str | None = None
    project: str | None = None        # owner of an OTHER_PROJECT reference
    candidates: tuple = ()
    empty: bool = False
    in_gate_dirs: bool = True
    search_truncated: bool = False

    @property
    def rejected(self):
        return self.status in REJECTED

    @property
    def cited(self):
        """What a handoff names: the declared file name, or the whole URL of an external artifact."""
        if self.status == EXTERNAL_ALLOWED:
            return self.url
        return re.split(r'[\\/]', self.reference.rstrip('/\\'))[-1]

    def warnings(self):
        """Structured warnings for what `warn` lets through; never for a rejection."""
        if self.rejected:
            return []
        found = []

        def add(code, detail):
            found.append({'code': code, 'status': self.status, 'reference': self.reference, 'path': self.path,
                          'gate': self.gate, 'reason': self.reason, 'detail': detail})

        if self.status == MISSING:
            add(_WARNING_CODES.get(self.reason, 'ARTIFACT_MISSING'), self.detail)
        if self.empty:
            add('ARTIFACT_EMPTY', f'{self.path} existe pero está vacío.')
        if self.status in (PRESENT, MISSING) and not self.in_gate_dirs:
            add('ARTIFACT_OUTSIDE_GATE_DIRS', f'{self.path} está fuera de los directorios esperados de la compuerta.')
        if self.search_truncated:
            add('ARTIFACT_SEARCH_TRUNCATED', 'La búsqueda acotada no recorrió todos los directorios permitidos.')
        return found

    def to_dict(self):
        return {'status': self.status, 'reference': self.reference, 'reason': self.reason, 'detail': self.detail,
                'gate': self.gate, 'path': self.path, 'url': self.url, 'project': self.project,
                'candidates': list(self.candidates), 'empty': self.empty, 'in_gate_dirs': self.in_gate_dirs}


# ----------------------------------------------------------------------------- classifier
def _norm(path):
    return os.path.normcase(os.path.normpath(str(path)))


def _fold(relative):
    """Case folding of a workspace-relative POSIX path as the host filesystem compares it (keeps '/')."""
    return relative.lower() if os.name == 'nt' else relative


def _within(child, parent):
    child, parent = _norm(child), _norm(parent)
    try:
        return os.path.commonpath([child, parent]) == parent
    except ValueError:            # different drives
        return False


def _is_link(entry):
    return entry.is_symlink() or (hasattr(entry, 'is_junction') and entry.is_junction())


class ArtifactClassifier:
    """Classifies references against one workspace. Bounded and read-only: stat/scandir/realpath only."""

    def __init__(self, workspace_root, *, project_id=None, engine_root=None, registry=None,
                 max_depth=MAX_DEPTH, max_entries=MAX_ENTRIES):
        given = Path(os.path.abspath(workspace_root))
        self.root = Path(os.path.realpath(given))
        self._roots = (self.root, given)
        self.project_id = project_id
        self.engine_root = Path(os.path.realpath(engine_root)) if engine_root else None
        self.registry = sorted(((pid, Path(os.path.realpath(path))) for pid, path in (registry or {}).items()
                                if _norm(os.path.realpath(path)) != _norm(self.root)),
                               key=lambda item: (-len(str(item[1])), item[0]))
        self.max_depth = max_depth
        self.max_entries = max_entries

    @classmethod
    def for_context(cls, context, **options):
        return cls(context.workspace_root, project_id=context.project_id, engine_root=context.engine_root,
                   registry=registered_workspaces(context.engine_root), **options)

    # ------------------------------------------------------------------ entry point
    def classify(self, reference, rule=None, *, future=()):
        """Classify one declared reference. `future`: workspace-relative paths that an explicit gate rule says
        the next stage creates; only those may be FUTURE, never a fallback for absent files."""
        gate = rule.gate if rule else None
        ref = reference.strip().strip('`').strip() if isinstance(reference, str) else ''

        def result(status, reason, detail, **extra):
            return Classification(status, ref, reason, detail, gate, **extra)

        if not ref:
            return result(MISSING, 'empty_reference', 'La compuerta no declara ningún artefacto.')
        if any(ord(ch) < 32 or ord(ch) == 127 for ch in ref):
            return result(OUTSIDE, 'invalid_characters', 'La referencia contiene caracteres de control.')
        if _SCHEME.match(ref):
            return self._url(ref, rule, result)
        return self._path(ref, rule, tuple(future), result)

    # ------------------------------------------------------------------ URLs
    def _url(self, ref, rule, result):
        hosts = rule.external_hosts if rule else ()
        if not hosts:
            return result(OUTSIDE, 'external_not_allowed', 'Esta compuerta no admite referencias externas.')
        if '\\' in ref or any(ch.isspace() for ch in ref):
            return result(OUTSIDE, 'invalid_url', 'La URL contiene barras invertidas o espacios.')
        try:
            parts = urlsplit(ref)
            port = parts.port
        except ValueError:
            return result(OUTSIDE, 'invalid_url', 'La URL no es válida.')
        if parts.scheme.lower() != 'https':
            return result(OUTSIDE, 'scheme_not_allowed', f'Solo se admite https, no {parts.scheme}.')
        if '@' in parts.netloc or parts.username is not None or parts.password is not None:
            return result(OUTSIDE, 'credentials', 'La URL no puede incluir credenciales.')
        if port not in (None, 443):
            return result(OUTSIDE, 'port_not_allowed', 'La URL no puede indicar otro puerto.')
        host = parts.hostname or ''
        if not host.isascii() or not _HOST.match(host):
            return result(OUTSIDE, 'invalid_host', 'El host de la URL no es un nombre DNS válido.')
        if host not in hosts:
            return result(OUTSIDE, 'host_not_allowed',
                          f'El host {host} no está autorizado en esta compuerta ({", ".join(hosts)}).')
        return result(EXTERNAL_ALLOWED, 'host_allowed', f'Referencia externa autorizada en {host}.', url=ref)

    # ------------------------------------------------------------------ paths
    def _path(self, ref, rule, future, result):
        text = ref.replace('\\', '/')
        win = PureWindowsPath(ref)
        if text.startswith('//'):
            return result(OUTSIDE, 'unc_path', 'Las rutas UNC o de dispositivo no pertenecen al workspace.')
        absolute = None
        if win.drive:
            if not win.root:
                return result(OUTSIDE, 'drive_relative', 'Las rutas relativas a una unidad son ambiguas.')
            if os.name != 'nt':
                return result(OUTSIDE, 'foreign_absolute', 'Ruta absoluta de Windows en un host que no es Windows.')
            absolute, text = ref, text[2:]
        elif text.startswith('/'):
            if os.name == 'nt':
                return result(OUTSIDE, 'rooted_without_drive', 'Ruta absoluta sin unidad: no se resuelve en Windows.')
            absolute = text
        if ':' in text:
            return result(OUTSIDE, 'invalid_characters', 'La ruta contiene ":" (flujo alterno o unidad).')
        if absolute is not None:
            return self._resolve(os.path.normpath(absolute), rule, future, result)
        parts = [part for part in text.split('/') if part not in ('', '.')]
        if not parts:
            return result(MISSING, 'not_a_file', 'La referencia nombra el workspace, no un archivo.')
        if len(parts) == 1 and parts[0] != '..' and not text.endswith('/'):
            return self._search(parts[0], rule, future, result)
        return self._resolve(os.path.normpath(os.path.join(self.root, *parts)), rule, future, result)

    def _relative(self, path):
        return PurePosixPath(*Path(os.path.relpath(path, self.root)).parts).as_posix()

    def _in_gate_dirs(self, relative, rule):
        if rule is None:
            return True
        folded = _fold(relative)
        return any(folded == _fold(d) or folded.startswith(_fold(d) + '/') for d in rule.dirs)

    def _resolve(self, lexical, rule, future, result, *, truncated=False):
        if not any(_within(lexical, root) for root in self._roots):
            return self._foreign(lexical, 'escapes_workspace', result)
        real = os.path.realpath(lexical)
        if not _within(real, self.root):
            return self._foreign(real, 'link_outside_workspace', result)
        owner = self._nested_owner(real)
        if owner:
            return result(OTHER_PROJECT, 'other_project', f'La ruta pertenece al proyecto {owner}.', project=owner)
        relative = self._relative(real)
        common = dict(path=relative, in_gate_dirs=self._in_gate_dirs(relative, rule), search_truncated=truncated)
        try:
            # `real` has no links left; one appearing now, or a different resolution, means it changed meanwhile.
            info = os.stat(real, follow_symlinks=False)
        except (FileNotFoundError, NotADirectoryError):
            if _fold(relative) in {_fold(f.replace('\\', '/')) for f in future}:
                return result(FUTURE, 'created_by_next_stage', f'{relative} lo crea la siguiente etapa.', **common)
            return result(MISSING, 'not_found', f'{relative} no existe en el workspace.', **common)
        except OSError:
            return result(MISSING, 'not_accessible', f'{relative} no se puede inspeccionar.', **common)
        if stat.S_ISLNK(info.st_mode) or _norm(os.path.realpath(lexical)) != _norm(real):
            return result(OUTSIDE, 'changed_during_check', 'La ruta cambió durante la verificación.')
        if not stat.S_ISREG(info.st_mode):
            return result(MISSING, 'not_a_file', f'{relative} no es un archivo regular (p. ej. un directorio).',
                          **common)
        return result(PRESENT, 'found', f'{relative} existe.', empty=info.st_size == 0, **common)

    def _foreign(self, path, reason, result):
        owner = self._owner(path) or self._owner(os.path.realpath(path))
        if owner:
            return result(OTHER_PROJECT, 'other_project', f'La ruta pertenece al proyecto {owner}.', project=owner)
        if self.engine_root and _within(path, self.engine_root):
            return result(OUTSIDE, 'engine_root', 'La ruta apunta al motor BMAD, no al workspace del proyecto.')
        detail = ('Un enlace simbólico o junction resuelve fuera del workspace.' if reason == 'link_outside_workspace'
                  else 'La ruta resuelve fuera del workspace del proyecto.')
        return result(OUTSIDE, reason, detail)

    def _project_id(self, directory):
        marker = Path(directory) / 'project.json'
        try:
            if marker.is_file():
                return validate_id(read_json(marker).get('project_id'))
        except (ConfigurationError, OSError):
            return None
        return None

    def _owner(self, path):
        """Project a foreign path provably belongs to: a registry workspace or the nearest project.json."""
        for identity, root in self.registry:
            if _within(path, root):
                return identity
        for directory in list(Path(path).parents)[:64]:
            identity = self._project_id(directory)
            if identity:
                return identity
        return None

    def _nested_owner(self, real):
        """Another project nested inside this workspace (e.g. a registered workspace under the engine root)."""
        for identity, root in self.registry:
            if _within(real, root) and not _within(self.root, root):
                return identity
        for directory in Path(real).parents:
            if not _within(directory, self.root) or _norm(directory) == _norm(self.root):
                break
            identity = self._project_id(directory)
            if identity:
                return identity
        return None

    # ------------------------------------------------------------------ bare names
    def _search(self, name, rule, future, result):
        """A bare filename: bounded, sorted search in the gate directories only; never the first match."""
        found, budget, truncated = set(), self.max_entries, False
        for directory in dict.fromkeys(rule.dirs if rule else DEFAULT_SEARCH_DIRS):
            base = os.path.join(self.root, *directory.split('/'))
            if not os.path.isdir(base) or not _within(os.path.realpath(base), self.root):
                continue
            stack = [(base, 0)]
            while stack and not truncated:
                current, depth = stack.pop()
                try:
                    with os.scandir(current) as entries:
                        ordered = sorted(entries, key=lambda e: e.name)
                except OSError:
                    continue
                subdirs = []
                for entry in ordered:
                    budget -= 1
                    if budget < 0:
                        truncated = True
                        break
                    if not _is_link(entry) and entry.is_dir(follow_symlinks=False):
                        if depth < self.max_depth and entry.name not in _SKIP_DIRS:
                            subdirs.append((entry.path, depth + 1))
                    elif os.path.normcase(entry.name) == os.path.normcase(name):
                        found.add(self._relative(os.path.join(current, entry.name)))
                stack.extend(reversed(subdirs))
        matches = tuple(sorted(found))
        if len(matches) > 1 or (matches and truncated):
            return result(AMBIGUOUS, 'several_matches' if len(matches) > 1 else 'search_truncated',
                          f'{name} coincide con {len(matches)} archivo(s) y no se puede elegir uno: '
                          + ', '.join(matches[:10]), candidates=matches, search_truncated=truncated)
        if matches:
            return self._resolve(os.path.join(self.root, *matches[0].split('/')), rule, future, result)
        planned = [f for f in future if PurePosixPath(f).name == name]
        if len(planned) == 1:
            return self._resolve(os.path.join(self.root, *planned[0].split('/')), rule, future, result)
        where = ', '.join(rule.dirs if rule else DEFAULT_SEARCH_DIRS)
        return result(MISSING, 'not_found', f'{name} no existe en los directorios de la compuerta ({where}).',
                      search_truncated=truncated)
