"""Fase 4F-E2: utils/approve_step.py ubica el entregable con el clasificador compartido (bmad_runtime.artifacts)."""
import json
from pathlib import Path
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from utils import approve_step

ENGINE = Path(approve_step.__file__).resolve().parents[1]


@pytest.fixture
def ws(tmp_path):
    root = tmp_path / 'alfa'
    (root / 'docs').mkdir(parents=True)
    (root / 'project.json').write_text(json.dumps({'schema_version': 1, 'project_id': 'alfa'}), encoding='utf-8')
    return root


def run(ws, tracker_text, answers):
    tracker = ws / 'docs' / 'tracker_bmad.md'
    tracker.write_text(tracker_text, encoding='utf-8')
    context = SimpleNamespace(workspace_root=ws, tracker_path=tracker, project_id='alfa', engine_root=ENGINE)
    config = {key: dict(value) for key, value in approve_step.APPROVAL_CONFIG.items()}
    with patch('bmad_runtime.context.resolve_context', return_value=context), \
            patch.object(approve_step, 'APPROVAL_CONFIG', config), \
            patch.object(approve_step, 'DIRECTORIO_RAIZ', approve_step.DIRECTORIO_RAIZ), \
            patch.object(approve_step, 'TRACKER_PATH', approve_step.TRACKER_PATH), \
            patch.object(approve_step, 'abrir_archivo_en_so') as opened, \
            patch('builtins.input', side_effect=answers), patch('builtins.print') as printed:
        try:
            approve_step.main([])
            code = 0
        except SystemExit as exc:
            code = exc.code
    output = '\n'.join(' '.join(str(a) for a in call.args) for call in printed.call_args_list)
    return code, tracker.read_text(encoding='utf-8'), opened, output


def write(root, relative):
    path = root / relative
    path.parent.mkdir(parents=True, exist_ok=True)
    path.write_text('contenido', encoding='utf-8')


def test_a_present_artifact_is_opened_and_its_resolved_path_recorded(ws):
    write(ws, 'docs/product-analyst/pb-reservas.md')
    code, text, opened, _ = run(ws, '- **Artefacto generado:** `docs/product-analyst/pb-reservas.md`\n', ['2', 's'])
    assert code == 0
    opened.assert_called_once_with(ws / 'docs/product-analyst/pb-reservas.md')
    assert '- **Artefacto generado:** `docs/product-analyst/pb-reservas.md`\n- **Estado:** APPROVE' in text
    assert '@PM: El Product Brief ha sido auditado y aprobado formalmente en el archivo pb-reservas.md' in text


def test_a_missing_artifact_warns_and_keeps_the_previous_flow(ws):
    code, text, opened, output = run(ws, 'cita pb-reservas.md\n', ['2', 's'])
    assert code == 0 and not opened.called
    assert '[ARTIFACT_MISSING]' in output and text.count('] HUMANO') == 1


def test_ambiguous_names_ask_for_the_exact_path_never_the_first_match(ws):
    write(ws, 'docs/product-analyst/pb-reservas.md')
    write(ws, 'docs/product-analyst/v2/pb-reservas.md')
    code, text, opened, output = run(ws, 'cita pb-reservas.md\n', ['2', 'docs/product-analyst/v2/pb-reservas.md', 's'])
    assert code == 0 and 'coincide con 2 archivo(s)' in output
    opened.assert_called_once_with(ws / 'docs/product-analyst/v2/pb-reservas.md')
    assert '`docs/product-analyst/v2/pb-reservas.md`' in text
    original = 'cita pb-reservas.md\n'
    code, text, _, _ = run(ws, original, ['2', ''])
    assert code == 1 and text == original


@pytest.mark.parametrize('manual', ['../beta/docs/product-analyst/pb-x.md', '../../fuera/pb-x.md'])
def test_outside_and_other_project_references_are_rejected_without_writing(ws, manual):
    beta = ws.parent / 'beta'
    (beta / 'docs').mkdir(parents=True)
    (beta / 'project.json').write_text(json.dumps({'schema_version': 1, 'project_id': 'beta'}), encoding='utf-8')
    original = 'sin artefactos\n'
    code, text, opened, output = run(ws, original, ['2', manual])
    assert code == 1 and text == original and not opened.called
    assert 'Artefacto rechazado' in output


def test_external_figma_reference_is_not_opened(ws):
    url = 'https://www.figma.com/file/AbC/Reservas'
    code, text, opened, output = run(ws, 'sin artefactos\n', ['8', url, 's'])
    assert code == 0 and not opened.called and url in output
    assert f'`{url}`' in text
