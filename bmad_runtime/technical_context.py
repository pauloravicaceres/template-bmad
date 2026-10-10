"""Provider-independent, bounded workspace context. Reads never imply approval."""
import json
import os
from pathlib import Path
import re
try:
    import tomllib
except ImportError:  # Python 3.10 remains supported by the runtime.
    tomllib = None
import xml.etree.ElementTree as ET

from .errors import ConfigurationError

PROJECT_CONSTITUTION = '.specify/memory/constitution.md'
NEUTRAL_CONSTITUTION = '''# Constitución del proyecto

## Core Principles
Respetar el código y las decisiones aprobadas de este workspace. La política
operativa del motor conserva autoridad sobre aislamiento, seguridad y workflow.

## Stack & Technical Constraints
Estado: pendiente. Si existe código, observar sus manifests y arquitectura antes
de proponer cambios. No heredar tecnologías de otros proyectos. SA puede proponer
opciones; requieren aprobación humana explícita y revisión QT antes de ser obligatorias.
Registrar inventario y diferencias en docs/architecture/tech-stack.md y las
decisiones con estado y evidencia de aprobación en docs/architecture/adr/.

## Governance
Este archivo es la única constitución técnica, también para Spec Kit. Preservar
decisiones aprobadas al enmendarlo. Observación, propuesta y aprobación son estados
distintos; ni detectar una dependencia ni generar un plan concede aprobación.
'''
TECHNICAL_ROLES = {'solutions-architect', 'data-architect', 'api-architect', 'qa-tech',
                   'dev-backend', 'dev-frontend', 'designer-ux', 'qa-auto', 'code-review', 'devops'}
TECHNICAL_OPERATIONS = {'plan', 'tasks', 'analyze', 'converge', 'implement'}
SKIP = {'node_modules', '.git', '.venv', 'venv', '__pycache__', 'bin', 'obj',
        '.test-tmp', 'temp', 'logs', 'state', '.bmad-runtime', 'dist', 'build',
        '.aws', '.ssh', '.codex', '.claude', '.agents', 'secrets', 'credentials'}
MAX_FILE = 512_000
MAX_PROMPT = 24_000


def safe_text(context, relative):
    """Only explicit public documentation/manifests; callers never request secrets."""
    path = context.output(relative)
    lexical = context.workspace_root / relative
    if path != lexical.absolute():
        raise ConfigurationError(f'Context reads cannot follow links: {relative}')
    if any(re.search(r'(?i)(^\.env|secret|credential|password|private)', part) for part in Path(relative).parts):
        raise ConfigurationError('Sensitive files are excluded from agent context.')
    if not path.is_file():
        return ''
    if path.stat().st_size > MAX_FILE:
        raise ConfigurationError(f'Context file exceeds {MAX_FILE} bytes: {relative}')
    return path.read_text(encoding='utf-8-sig')


def _atom(value):
    # Reject URLs, credentials and arbitrary manifest values instead of echoing them.
    value = str(value)
    return value if re.fullmatch(r'[@\w.*+^~/<>=,;!() -]{1,100}', value) else '[valor omitido]'


def discover(context):
    """Bounded, deterministic metadata scan, excluding links and nested workspaces."""
    observations, evidence, issues = [], [], []
    base = context.output('app') if context.legacy else context.workspace_root
    visited = 0
    ci = base / '.github' / 'workflows'
    if ci.is_dir() and ci.resolve() == ci.absolute():
        evidence.extend(path.relative_to(context.workspace_root).as_posix()
                        for path in sorted(ci.glob('*.y*ml'))[:30]
                        if path.is_file() and not path.is_symlink())
    def add(source, technology, version='presente'):
        if len(observations) >= 300:
            return
        observations.append({'source': source, 'technology': _atom(technology),
                             'version': _atom(version), 'status': 'observado'})
    for folder, dirs, files in os.walk(base, followlinks=False):
        current = Path(folder)
        dirs[:] = sorted(d for d in dirs if d.lower() not in SKIP and not d.startswith('.')
                         and not (current / d).is_symlink()
                         and (current / d).resolve() == (current / d).absolute()
                         and not (current / d / 'project.json').exists())
        visited += 1
        if visited > 2000 or len(observations) >= 300 or len(evidence) >= 300:
            issues.append('Exploración limitada; consultar manifests restantes bajo demanda.')
            break
        for name in sorted(files):
            if name.endswith(('.py', '.cs', '.tsx', '.jsx', '.ts', '.rs', '.go')) and len(evidence) < 100:
                source = current / name
                if not source.is_symlink():
                    relative = source.relative_to(context.workspace_root).as_posix()
                    context.output(relative)
                    evidence.append(relative)  # Source paths only; never inject source content.
            if not (name in {'package.json', 'package-lock.json', 'pyproject.toml', 'requirements.txt',
                             'Dockerfile', 'docker-compose.yml', 'compose.yaml', 'Cargo.toml', 'go.mod',
                             'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'uv.lock', '.gitlab-ci.yml', 'azure-pipelines.yml'}
                    or name.endswith(('.csproj', '.sln'))):
                continue
            path = current / name
            if path.is_symlink():
                continue
            relative = path.relative_to(context.workspace_root).as_posix()
            context.output(relative)  # fail closed on an escaping parent junction
            evidence.append(relative)
            if name in {'yarn.lock', 'pnpm-lock.yaml', 'poetry.lock', 'uv.lock', '.gitlab-ci.yml', 'azure-pipelines.yml'} or name.endswith('.sln'):
                continue  # Evidence of build structure; no arbitrary scripts or locked URLs.
            try:
                body = safe_text(context, relative)
                if name == 'package.json':
                    data = json.loads(body)
                    for section in ('dependencies', 'devDependencies'):
                        for key, value in sorted(data.get(section, {}).items()):
                            add(relative, key, value)
                elif name == 'package-lock.json':
                    data = json.loads(body)
                    manifest = json.loads(safe_text(context, (current / 'package.json').relative_to(context.workspace_root))) if (current / 'package.json').is_file() else {}
                    direct = set(manifest.get('dependencies', {})) | set(manifest.get('devDependencies', {}))
                    for key, value in sorted(data.get('packages', {}).items()):
                        if key.startswith('node_modules/') and key.count('node_modules/') == 1:
                            # Only direct packages already observed, not the whole lockfile.
                            package = key[len('node_modules/'):]
                            if package in direct:
                                add(relative, package, value.get('version', 'sin versión'))
                elif name.endswith('.csproj'):
                    root = ET.fromstring(body)
                    for element in root.iter():
                        tag = element.tag.split('}')[-1]
                        if tag in {'TargetFramework', 'TargetFrameworks'}:
                            add(relative, '.NET', element.text or '')
                        elif tag == 'PackageReference':
                            add(relative, element.get('Include', ''), element.get('Version', 'sin versión'))
                elif name == 'pyproject.toml':
                    if tomllib is None:
                        add(relative, 'Python')
                        issues.append(f'{relative}: lectura TOML detallada disponible con Python 3.11+; revisar dependencias manualmente.')
                        continue
                    data = tomllib.loads(body)
                    add(relative, 'Python', data.get('project', {}).get('requires-python', 'presente'))
                    for value in data.get('project', {}).get('dependencies', []):
                        match = re.match(r'([\w.-]+)(.*)', value)
                        if match:
                            add(relative, *match.groups())
                elif name == 'requirements.txt':
                    add(relative, 'Python')
                    for line in body.splitlines():
                        match = re.fullmatch(r'([\w.-]+)([<>=!~][\w.,<>=!~]+)?', line.strip())
                        if match:
                            add(relative, match[1], match[2] or 'sin versión')
                elif name in {'Dockerfile', 'docker-compose.yml', 'compose.yaml'}:
                    for image in re.findall(r'(?im)^\s*(?:FROM\s+|image:\s*)([\w./:-]+)', body):
                        add(relative, 'imagen', image.replace(':', ' '))
                elif name == 'go.mod':
                    add(relative, 'Go')
                elif name == 'Cargo.toml':
                    add(relative, 'Rust')
            except (ValueError, TypeError, AttributeError, ET.ParseError, ConfigurationError) as exc:
                issues.append(f'{relative}: metadatos no disponibles ({type(exc).__name__}).')
    # No approval inferred even when documentation contains a matching dependency.
    documented = safe_text(context, 'docs/architecture/tech-stack.md')
    differences = sorted({o['technology'] + ' ' + o['version'] for o in observations
                          if o['technology'] not in documented or o['version'] not in documented})
    return {'mode': 'brownfield' if evidence else 'greenfield', 'observations': observations,
            'evidence': evidence, 'differences': differences,
            'decision': 'consultar decisiones del proyecto; sin aprobación inferida', 'issues': issues}


def document_index(context, role=None, operation=None):
    technical = role in TECHNICAL_ROLES or operation in TECHNICAL_OPERATIONS
    paths = [PROJECT_CONSTITUTION]
    # Existing local equivalents are supported; never consult engine project memory.
    if technical:
        paths += ['docs/architecture/tech-stack.md', 'docs/architecture/architecture.md',
                  'docs/solutions-architect/tech_guidelines.md']
        folder = context.output('docs/architecture')
        if folder.is_dir():
            guides = ['agent-mandates.md', 'security-observability.md']
            if role not in {'dev-backend', 'data-architect', 'api-architect', 'devops'}:
                guides += ['frontend.md']
            if role not in {'dev-frontend', 'designer-ux'}:
                guides += ['persistence.md', 'integration.md']
            paths += ['docs/architecture/' + name for name in guides]
            role_names = [role] if role else ['dev-backend', 'dev-frontend', 'qa-auto', 'code-review']
            if role in {'solutions-architect', 'qa-tech'}:
                role_names = ['dev-backend', 'dev-frontend', 'qa-auto', 'code-review', 'devops']
            for name in role_names:
                if name:
                    paths.append(f'docs/architecture/roles/{name}.md')
            for path in sorted(context.output('docs/architecture/adr').glob('*.md')):
                if not re.search(r'secret|credential|password|token|private', path.name, re.I):
                    paths.append(path.relative_to(context.workspace_root).as_posix())
    return [p for p in dict.fromkeys(paths) if context.output(p).is_file()][:80]


def source_directory(context, layer):
    """Keep a Brownfield's source tree; ambiguous layouts need explicit code_dirs."""
    found = discover(context)
    candidates = set()
    frontend = {'react', '@angular/core', 'vue', 'nuxt', 'svelte', 'next'}
    for row in found['observations']:
        source = Path(row['source'])
        is_frontend = row['technology'] in frontend and source.name == 'package.json'
        is_backend = source.suffix == '.csproj' or source.name in {'requirements.txt', 'pyproject.toml', 'go.mod', 'Cargo.toml'}
        if (layer == 'frontend' and is_frontend) or (layer == 'backend' and is_backend):
            parts = source.parts[:-1]
            root = '/'.join(parts[:2] if parts and parts[0] == 'app' else parts[:1]) or '.'
            candidates.add(root)
    if len(candidates) == 1:
        return candidates.pop()
    if found['mode'] == 'greenfield':
        return 'app/' + layer  # Neutral organization for a new app, never a technology choice.
    raise ConfigurationError(f'Brownfield layout for {layer} is ambiguous; configure project.json.config.code_dirs without moving source files.')


def assemble(context, *, role=None, operation=None, compact=False):
    policy = context.engine_root / 'constitution.md'
    if policy.exists() and policy.resolve() != policy.absolute():
        raise ConfigurationError('Framework policy cannot follow links.')
    parts = ['CONTEXTO BMAD: política operativa > aislamiento y seguridad; constitución local > '
             'restricciones técnicas; ADR aprobado > decisión particular. Una propuesta no es aprobación. '
             'Lee íntegramente los documentos pertinentes enlazados antes de actuar. '
             'No leas secretos ni archivos fuera del workspace, salvo política, perfiles y skills del motor.']
    if operation:
        parts.append('SPEC KIT: conserva la constitución local y sus enlaces a guías y ADRs al enmendarla; '
                     'no sustituyas decisiones aprobadas por el contenido de una propuesta o un plan. '
                     'Su existencia no prueba Brownfield ni aprobación. Nunca edites la política global.')
    if policy.is_file():
        parts.append('POLÍTICA GLOBAL: ' + policy.as_posix())
        if not compact:
            if policy.stat().st_size > MAX_FILE:
                raise ConfigurationError('Framework policy exceeds context limit.')
            text = policy.read_text(encoding='utf-8-sig')
            if len(text) <= 7000:
                parts.append(text)
    paths = document_index(context, role, operation)
    if PROJECT_CONSTITUTION not in paths:
        parts.append('Constitución local pendiente. No heredar el stack del motor ni de otro proyecto.')
    for relative in paths:
        body = safe_text(context, relative)
        parts.append('DOCUMENTO LOCAL: ' + context.output(relative).as_posix())
        # Full small constitution; specialized guides are read by role/on demand.
        if relative == PROJECT_CONSTITUTION and not compact and len(body) <= 6000:
            parts.append(body)
    if role in TECHNICAL_ROLES or operation in TECHNICAL_OPERATIONS:
        found = discover(context)
        parts.append('Estado: ' + found['mode'] + '. Observaciones sin aprobación:')
        seen = set()
        for row in found['observations']:
            key = (row['technology'], row['version'])
            if key not in seen and len(seen) < (8 if compact else 35):
                parts.append(f"- {row['technology']} {row['version']} ({row['source']})")
                seen.add(key)
        if not found['observations']:
            parts.append('Stack sin detectar: consultar restricciones locales; si faltan, SA propone y solicita aprobación humana.')
        if found['differences']:
            parts.append('Diferencias con inventario documental (no modificar decisiones): ' + '; '.join(found['differences'][:10]))
        parts.extend(found['issues'][:3])
    text = '\n'.join(parts) + '\nTAREA ACTUAL:\n'
    if len(text) > MAX_PROMPT:
        raise ConfigurationError('Context index exceeds prompt budget; reduce the project index.')
    return text


def initialize_constitution(context):
    from .workspace import write_new
    write_new(context.output(PROJECT_CONSTITUTION), NEUTRAL_CONSTITUTION)
