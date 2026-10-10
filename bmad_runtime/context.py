"""Explicit project identity and filesystem boundaries, independent of operator cwd."""
from dataclasses import dataclass
import hashlib
import json
import os
from pathlib import Path, PureWindowsPath
import re
import warnings

from .errors import ConfigurationError


def read_json(path):
    try:
        value = json.loads(Path(path).read_text(encoding='utf-8-sig'))
        if not isinstance(value, dict):
            raise ValueError('Expected object')
        return value
    except (OSError, ValueError) as exc:
        raise ConfigurationError(f'Cannot read JSON object: {path}') from exc


def absolute_path(value, base):
    path = Path(value).expanduser()
    win = PureWindowsPath(str(value))
    if win.drive and not win.is_absolute():
        raise ConfigurationError('Drive-relative paths are not supported.')
    if os.name != 'nt' and win.is_absolute():
        raise ConfigurationError('Windows absolute paths require a Windows host.')
    return (path if path.is_absolute() else Path(base) / path).resolve()


def validate_id(value):
    if not isinstance(value, str) or not re.fullmatch(r'[a-zA-Z0-9][a-zA-Z0-9_-]{0,63}', value):
        raise ConfigurationError('project_id must contain 1-64 ASCII letters, digits, _ or -.')
    if value.upper() in {'CON', 'PRN', 'AUX', 'NUL', *(f'COM{i}' for i in range(10)), *(f'LPT{i}' for i in range(10))}:
        raise ConfigurationError('Reserved project_id.')
    return value


@dataclass(frozen=True)
class ProjectContext:
    engine_root: Path
    workspace_root: Path
    project_id: str
    legacy: bool = False

    def output(self, relative):
        value = str(relative).replace('\\', '/')
        if Path(value).is_absolute() or PureWindowsPath(value).drive or '..' in Path(value).parts:
            raise ConfigurationError(f'Output must be workspace-relative: {relative}')
        path = (self.workspace_root / value).resolve()
        if not path.is_relative_to(self.workspace_root):
            raise ConfigurationError(f'Output escapes workspace: {relative}')
        if os.name == 'nt' and (':' in value or any(part.endswith((' ', '.')) for part in value.split('/'))):
            raise ConfigurationError('Ambiguous Windows output path.')
        return path

    @property
    def docs_dir(self): return self.output('docs')
    @property
    def app_dir(self): return self.output('app')
    @property
    def specs_dir(self): return self.output('specs')
    @property
    def specify_dir(self): return self.output('.specify')
    @property
    def handoffs_dir(self): return self.output('docs' if self.legacy else 'handoffs')
    @property
    def tracker_path(self): return self.handoffs_dir / 'tracker_bmad.md'
    @property
    def state_dir(self): return self.output('.bmad-runtime' if self.legacy else 'state')
    @property
    def logs_dir(self): return self.output('logs')
    @property
    def temp_dir(self): return self.output('temp')

    def session_name(self, role):
        if self.legacy:
            return role
        digest = hashlib.sha256(os.path.normcase(str(self.workspace_root)).encode()).hexdigest()[:12]
        return f'{self.project_id}-{digest}-{role}'

    def environment(self):
        return {key: str(value) for key, value in {
            'ENGINE_ROOT': self.engine_root, 'WORKSPACE_ROOT': self.workspace_root,
            'PROJECT_ID': self.project_id, 'BMAD_WORKSPACE': self.workspace_root,
            'BMAD_PROJECT': self.project_id, 'BMAD_TRACKER': self.tracker_path,
            'BMAD_DOCUMENTS': self.docs_dir, 'BMAD_APP': self.app_dir,
            'BMAD_HANDOFFS': self.handoffs_dir, 'BMAD_STATE': self.state_dir,
            'BMAD_LOGS': self.logs_dir, 'BMAD_TEMP': self.temp_dir,
            'BMAD_CONFIG': self.output('config_bmad.json' if self.legacy else 'state/config_bmad.json'),
            'SPECIFY_INIT_DIR': self.workspace_root,
            'TEMP': self.temp_dir, 'TMP': self.temp_dir, 'TMPDIR': self.temp_dir,
        }.items()}

    def instructions(self):
        return ('CONTRATO MULTIWORKSPACE (prevalece sobre rutas legacy de perfiles y skills):\n'
                + '\n'.join(f'{key}={value}' for key, value in self.environment().items())
                + '\nTrabaja con cwd=WORKSPACE_ROOT. Lee perfiles, skills y plantillas compartidas '
                'mediante rutas absolutas ENGINE_ROOT. Todas las escrituras pertenecen a WORKSPACE_ROOT. '
                'Reinterpreta ../docs, docs/, app/, specs/, .specify/, temp/ respecto a WORKSPACE_ROOT; '
                'cualquier tracker_bmad.md usa BMAD_TRACKER; handoffs legacy de utils/ usan BMAD_HANDOFFS. '
                'RUTA_CONFIGURACION y cualquier lectura legacy de config_bmad.json usan BMAD_CONFIG (configuración efectiva). '
                'Prohibido escribir en ENGINE_ROOT/utils, ENGINE_ROOT/docs, ENGINE_ROOT/app o perfiles compartidos. '
                'No copies agentes ni skills. No ejecutes init_bmad sin selección de proyecto, clean_files o delete_agents. '
                'Scripts SpecKit: usa .specify/scripts del workspace y SPECIFY_INIT_DIR=WORKSPACE_ROOT; '
                'La política global está en ENGINE_ROOT/constitution.md; CARPETA_CONTEXTO y la clave context '
                'son siempre WORKSPACE_ROOT/.specify/memory/constitution.md. Nunca leas la memoria técnica '
                'de ENGINE_ROOT para otro workspace. Las guías técnicas están en WORKSPACE_ROOT/docs/architecture. '
                'si un proceso hijo no heredó esas variables, pásalas explícitamente. '
                'No inicialices Git ni uses un repositorio padre. No modifiques otros proyectos.\n')

    def validate(self, *, require_exists=True):
        if not self.engine_root.is_dir():
            raise ConfigurationError('ENGINE_ROOT does not exist.')
        if not self.legacy and (self.workspace_root == self.engine_root or self.engine_root.is_relative_to(self.workspace_root)):
            raise ConfigurationError('Workspace cannot equal or contain ENGINE_ROOT.')
        if not self.legacy and self.workspace_root.is_relative_to(self.engine_root):
            from .config import AGENT_PHASES
            first = os.path.normcase(self.workspace_root.relative_to(self.engine_root).parts[0])
            if first in {*AGENT_PHASES, 'docs', 'utils', 'app', 'specs', 'skills', 'bmad_runtime', 'bmad-control-center', '.specify', '.agents', '.claude', '.git', '.github'}:
                raise ConfigurationError('Workspace overlaps a shared engine directory.')
        if require_exists and not self.workspace_root.is_dir():
            raise ConfigurationError('Workspace does not exist; initialize it explicitly.')
        # Resolve each controlled output, including files, to reject existing links/junctions.
        for relative in ('docs', 'app', 'specs', '.specify', 'handoffs', 'state', 'logs', 'temp',
                         'project.json', 'handoffs/tracker_bmad.md', 'state/state.sqlite3'):
            self.output(relative)
        parent = self.workspace_root
        while not parent.exists():
            parent = parent.parent
        if not parent.is_dir() or not os.access(parent, os.R_OK | os.W_OK):
            raise ConfigurationError(f'Workspace is not readable/writable: {parent}')
        return self


def resolve_context(engine_root, *, workspace=None, project=None, config_path=None, initialize=False, environ=None):
    engine = Path(engine_root).resolve()
    env = os.environ if environ is None else environ
    # Explicit CLI selection wins as a pair over environment inherited from another project.
    if workspace is None and project is None:
        workspace, project = env.get('BMAD_WORKSPACE'), env.get('BMAD_PROJECT')
    config_file = absolute_path(config_path, engine) if config_path else engine / 'config_bmad.json'
    defaults = read_json(config_file) if config_path is not None or config_file.exists() else {}
    if workspace is None and project is not None:
        validate_id(project)
        registry = defaults.get('projects', {})
        if not isinstance(registry, dict) or project not in registry or not isinstance(registry[project], str):
            raise ConfigurationError(f'Project {project!r} has no configured workspace.')
        workspace = absolute_path(registry[project], config_file.parent)
    if workspace is None:
        if 'projects' in defaults:
            raise ConfigurationError('Select a workspace with --workspace or a registered --project. Initialize a new workspace with init_bmad.py.')
        warnings.warn('BMAD legacy: no --workspace/--project; using ENGINE_ROOT. Deprecated; removal in next major version, not before 2027-01-01.', FutureWarning, stacklevel=2)
        return ProjectContext(engine, engine, 'legacy', True).validate()
    root = absolute_path(workspace, engine)
    provisional = ProjectContext(engine, root, 'pending').validate(require_exists=not initialize)
    identity = provisional.output('project.json')
    if identity.exists():
        data = read_json(identity)
        actual = validate_id(data.get('project_id'))
        if project is not None and actual != project:
            raise ConfigurationError('Selected project_id differs from project.json.')
        if set(data) - {'schema_version', 'project_id', 'config'} or type(data.get('schema_version')) is not int or data.get('schema_version') != 1:
            raise ConfigurationError('Unsupported project.json schema.')
        project = actual
    elif not initialize:
        raise ConfigurationError('Missing project.json; initialize the selected workspace explicitly.')
    return ProjectContext(engine, root, validate_id(project)).validate(require_exists=not initialize)


def add_project_arguments(parser):
    parser.add_argument('--workspace', type=Path, help='Workspace path; relative paths are anchored to ENGINE_ROOT.')
    parser.add_argument('--project', help='Project identity (registered in global projects when no workspace is given).')
