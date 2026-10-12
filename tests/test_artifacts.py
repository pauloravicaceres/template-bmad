"""Fase 4F-E2: clasificador de artefactos de compuerta (bmad_runtime.artifacts), solo lectura y determinista."""
import json
import os
from pathlib import Path

import pytest

from bmad_runtime import artifacts
from bmad_runtime.artifacts import (AMBIGUOUS, EXTERNAL_ALLOWED, FUTURE, GATES, MISSING, OTHER_PROJECT, OUTSIDE, PRESENT,
                                    ArtifactClassifier, gate_for_author, load_policy, policy_from_config,
                                    rule_for_folder)
from bmad_runtime.config import RuntimeConfig
from bmad_runtime.errors import ConfigurationError

PA = GATES['product-analyst']
UX = GATES['designer-ux']


def project(root, identity):
    root.mkdir(parents=True, exist_ok=True)
    (root / 'project.json').write_text(json.dumps({'schema_version': 1, 'project_id': identity}), encoding='utf-8')
    return root


def write(root, relative, text='contenido'):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text(text, encoding='utf-8')
    return path


@pytest.fixture
def ws(tmp_path):
    root = project(tmp_path / 'alfa', 'alfa')
    write(root, 'docs/product-analyst/pb-reservas.md')
    return root


@pytest.fixture
def classifier(ws):
    return ArtifactClassifier(ws, project_id='alfa')


def link(target, path):
    """Symlink, or a junction for directories on Windows without symlink privilege; None when impossible."""
    try:
        os.symlink(target, path, target_is_directory=Path(target).is_dir())
        return path
    except (OSError, NotImplementedError):
        if os.name == 'nt' and Path(target).is_dir():
            import _winapi
            _winapi.CreateJunction(str(target), str(path))
            return path
    return None


def snapshot(root):
    return sorted((str(p.relative_to(root)), p.stat().st_mtime_ns, p.stat().st_size)
                  for p in root.rglob('*') if p.is_file())


# ----------------------------------------------------------------------------- the seven statuses
def test_every_status_is_reachable(ws, classifier, tmp_path):
    project(tmp_path / 'beta', 'beta')
    write(ws, 'docs/product-analyst/old/pb-doble.md')
    write(ws, 'docs/product-analyst/pb-doble.md')
    future = 'docs/business-analyst/003-gestion-clientes.md'
    found = {
        PRESENT: classifier.classify('docs/product-analyst/pb-reservas.md', PA),
        MISSING: classifier.classify('docs/product-analyst/pb-nada.md', PA),
        FUTURE: classifier.classify(future, GATES['business-analyst'], future=(future,)),
        EXTERNAL_ALLOWED: classifier.classify('https://www.figma.com/file/AbC/Reservas', UX),
        OUTSIDE: classifier.classify('../fuera.md', PA),
        OTHER_PROJECT: classifier.classify('../beta/docs/product-analyst/pb-x.md', PA),
        AMBIGUOUS: classifier.classify('pb-doble.md', PA),
    }
    assert {status: c.status for status, c in found.items()} == {s: s for s in artifacts.STATUSES}
    assert found[OTHER_PROJECT].project == 'beta'
    assert [c.rejected for c in found.values()] == [False, False, False, False, True, True, True]


def test_classification_is_deterministic_and_read_only(ws, classifier):
    write(ws, 'docs/product-analyst/a/pb-doble.md')
    write(ws, 'docs/product-analyst/b/pb-doble.md')
    before = snapshot(ws)
    references = ('pb-doble.md', 'pb-reservas.md', '../x.md', 'nada.md')
    first = [classifier.classify(r, PA).to_dict() for r in references]
    again = [classifier.classify(r, PA).to_dict() for r in references]
    assert first == again and snapshot(ws) == before
    assert first[0]['candidates'] == ['docs/product-analyst/a/pb-doble.md', 'docs/product-analyst/b/pb-doble.md']


def test_the_classifier_imports_no_network_or_write_capability():
    import ast
    tree = ast.parse(Path(artifacts.__file__).read_text(encoding='utf-8'))
    imported = {alias.name.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.Import)
                for alias in node.names}
    imported |= {node.module.split('.')[0] for node in ast.walk(tree) if isinstance(node, ast.ImportFrom) and node.module}
    assert not imported & {'socket', 'http', 'requests', 'httpx', 'shutil', 'subprocess', 'tempfile'}
    assert 'urlopen' not in Path(artifacts.__file__).read_text(encoding='utf-8')
    source = Path(artifacts.__file__).read_text(encoding='utf-8')
    assert not any(call in source for call in ('.write_', '.unlink(', '.mkdir(', '.rename(', 'open('))


def test_resolution_ignores_the_process_cwd(ws, tmp_path, monkeypatch):
    elsewhere = tmp_path / 'cwd'
    write(elsewhere, 'docs/product-analyst/pb-cwd.md')
    monkeypatch.chdir(elsewhere)
    result = ArtifactClassifier(ws).classify('docs/product-analyst/pb-cwd.md', PA)
    assert (result.status, result.path) == (MISSING, 'docs/product-analyst/pb-cwd.md')


# ----------------------------------------------------------------------------- paths
@pytest.mark.parametrize('reference', ['docs/product-analyst/pb-reservas.md', 'docs\\product-analyst\\pb-reservas.md',
                                       './docs//product-analyst/./pb-reservas.md', '`docs/product-analyst/pb-reservas.md`',
                                       'docs/product-analyst/../product-analyst/pb-reservas.md'])
def test_windows_and_posix_separators_resolve_to_one_normalized_path(classifier, reference):
    result = classifier.classify(reference, PA)
    assert (result.status, result.path, result.in_gate_dirs) == (PRESENT, 'docs/product-analyst/pb-reservas.md', True)


def test_absolute_paths_only_inside_the_workspace(ws, classifier, tmp_path):
    inside = classifier.classify(str(ws / 'docs' / 'product-analyst' / 'pb-reservas.md'), PA)
    assert (inside.status, inside.path) == (PRESENT, 'docs/product-analyst/pb-reservas.md')
    write(tmp_path, 'suelto/pb-fuera.md')
    outside = classifier.classify(str(tmp_path / 'suelto' / 'pb-fuera.md'), PA)
    assert (outside.status, outside.reason) == (OUTSIDE, 'escapes_workspace')


@pytest.mark.parametrize('reference, reason', [
    ('../fuera.md', 'escapes_workspace'),
    ('docs/../../fuera.md', 'escapes_workspace'),
    ('..\\..\\Windows\\system.ini', 'escapes_workspace'),
    ('\\\\servidor\\recurso\\pb.md', 'unc_path'),
    ('//servidor/recurso/pb.md', 'unc_path'),
    ('\\\\?\\C:\\pb.md', 'unc_path'),
    ('C:docs\\pb.md', 'drive_relative'),
    ('docs/product-analyst/pb-reservas.md:oculto', 'invalid_characters'),
    ('docs/pb\x00.md', 'invalid_characters'),
    ('file:///etc/passwd', 'external_not_allowed'),
])
def test_escapes_and_foreign_forms_are_outside(classifier, reference, reason):
    result = classifier.classify(reference, PA)
    assert (result.status, result.reason) == (OUTSIDE, reason) and result.rejected and result.warnings() == []


@pytest.mark.skipif(os.name != 'nt', reason='Windows-only path forms')
def test_rooted_path_without_drive_is_outside_on_windows(classifier):
    assert classifier.classify('/docs/product-analyst/pb-reservas.md', PA).reason == 'rooted_without_drive'


@pytest.mark.skipif(os.name == 'nt', reason='POSIX-only path forms')
def test_windows_absolute_path_is_foreign_on_posix(classifier):
    assert classifier.classify('C:\\docs\\pb.md', PA).reason == 'foreign_absolute'


def test_links_leaving_the_workspace_are_outside(ws, classifier, tmp_path):
    secret = tmp_path / 'secretos'
    write(secret, 'pb-clave.md')
    if not link(secret, ws / 'docs' / 'product-analyst' / 'enlace'):
        pytest.skip('no symlink/junction support')
    result = classifier.classify('docs/product-analyst/enlace/pb-clave.md', PA)
    assert (result.status, result.reason) == (OUTSIDE, 'link_outside_workspace')
    assert classifier.classify('docs/product-analyst/enlace/no-existe.md', PA).status == OUTSIDE
    assert classifier.classify('pb-clave.md', PA).status == MISSING, 'a bare-name search never enters links'


def test_links_inside_the_workspace_resolve_to_the_real_path(ws, classifier):
    if not link(ws / 'docs' / 'product-analyst', ws / 'docs' / 'atajo'):
        pytest.skip('no symlink/junction support')
    result = classifier.classify('docs/atajo/pb-reservas.md', PA)
    assert (result.status, result.path) == (PRESENT, 'docs/product-analyst/pb-reservas.md')


def test_empty_files_and_directories(ws, classifier):
    write(ws, 'docs/product-analyst/pb-vacio.md', '')
    empty = classifier.classify('docs/product-analyst/pb-vacio.md', PA)
    assert (empty.status, empty.empty) == (PRESENT, True)
    assert [w['code'] for w in empty.warnings()] == ['ARTIFACT_EMPTY']
    folder = classifier.classify('docs/product-analyst', PA)
    assert (folder.status, folder.reason) == (MISSING, 'not_a_file')
    assert [w['code'] for w in folder.warnings()] == ['ARTIFACT_NOT_A_FILE']
    assert classifier.classify('docs/product-analyst/', PA).reason == 'not_a_file'


def test_paths_outside_the_gate_directories_warn(ws, classifier):
    write(ws, 'notas/pb-suelto.md')
    result = classifier.classify('notas/pb-suelto.md', PA)
    assert (result.status, result.in_gate_dirs) == (PRESENT, False)
    assert [w['code'] for w in result.warnings()] == ['ARTIFACT_OUTSIDE_GATE_DIRS']


# ----------------------------------------------------------------------------- other projects
def test_other_projects_by_project_json_and_registry(ws, tmp_path):
    beta = project(tmp_path / 'beta', 'beta')
    write(beta, 'docs/product-analyst/pb-beta.md')
    gamma = tmp_path / 'gamma'
    write(gamma, 'docs/pb-gamma.md')
    classifier = ArtifactClassifier(ws, project_id='alfa', registry={'gamma': gamma, 'alfa': ws})
    by_marker = classifier.classify(str(beta / 'docs' / 'product-analyst' / 'pb-beta.md'), PA)
    by_registry = classifier.classify('../gamma/docs/pb-gamma.md', PA)
    assert (by_marker.status, by_marker.project) == (OTHER_PROJECT, 'beta')
    assert (by_registry.status, by_registry.project) == (OTHER_PROJECT, 'gamma')
    unknown = classifier.classify(str(tmp_path / 'sin-proyecto' / 'pb.md'), PA)
    assert unknown.status == OUTSIDE, 'without proof of ownership it is only outside'


def test_a_project_nested_in_the_workspace_is_another_project(tmp_path):
    engine = tmp_path / 'motor'                       # legacy workspace = engine root, with a registered child
    child = project(engine / 'clientes' / 'beta', 'beta')
    write(child, 'docs/product-analyst/pb-beta.md')
    write(engine, 'docs/product-analyst/pb-motor.md')
    classifier = ArtifactClassifier(engine, project_id='legacy', registry={'beta': child})
    nested = classifier.classify('clientes/beta/docs/product-analyst/pb-beta.md', PA)
    assert (nested.status, nested.project) == (OTHER_PROJECT, 'beta')
    assert classifier.classify('docs/product-analyst/pb-motor.md', PA).status == PRESENT
    unregistered = project(engine / 'otros' / 'delta', 'delta')
    write(unregistered, 'docs/pb.md')
    assert classifier.classify('otros/delta/docs/pb.md', PA).project == 'delta'


def test_the_engine_root_is_not_the_project(tmp_path):
    engine = tmp_path / 'motor'
    write(engine, 'docs/product-analyst/pb-motor.md')
    ws = project(tmp_path / 'ws', 'alfa')
    result = ArtifactClassifier(ws, engine_root=engine).classify(str(engine / 'docs/product-analyst/pb-motor.md'), PA)
    assert (result.status, result.reason) == (OUTSIDE, 'engine_root')


# ----------------------------------------------------------------------------- bare names
def test_bare_names_search_only_the_gate_directories(ws, classifier):
    write(ws, 'docs/product-manager/pb-ajeno.md')
    write(ws, 'pb-raiz.md')
    assert classifier.classify('pb-reservas.md', PA).path == 'docs/product-analyst/pb-reservas.md'
    assert classifier.classify('pb-ajeno.md', PA).status == MISSING
    assert classifier.classify('pb-raiz.md', PA).status == MISSING
    write(ws, 'docs/product-analyst/v2/pb-reservas.md')
    ambiguous = classifier.classify('pb-reservas.md', PA)
    assert (ambiguous.status, ambiguous.reason) == (AMBIGUOUS, 'several_matches')
    assert ambiguous.candidates == ('docs/product-analyst/pb-reservas.md', 'docs/product-analyst/v2/pb-reservas.md')


def test_bare_name_search_is_bounded(ws):
    for i in range(30):
        write(ws, f'docs/product-analyst/a{i:02d}.md')
    bounded = ArtifactClassifier(ws, max_entries=10)
    missing = bounded.classify('zz-no-existe.md', PA)
    assert missing.status == MISSING and [w['code'] for w in missing.warnings()][-1] == 'ARTIFACT_SEARCH_TRUNCATED'
    unprovable = bounded.classify('a03.md', PA)
    assert (unprovable.status, unprovable.reason) == (AMBIGUOUS, 'search_truncated')
    write(ws, 'docs/product-analyst/1/2/3/pb-hondo.md')
    assert ArtifactClassifier(ws, max_depth=1).classify('pb-hondo.md', PA).status == MISSING


# ----------------------------------------------------------------------------- URLs
@pytest.mark.parametrize('url', ['https://www.figma.com/file/AbC123/Reservas?node-id=1-2',
                                 'https://figma.com/design/AbC123/Reservas', 'https://FIGMA.com/file/x',
                                 'https://www.figma.com:443/file/x'])
def test_figma_https_urls_are_external_allowed_in_ux(classifier, url):
    result = classifier.classify(url, UX)
    assert (result.status, result.url, result.cited) == (EXTERNAL_ALLOWED, url, url)


@pytest.mark.parametrize('url, reason', [
    ('http://www.figma.com/file/x', 'scheme_not_allowed'),
    ('ftp://figma.com/x', 'scheme_not_allowed'),
    ('https://evilfigma.com/file/x', 'host_not_allowed'),
    ('https://figma.com.evil.com/file/x', 'host_not_allowed'),
    ('https://api.figma.com/v1/files', 'host_not_allowed'),
    ('https://www.figma.co/file/x', 'host_not_allowed'),
    ('https://user:clave@figma.com/file/x', 'credentials'),
    ('https://figma.com@evil.com/file/x', 'credentials'),
    ('https://www.figma.com\\@evil.com/x', 'invalid_url'),
    ('https://figma.com:8443/file/x', 'port_not_allowed'),
    ('https://xn--fgma-wqa.com/file/x', 'host_not_allowed'),
    ('https://fígma.com/file/x', 'invalid_host'),
    ('https://[::1]/file/x', 'invalid_host'),
])
def test_invalid_or_unauthorized_urls_are_outside(classifier, url, reason):
    result = classifier.classify(url, UX)
    assert (result.status, result.reason) == (OUTSIDE, reason)


def test_urls_are_rejected_in_gates_without_an_allowlist(classifier):
    for gate in sorted(set(GATES) - {'designer-ux'}):
        assert classifier.classify('https://www.figma.com/file/x', GATES[gate]).reason == 'external_not_allowed'
    assert classifier.classify('https://www.figma.com/file/x').reason == 'external_not_allowed'


# ----------------------------------------------------------------------------- FUTURE
def test_future_only_for_the_exact_path_an_explicit_rule_authorizes(ws, classifier):
    ba = GATES['business-analyst']
    planned = 'docs/business-analyst/003-gestion-clientes.md'
    assert classifier.classify(planned, ba, future=(planned,)).status == FUTURE
    assert classifier.classify(planned, ba).status == MISSING, 'never a fallback for absent files'
    assert classifier.classify('docs/business-analyst/004-otra.md', ba, future=(planned,)).status == MISSING
    assert classifier.classify('003-gestion-clientes.md', ba, future=(planned,)).status == FUTURE
    write(ws, planned)
    assert classifier.classify(planned, ba, future=(planned,)).status == PRESENT
    assert classifier.classify('../x.md', ba, future=('../x.md',)).status == OUTSIDE


# ----------------------------------------------------------------------------- warnings, rules, policy
def test_structured_warning_fields(classifier):
    [warning] = classifier.classify('docs/product-analyst/pb-nada.md', PA).warnings()
    assert warning == {'code': 'ARTIFACT_MISSING', 'status': MISSING, 'reference': 'docs/product-analyst/pb-nada.md',
                       'path': 'docs/product-analyst/pb-nada.md', 'gate': 'product-analyst', 'reason': 'not_found',
                       'detail': 'docs/product-analyst/pb-nada.md no existe en el workspace.'}


def test_gate_rules_cover_the_control_center_authors():
    for author, gate in [('Business Storyteller', 'business-storyteller'), ('PA', 'product-analyst'),
                         ('Product Manager', 'product-manager'), ('BA', 'business-analyst'),
                         ('QA Documental', 'qa-documental'), ('Designer UX', 'designer-ux'),
                         ('Solutions Architect', 'solutions-architect'), ('QA-Tech Senior', 'qa-tech')]:
        assert gate_for_author(author).gate == gate
    assert gate_for_author('Data Architect') is None
    assert rule_for_folder('dev-backend').dirs == ('docs/dev-backend',)


def test_policy_defaults_overrides_and_enforce_refused(tmp_path):
    assert policy_from_config(None) == {'mode': 'warn',
                                        'external_hosts': {'designer-ux': ('figma.com', 'www.figma.com')}}
    custom = policy_from_config({'external_hosts': {'designer-ux': [], 'qa-tech': ['docs.example.com']}})
    assert gate_for_author('UX', custom).external_hosts == ()
    assert gate_for_author('QT', custom).external_hosts == ('docs.example.com',)
    for bad in ({'mode': 'enforce'}, {'mode': 'strict'}, {'otro': 1}, {'external_hosts': {'nadie': []}},
                {'external_hosts': {'designer-ux': ['*.figma.com']}},
                {'external_hosts': {'designer-ux': ['https://figma.com']}}):
        with pytest.raises(ConfigurationError):
            policy_from_config(bad)
    (tmp_path / 'config_bmad.json').write_text(json.dumps({'ai': {'artifacts': {'mode': 'off'}}}), encoding='utf-8')
    assert load_policy(tmp_path)['mode'] == 'off'
    assert RuntimeConfig.load(tmp_path).data['artifacts']['mode'] == 'off'
    assert load_policy(tmp_path / 'sin-config')['mode'] == 'warn'
