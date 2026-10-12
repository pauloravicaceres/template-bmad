"""Fase 4F-E4.1: auditoría fail-closed de enforce y recuperación GitOps con repositorios Git temporales reales."""
import json
import sqlite3
import subprocess
from unittest.mock import Mock, patch

import pytest

from bmad_runtime import hu_enforcement, hu_lifecycle, watcher_service, workflow
from bmad_runtime.context import ProjectContext
from bmad_runtime.errors import ConfigurationError, ReconciliationRequired
from bmad_runtime.hu_enforcement import ALLOWED, RECONCILE, UNKNOWN, Enforcer, preflight
from bmad_runtime.hu_lifecycle import AUTHORITY, load_policy
from bmad_runtime.watcher_service import TrackerSnapshot
from tests.test_hu_enforcement import (Crash, HU_C, acknowledge, append, ask, authority, ba_handoffs, branches,
                                       checkout, enforcer, make_watcher, merger, open_a, open_hu, rejected_ops,
                                       request, run, unfinished_events)
from tests.test_hu_lifecycle import HU_A, HU_B, Project, git

__all__ = ['make_watcher']           # fixture reutilizada


@pytest.fixture
def project(tmp_path):
    item = Project(tmp_path)
    yield item
    item.store.close()


def no_git_change(project, decision, create):
    assert decision.rejected and not create.called
    assert [b for b in branches(project.root) if b.startswith('feat/')] == []


# --------------------------------------------------------------- 2. invariante fail-closed (watcher y preflight)
FAILURES = {
    'observer_exception': lambda: patch.object(hu_enforcement, 'observe', side_effect=RuntimeError('boom')),
    'git_timeout': lambda: patch.object(hu_lifecycle.subprocess, 'run',
                                        side_effect=subprocess.TimeoutExpired('git', 20)),
    'git_unavailable': lambda: patch.object(hu_lifecycle.subprocess, 'run', side_effect=FileNotFoundError('git')),
    'sqlite_unqueryable': lambda: patch.object(hu_lifecycle, '_previous_records',
                                               side_effect=sqlite3.OperationalError('database is locked')),
    'tracker_unstable': lambda: patch.object(watcher_service, 'read_tracker',
                                             return_value=TrackerSnapshot([], None, False)),
    'tracker_unreadable': lambda: patch.object(watcher_service, 'read_tracker',
                                               return_value=TrackerSnapshot([], None, True, 'invalid_utf8')),
}


@pytest.mark.parametrize('failure', sorted(FAILURES))
def test_any_observation_failure_blocks_the_watcher_opening(project, failure):
    number, key = request(project, 'open', HU_A)
    create = Mock()
    with FAILURES[failure]():
        decision = enforcer(project).open(key, number, f'feat/{HU_A}', create)
    assert (decision.code, decision.status) == (UNKNOWN, 'unknown')
    no_git_change(project, decision, create)
    assert authority(project) == {}                          # nada reservado


@pytest.mark.parametrize('failure', sorted(FAILURES))
def test_any_observation_failure_blocks_the_preflight(project, failure):
    with FAILURES[failure]():
        decision = preflight(project.context, HU_A)
    assert decision.rejected and decision.code == UNKNOWN


def test_corrupt_sqlite_blocks_the_preflight(project):
    project.store.close()
    (project.context.state_dir / 'state.sqlite3').write_bytes(b'esto no es sqlite' * 64)
    try:
        assert preflight(project.context, HU_A).code == UNKNOWN
    finally:
        project.store = Mock()


def test_unknown_reconcile_and_contradictory_evidence_block(project):
    git(project.root, 'branch', f'feat/{HU_C}')
    assert ask(project, 'open', HU_A).code == UNKNOWN                      # observación unknown
    git(project.root, 'branch', '-D', f'feat/{HU_C}')
    open_hu(project, HU_A)
    project.merge(HU_A, delete=False)
    assert ask(project, 'open', HU_B).code == RECONCILE                    # reconcile_required


def test_reservation_contradicting_git_blocks(project):
    open_hu(project, HU_A)
    project.store.put(AUTHORITY, {**authority(project), 'hu': HU_C, 'branch': f'feat/{HU_C}'})
    decision = ask(project, 'open', HU_B)
    assert decision.code == RECONCILE and 'authority_observation_mismatch' in decision.causes


def test_observation_failure_between_preflight_and_watcher_blocks(project):
    assert preflight(project.context, HU_A).code == ALLOWED
    number, key = request(project, 'open', HU_A)
    create = Mock()
    with patch.object(hu_lifecycle.subprocess, 'run', side_effect=subprocess.TimeoutExpired('git', 20)):
        decision = enforcer(project).open(key, number, f'feat/{HU_A}', create)
    no_git_change(project, decision, create)


def test_observe_mode_stays_non_blocking_when_the_observer_fails(make_watcher, tmp_path):
    rt = make_watcher('observe')
    create = Mock(side_effect=lambda branch: git(tmp_path, 'checkout', '-q', '-b', branch))
    with patch.object(hu_lifecycle, 'observe', side_effect=RuntimeError('boom')):
        run(rt, tmp_path, [open_a(rt), lambda: None], create=create)
    create.assert_called_once_with(f'feat/{HU_A}')


# Defecto confirmado 1: una rama feat/ con nombre inválido y trabajo sin integrar puede ser una HU abierta fuera del
# contrato; E3 la ignoraba y enforce declaraba el proyecto libre.
def test_unmerged_invalid_feature_branch_blocks_openings(project):
    git(project.root, 'checkout', '-q', '-b', 'feat/HU-007_Pagos')
    project.commit('feat/HU-007_Pagos', 'pagos.txt', 'trabajo\n')
    git(project.root, 'checkout', '-q', 'main')
    decision = ask(project, 'open', HU_A)
    assert decision.code == UNKNOWN and 'unattributed_feature_branch:feat/HU-007_Pagos' in decision.causes
    assert preflight(project.context, HU_A).code == UNKNOWN
    assert project.observe()['status'] == 'no_open_hu'           # observe no cambia: solo enforce bloquea


def test_integrated_invalid_feature_branch_does_not_block(project):
    git(project.root, 'branch', 'feat/HU-007_Pagos')                # sin commits propios: nada abierto
    assert ask(project, 'open', HU_A).code == ALLOWED


# Defecto confirmado 2: un project.json ilegible desactivaba en silencio el preflight de un proyecto en enforce.
def test_unreadable_project_json_never_falls_back_to_the_engine_policy(tmp_path):
    engine, workspace = tmp_path / 'engine', tmp_path / 'ws'
    engine.mkdir()
    workspace.mkdir()
    (engine / 'config_bmad.json').write_text(json.dumps({'ai': {}}), encoding='utf-8')
    context = ProjectContext(engine, workspace, 'iso')
    assert load_policy(context) == {'mode': 'observe'}                      # sin project.json: config del motor
    (workspace / 'project.json').write_text('{"config": {"ai": {"hu_lifecycle": {"mode": "enf', encoding='utf-8')
    with pytest.raises(ConfigurationError):
        load_policy(context)


# Defecto confirmado 3: un evento E4 terminado sin operación confirmada (p. ej. cierre en conflicto reconocido y
# fusionado a mano) se observaba como `closed` por el mensaje de merge.
def test_acknowledged_unconfirmed_close_is_never_observed_as_closed(project):
    open_hu(project, HU_A)
    project.commit(f'feat/{HU_A}', 'README.md', 'rama\n')
    project.commit('main', 'README.md', 'base cambiada\n')
    number, key = request(project, 'close', HU_A)
    with pytest.raises(SystemExit):
        enforcer(project).close(key, number, f'feat/{HU_A}', merger(project))
    acknowledge(project.store, key)
    git(project.root, 'checkout', '-q', 'main')
    git(project.root, 'merge', '--no-ff', '--no-edit', '-X', 'ours', f'feat/{HU_A}')
    git(project.root, 'branch', '-d', f'feat/{HU_A}')
    data = project.observe()['hus'][HU_A]
    assert data['observed_state'] == 'reconcile_required' and 'close_unconfirmed' in data['causes']


def test_acknowledged_unverified_opening_is_never_observed_as_active(project):
    number, key = request(project, 'open', HU_A)
    with pytest.raises(ReconciliationRequired):          # rama creada sin dejar HEAD en ella: no verificable
        enforcer(project).open(key, number, f'feat/{HU_A}',
                               lambda branch: git(project.root, 'branch', branch))
    acknowledge(project.store, key)
    data = project.observe()['hus'][HU_A]
    assert data['observed_state'] == 'reconcile_required' and 'open_unconfirmed' in data['causes']
    assert ask(project, 'open', HU_B).code == RECONCILE


# --------------------------------------------------------------- 3. recuperación tras caída (sin Git destructivo)
def test_recovery_never_writes_git_and_is_idempotent(project):
    open_hu(project, HU_A)
    number, key = request(project, 'close', HU_A)

    def merge_then_crash(branch):
        merger(project)(branch)
        raise Crash()

    with patch.object(Enforcer, '_close_failed'), pytest.raises(Crash):
        enforcer(project).close(key, number, f'feat/{HU_A}', merge_then_crash)
    before = project.git_state()
    assert enforcer(project).recover()['outcome'] == 'close_interrupted_after_merge'
    assert enforcer(project).recover() is None and project.git_state() == before
    assert authority(project)['state'] == 'reconcile_required'
    assert project.observe()['hus'][HU_A]['observed_state'] != 'closed'


def test_recovery_with_contradictory_git_evidence_requires_reconciliation(project):
    open_hu(project, HU_A)
    number, key = request(project, 'close', HU_A)
    with patch.object(Enforcer, '_close_failed'), pytest.raises(Crash):
        enforcer(project).close(key, number, f'feat/{HU_A}', Mock(side_effect=Crash()))
    project.commit('main', 'otro.txt', 'la base se movió sin integrar la HU\n')
    assert enforcer(project).recover()['outcome'] == 'close_interrupted_unclear'
    assert authority(project)['state'] == 'reconcile_required'


def test_recovery_of_a_resumed_opening_whose_branch_disappeared(project):
    open_hu(project, HU_A)
    number, key = request(project, 'open', HU_A)

    def delete_then_crash(branch):
        git(project.root, 'checkout', '-q', 'main')
        git(project.root, 'branch', '-q', '-D', branch)
        raise Crash()

    with patch.object(Enforcer, '_open_failed'), pytest.raises(Crash):
        enforcer(project).open(key, number, f'feat/{HU_A}', delete_then_crash)
    assert enforcer(project).recover()['outcome'] == 'branch_disappeared'
    assert authority(project)['state'] == 'reconcile_required'


def test_unreadable_git_during_recovery_keeps_the_reservation(project):
    number, key = request(project, 'open', HU_A)
    with patch.object(Enforcer, '_open_failed'), pytest.raises(Crash):
        enforcer(project).open(key, number, f'feat/{HU_A}', Mock(side_effect=Crash()))
    with patch.object(hu_lifecycle.subprocess, 'run', side_effect=FileNotFoundError('git')):
        assert enforcer(project).recover()['outcome'] == 'git_unreadable'
    assert authority(project)['state'] == 'opening'
    assert ask(project, 'open', HU_B).code == 'HU_OPENING_IN_PROGRESS'


# --------------------------------------------------------------- 4. D5 con interrupción y acknowledge de todo
def acknowledge_all(rt):
    for key, raw in list(rt.state.db.execute(
            "SELECT id,data FROM records WHERE id LIKE 'event:%' OR id LIKE 'queued:%'")):
        if json.loads(raw)['state'] != 'done':
            acknowledge(rt.state, key)


def d5(rt):
    return append(rt, 'HUMANO', '- **Estado:** APPROVE', f'- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/{HU_B}',
                  f'@BA: La rama feat/{HU_B} ha sido creada. Procede.')


def test_d5_interrupted_then_everything_acknowledged_never_dispatches(make_watcher, tmp_path):
    rt = make_watcher('enforce')
    # Caída justo al retener la línea @BA: su evento queda in_flight antes de suprimirse.
    with patch.object(Enforcer, 'suppress', side_effect=RuntimeError('caída')):
        run(rt, tmp_path, [open_a(rt), d5(rt), lambda: None, lambda: None], expect=ReconciliationRequired)
    assert len(unfinished_events(rt)) == 1
    rt = make_watcher('enforce')
    run(rt, tmp_path, [], expect=ReconciliationRequired)                 # in_flight: se detiene sin despachar
    acknowledge_all(rt)                                                  # el operador reconoce todo lo pendiente
    for _ in range(2):                                                   # y reanuda (dos veces)
        rt = make_watcher('enforce')
        run(rt, tmp_path, [lambda: None, lambda: None])
    assert ba_handoffs(rt) == [] and f'feat/{HU_B}' not in branches(tmp_path)
    [op] = rejected_ops(rt)
    assert (op['state'], op['notice']['state']) == ('rejected', 'delivered')
    assert rt.context.tracker_path.read_text(encoding='utf-8').count('HU BLOQUEADA') == 1
    assert rt.state.get(AUTHORITY)['hu'] == HU_A and unfinished_events(rt) == []


def pm_handoffs(rt):
    return [key for key, raw in rt.state.db.execute("SELECT id,data FROM records WHERE id LIKE 'queued:%'")
            if json.loads(raw).get('agent_id') == 'product-manager' and json.loads(raw).get('outcome') != 'suppressed']


def test_acknowledged_in_flight_close_never_dispatches_its_block(make_watcher, tmp_path):
    rt = make_watcher('enforce')
    run(rt, tmp_path, [open_a(rt), lambda: None])
    close = append(rt, 'Code Review', f'- **Handoff:** @WATCHER: GITOPS-MERGE-CLOSE feat/{HU_A}',
                   '@PM: HU cerrada; continúa con la siguiente épica.')
    with patch.object(workflow, 'confirmar_cierre_rama'), \
            patch.object(workflow, 'fusionar_rama', side_effect=SystemExit(1)):     # conflicto: merge abortado
        run(rt, tmp_path, [close, lambda: None, lambda: None], expect=SystemExit)
    assert rt.state.get(AUTHORITY)['state'] == 'reconcile_required'
    rt = make_watcher('enforce')
    run(rt, tmp_path, [], expect=ReconciliationRequired)
    acknowledge_all(rt)
    rt = make_watcher('enforce')
    run(rt, tmp_path, [d5(rt), lambda: None, lambda: None])
    assert pm_handoffs(rt) == [] and ba_handoffs(rt) == []
    assert rt.state.get(AUTHORITY)['state'] == 'reconcile_required'
    assert [op['decision']['code'] for op in rejected_ops(rt)] == [RECONCILE]
    assert f'feat/{HU_A}' in branches(tmp_path) and f'feat/{HU_B}' not in branches(tmp_path)


# --------------------------------------------------------------- 5. concurrencia: reintento de la misma HU
def test_retrying_the_same_hu_never_duplicates(project):
    open_hu(project, HU_A)
    calls = []
    for _ in range(3):
        number, key = request(project, 'open', HU_A)
        assert enforcer(project).open(key, number, f'feat/{HU_A}', checkout(project, calls)).code == 'HU_OPEN_RESUME'
        project.store.finish(key, 'done')
    assert [b for b in branches(project.root) if b.startswith('feat/')] == [f'feat/{HU_A}']
    assert authority(project)['hu'] == HU_A and len(calls) == 3
