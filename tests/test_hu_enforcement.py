"""Fase 4F-E4: una HU abierta por proyecto (modo enforce) con repositorios Git temporales reales y workspaces aislados."""
import io
import json
import re
import threading
from contextlib import redirect_stdout
from unittest.mock import Mock, patch

import pytest

from bmad_runtime import hu_enforcement, hu_lifecycle, workflow
from bmad_runtime.commands import Result
from bmad_runtime.config import RuntimeConfig
from bmad_runtime.context import ProjectContext
from bmad_runtime.errors import ReconciliationRequired
from bmad_runtime.hu_enforcement import (ALLOWED, ANOTHER_OPEN, CLOSE_ALLOWED, CLOSE_MISMATCH, CLOSING, OPENING,
                                         RECONCILE, RESUME, SHARED, UNKNOWN, Enforcer, hu_lock, preflight, reconcile)
from bmad_runtime.hu_lifecycle import AUTHORITY, GATE, RESOLUTION_PREFIX, load_policy, op_key_for
from bmad_runtime.providers import default_registry
from bmad_runtime.runtime import Runtime
from bmad_runtime.state import StateStore, project_lock
from bmad_runtime.tracker_io import TrackerWriter
from bmad_runtime.watcher_service import read_tracker
from tests.test_hu_lifecycle import HU_A, HU_B, ROOT, Project, git, rows
from tests.test_tracker_integrity import FakeProvider
from tests.test_tracker_io import run_watcher

HU_C = '003-reportes-ventas'


class Crash(BaseException):
    """El proceso muere: ningún manejador de errores del enforcer llega a correr."""


# ----------------------------------------------------------------------------------------------- helpers
@pytest.fixture
def project(tmp_path):
    item = Project(tmp_path)
    yield item
    item.store.close()


def enforcer(project, store=None, **options):
    options.setdefault('writer', lambda: TrackerWriter.for_context(project.context))
    return Enforcer(project.context, store or project.store, sleep=lambda _s: None, **options)


def request(project, action, hu, *extra, author='HUMANO'):
    """Bloque con la macro (y líneas dependientes) y su evento reclamado con hu_gate, como hace el watcher."""
    macro = 'BRANCH-CREATE' if action == 'open' else 'MERGE-CLOSE'
    project.block(author, f'- **Handoff:** @WATCHER: GITOPS-{macro} feat/{hu}', *extra)
    lines = project.lines()
    number = max(i for i, line in enumerate(lines) if f'GITOPS-{macro} feat/{hu}' in line)
    key = project.event(number)
    project.store.claim(key, {GATE: action})
    return number, key


def checkout(project, calls=None):
    def create(branch):
        if calls is not None:
            calls.append(branch)
        exists = git(project.root, 'branch', '--list', branch).stdout.strip()
        git(project.root, 'checkout', '-q', *([] if exists else ['-b']), branch)
    return create


def merger(project):
    """La estrategia del watcher (fusionar_rama): --no-ff, borrar la rama; en conflicto aborta y detiene."""
    def merge(branch):
        git(project.root, 'checkout', '-q', 'main')
        if git(project.root, 'merge', '--no-ff', '--no-edit', branch, check=False).returncode:
            git(project.root, 'merge', '--abort')
            git(project.root, 'checkout', '-q', branch)
            raise SystemExit(1)
        git(project.root, 'branch', '-d', branch)
    return merge


def open_hu(project, hu, commit=True):
    number, key = request(project, 'open', hu)
    decision = enforcer(project).open(key, number, f'feat/{hu}', checkout(project))
    project.store.finish(key, 'done')               # el watcher completa la línea
    if commit and not decision.rejected:
        project.commit(f'feat/{hu}', f'{hu}.txt', f'{hu}\n')
    return decision


def ask(project, action, hu, operation=None):
    number, key = request(project, action, hu)
    gate = enforcer(project)
    if action == 'open':
        return gate.open(key, number, f'feat/{hu}', operation or checkout(project))
    return gate.close(key, number, f'feat/{hu}', operation or merger(project))


def branches(root):
    return sorted(git(root, 'for-each-ref', '--format=%(refname:short)', 'refs/heads').stdout.split())


def head(root):
    return git(root, 'symbolic-ref', '--short', 'HEAD').stdout.strip()


def authority(project):
    return project.store.get(AUTHORITY) or {}


def acknowledge(store, key):
    """Lo que hace `python -m bmad_runtime.state --acknowledge event:<id> --confirm`."""
    previous = store.get(key)['state']
    store.finish(key, 'done')
    store.put(key, {**store.get(key), 'acknowledged': 1.0, 'acknowledged_state': previous})


# ----------------------------------------------------------------------------------------- apertura
def test_first_hu_of_the_project_is_reserved_opened_and_confirmed(project):
    decision = open_hu(project, HU_A, commit=False)
    assert (decision.verdict, decision.code) == ('allow', ALLOWED)
    data = authority(project)
    assert (data['state'], data['hu'], data['branch']) == ('active', HU_A, f'feat/{HU_A}')
    assert [entry['to'] for entry in data['history']] == ['opening', 'active']
    op = project.store.get(decision.op)
    assert (op['state'], op['outcome'], op['tip_before'], op['kind']) == ('confirmed', 'opened', None, 'open')
    assert op['tip'] == git(project.root, 'rev-parse', f'feat/{HU_A}').stdout.strip()
    assert head(project.root) == f'feat/{HU_A}'


def test_same_hu_resumes_idempotently_without_opening_another(project):
    open_hu(project, HU_A)
    git(project.root, 'checkout', '-q', 'main')
    decision = open_hu(project, HU_A, commit=False)
    assert (decision.verdict, decision.code) == ('resume', RESUME)
    assert project.store.get(decision.op)['outcome'] == 'resumed'
    assert authority(project)['hu'] == HU_A and branches(project.root) == [f'feat/{HU_A}', 'main']
    assert head(project.root) == f'feat/{HU_A}'


def test_second_hu_is_rejected_without_touching_git(project):
    open_hu(project, HU_A)
    before, calls = project.git_state(), []
    number, key = request(project, 'open', HU_B)
    decision = enforcer(project).open(key, number, f'feat/{HU_B}', checkout(project, calls))
    assert (decision.verdict, decision.code, decision.open_hu) == ('reject', ANOTHER_OPEN, HU_A)
    assert calls == [] and project.git_state() == before
    op, event = project.store.get(decision.op), project.store.get(key)
    assert op['state'] == 'rejected' and op['notice']['state'] == 'pending'
    assert (event['state'], event['outcome'], event['hu_op']) == ('done', 'rejected', decision.op)
    assert authority(project)['hu'] == HU_A
    # la apertura rechazada no aparece como HU en la observación: la única abierta sigue siendo HU_A
    observation = project.observe()
    assert (observation['status'], observation['open']) == ('one_open_hu', [HU_A])
    assert observation['tracker']['excluded_macros'] == {HU_B: [number + 1]}


def test_rejection_notice_is_one_valid_watcher_block_and_idempotent(project):
    open_hu(project, HU_A)
    number, key = request(project, 'open', HU_B)
    gate = enforcer(project)
    decision = gate.open(key, number, f'feat/{HU_B}', checkout(project))
    assert gate.pending_notices() == [decision.op]
    assert gate.notify(decision.op) and not gate.notify(decision.op)
    assert gate.open(key, number, f'feat/{HU_B}', checkout(project)) == decision      # repetir no rehace nada
    text = project.context.tracker_path.read_text(encoding='utf-8')
    block = text[text.rindex('### ['):]
    assert block.splitlines()[0].endswith('] WATCHER') and '- **Handoff:** @HUMANO:' in block
    assert ANOTHER_OPEN in block and HU_A in block and decision.op in block
    assert not any(hu_lifecycle.gitops_macro(line, macro) for line in block.splitlines()
                   for macro in ('BRANCH-CREATE', 'MERGE-CLOSE'))
    assert not re.search(r'@(?!HUMANO:)[A-Z][A-Z-]*:', block)                 # ningún otro agente citado
    assert text.count('HU BLOQUEADA') == 1 and gate.pending_notices() == []


def test_unknown_state_never_authorizes_an_opening(project):
    git(project.root, 'branch', f'feat/{HU_C}')                     # rama sin historial: podría ser una HU abierta
    decision = ask(project, 'open', HU_A)
    assert (decision.code, decision.status) == (UNKNOWN, 'unknown')
    assert f'feat/{HU_A}' not in branches(project.root)


def test_failed_observation_is_unknown_never_free(project):
    with patch.object(hu_enforcement, 'observe', side_effect=RuntimeError('boom')):
        decision = ask(project, 'open', HU_A)
    assert decision.code == UNKNOWN and 'observation_failed:RuntimeError' in decision.causes


def test_workspace_without_repository_is_unknown(tmp_path):
    item = Project(tmp_path, repo=False)
    try:
        decision = ask(item, 'open', HU_A, operation=Mock())
    finally:
        item.store.close()
    assert decision.code == UNKNOWN and 'git_no_repository' in decision.causes


def test_reconcile_required_blocks_any_new_hu(project):
    open_hu(project, HU_A)
    project.merge(HU_A)                                       # fusionada y borrada fuera del watcher
    decision = ask(project, 'open', HU_B)
    assert (decision.code, decision.status) == (RECONCILE, 'reconcile_required')


def test_invalid_branch_is_rejected_without_git(project):
    project.block('HUMANO', '- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/004_mal')
    number = len(project.lines()) - 1
    key = project.event(number)
    project.store.claim(key, {GATE: 'open'})
    create = Mock()
    decision = enforcer(project).open(key, number, 'feat/004_mal', create)
    assert decision.code == hu_enforcement.INVALID and not create.called


def test_reservations_are_idempotent_per_operation(project):
    number, key = request(project, 'open', HU_A)
    gate, calls = enforcer(project), []
    first = gate.open(key, number, f'feat/{HU_A}', checkout(project, calls))
    second = gate.open(key, number, f'feat/{HU_A}', checkout(project, calls))
    assert first == second and calls == [f'feat/{HU_A}'] and first.op == op_key_for(key)
    assert [entry['to'] for entry in authority(project)['history']] == ['opening', 'active']


# ----------------------------------------------------------------------------- opening / closing interrumpidos
def test_interrupted_opening_blocks_others_and_recovers_from_git(project):
    number, key = request(project, 'open', HU_A)

    def create_then_crash(branch):
        checkout(project)(branch)
        raise Crash()

    with patch.object(Enforcer, '_open_failed'), pytest.raises(Crash):
        enforcer(project).open(key, number, f'feat/{HU_A}', create_then_crash)
    assert authority(project)['state'] == 'opening'
    assert ask(project, 'open', HU_B).code == OPENING                # una rama creada sin confirmar no deja ventana
    assert enforcer(project).recover() == {'state': 'active', 'hu': HU_A, 'outcome': 'recovered'}
    assert project.store.get(op_key_for(key))['state'] == 'confirmed'
    assert project.store.get(key)['state'] == 'in_flight'           # el evento sigue exigiendo reconocimiento humano
    assert enforcer(project).recover() is None                       # idempotente


def test_interrupted_opening_before_git_releases_the_reservation(project):
    number, key = request(project, 'open', HU_A)
    with patch.object(Enforcer, '_open_failed'), pytest.raises(Crash):
        enforcer(project).open(key, number, f'feat/{HU_A}', Mock(side_effect=Crash()))
    assert enforcer(project).recover() == {'state': 'free', 'hu': HU_A, 'outcome': 'not_executed'}
    assert project.store.get(op_key_for(key))['state'] == 'not_executed'
    assert ask(project, 'open', HU_B).code == ALLOWED


def test_failed_branch_create_without_git_change_restores_the_reservation(project):
    number, key = request(project, 'open', HU_A)
    with pytest.raises(ReconciliationRequired):
        enforcer(project).open(key, number, f'feat/{HU_A}', Mock(side_effect=ReconciliationRequired('sucio')))
    assert project.store.get(op_key_for(key))['state'] == 'failed' and authority(project)['state'] == 'free'
    acknowledge(project.store, key)                                  # reconocer no la convierte en apertura
    assert ask(project, 'open', HU_B).code == ALLOWED


def test_interrupted_closing_after_merge_requires_reconciliation(project):
    open_hu(project, HU_A)
    number, key = request(project, 'close', HU_A)

    def merge_then_crash(branch):
        merger(project)(branch)
        raise Crash()

    with patch.object(Enforcer, '_close_failed'), pytest.raises(Crash):
        enforcer(project).close(key, number, f'feat/{HU_A}', merge_then_crash)
    assert authority(project)['state'] == 'closing'
    assert ask(project, 'open', HU_B).code == CLOSING
    assert enforcer(project).recover()['outcome'] == 'close_interrupted_after_merge'
    assert authority(project)['state'] == 'reconcile_required'      # nunca closed automáticamente
    assert ask(project, 'open', HU_C).code == RECONCILE


def test_interrupted_closing_before_merge_returns_to_active(project):
    open_hu(project, HU_A)
    number, key = request(project, 'close', HU_A)
    with patch.object(Enforcer, '_close_failed'), pytest.raises(Crash):
        enforcer(project).close(key, number, f'feat/{HU_A}', Mock(side_effect=Crash()))
    assert enforcer(project).recover() == {'state': 'active', 'hu': HU_A, 'outcome': 'not_executed'}
    acknowledge(project.store, key)
    assert open_hu(project, HU_A, commit=False).code == RESUME and ask(project, 'open', HU_B).code == ANOTHER_OPEN


# ------------------------------------------------------------------------------------------------ cierre
def test_verified_merge_close_frees_the_project(project):
    open_hu(project, HU_A)
    tip = git(project.root, 'rev-parse', f'feat/{HU_A}').stdout.strip()
    number, key = request(project, 'close', HU_A, author='Code Review')
    decision = enforcer(project).close(key, number, f'feat/{HU_A}', merger(project))
    project.store.finish(key, 'done')
    assert decision.code == CLOSE_ALLOWED
    data, op = authority(project), project.store.get(decision.op)
    assert (data['state'], data['hu'], data['last_closed']['hu'], data['last_closed']['tip']) == ('free', None, HU_A, tip)
    assert (op['state'], op['outcome'], op['branch_deleted']) == ('confirmed', 'closed', True)
    assert project.observe()['status'] == 'no_open_hu'
    assert open_hu(project, HU_B).code == ALLOWED


def test_close_of_a_different_hu_is_rejected_without_merging(project):
    open_hu(project, HU_A)
    before = project.git_state()
    merge = Mock()
    decision = ask(project, 'close', HU_B, operation=merge)
    assert decision.code == CLOSE_MISMATCH and not merge.called and project.git_state() == before
    assert authority(project)['hu'] == HU_A


def test_close_not_confirmed_by_the_human_changes_nothing(project):
    open_hu(project, HU_A)
    number, key = request(project, 'close', HU_A)
    confirm = Mock(side_effect=ReconciliationRequired('Cierre de rama no confirmado.'))
    with pytest.raises(ReconciliationRequired):
        enforcer(project).close(key, number, f'feat/{HU_A}', Mock(), confirm=confirm)
    assert project.store.get(op_key_for(key))['state'] == 'not_executed' and authority(project)['state'] == 'active'
    acknowledge(project.store, key)                       # el cierre reconocido no cierra ni deja dudas
    assert project.observe()['status'] == 'one_open_hu'


def test_merge_close_conflict_keeps_reconcile_required_until_proven(project):
    open_hu(project, HU_A)
    project.commit(f'feat/{HU_A}', 'README.md', 'rama\n')
    project.commit('main', 'README.md', 'base cambiada\n')
    number, key = request(project, 'close', HU_A)
    with pytest.raises(SystemExit):
        enforcer(project).close(key, number, f'feat/{HU_A}', merger(project))
    data = authority(project)
    assert (data['state'], data['hu'], data['causes']) == ('reconcile_required', HU_A, ['merge_conflict'])
    assert f'feat/{HU_A}' in branches(project.root)
    assert ask(project, 'open', HU_B).code == RECONCILE
    acknowledge(project.store, key)                                   # el reconocimiento no cierra la HU
    assert ask(project, 'open', HU_C).code == RECONCILE
    with pytest.raises(ReconciliationRequired, match='no demuestra'):
        reconcile(project.context, project.store, HU_A, 'closed', reason='x', confirm=True)
    git(project.root, 'checkout', '-q', 'main')                       # el humano resuelve y fusiona a mano
    git(project.root, 'merge', '--no-ff', '--no-edit', '-X', 'ours', f'feat/{HU_A}')
    git(project.root, 'branch', '-d', f'feat/{HU_A}')
    result = reconcile(project.context, project.store, HU_A, 'closed', reason='conflicto resuelto a mano',
                       actor='lead', confirm=True)
    assert result['evidence']['close_proof']['kind'] == 'recorded_close_tip_integrated'
    assert authority(project)['state'] == 'free'
    assert project.store.get(op_key_for(key))['state'] == 'reconciled'
    assert open_hu(project, HU_B).code == ALLOWED


# ---------------------------------------------------------------------------------- concurrencia y alcance
def test_two_concurrent_openers_of_different_hus_open_exactly_one(project):
    requests = {hu: request(project, 'open', hu) for hu in (HU_A, HU_B)}
    barrier, results, errors = threading.Barrier(2), {}, []

    def run(hu):
        store = StateStore.in_directory(project.context.state_dir)
        try:
            gate = enforcer(project, store)
            barrier.wait()
            number, key = requests[hu]
            results[hu] = gate.open(key, number, f'feat/{hu}', checkout(project))
        except BaseException as exc:          # noqa: BLE001 - se informa en la aserción
            errors.append(exc)
        finally:
            store.close()

    threads = [threading.Thread(target=run, args=(hu,)) for hu in (HU_A, HU_B)]
    [thread.start() for thread in threads]
    [thread.join() for thread in threads]
    assert not errors
    assert sorted(result.verdict for result in results.values()) == ['allow', 'reject']
    winner = next(hu for hu, result in results.items() if result.verdict == 'allow')
    assert [b for b in branches(project.root) if b.startswith('feat/')] == [f'feat/{winner}']
    assert authority(project)['hu'] == winner


def test_independent_projects_open_in_parallel_without_a_global_lock(tmp_path):
    alpha, beta = Project(tmp_path, 'alpha'), Project(tmp_path, 'beta')
    try:
        with hu_lock(alpha.context):                       # alpha ocupado no detiene a beta
            number, key = request(beta, 'open', HU_A)
            assert enforcer(beta, lock_timeout=0.5).open(key, number, f'feat/{HU_A}', checkout(beta)).code == ALLOWED
            beta.store.finish(key, 'done')
        results, barrier = {}, threading.Barrier(2)
        pending = {item.context.project_id: (item, request(item, 'open', HU_B)) for item in (alpha, beta)}

        def run(name):
            item, (number, key) = pending[name]
            store = StateStore.in_directory(item.context.state_dir)
            try:
                barrier.wait()
                results[name] = enforcer(item, store).open(key, number, f'feat/{HU_B}', checkout(item))
            finally:
                store.close()

        threads = [threading.Thread(target=run, args=(name,)) for name in pending]
        [thread.start() for thread in threads]
        [thread.join() for thread in threads]
        assert results['alpha'].code == ALLOWED                      # alpha estaba libre
        assert results['beta'].code == ANOTHER_OPEN                  # beta ya tenía HU_A: su regla, no la de alpha
        assert alpha.store.get(AUTHORITY)['hu'] == HU_B and beta.store.get(AUTHORITY)['hu'] == HU_A
        assert (alpha.context.state_dir / 'hu.lock').exists() and (beta.context.state_dir / 'hu.lock').exists()
    finally:
        alpha.store.close()
        beta.store.close()


def test_projects_sharing_a_repository_are_rejected_explicitly(tmp_path):
    alpha = Project(tmp_path, 'alpha')
    beta_root = (tmp_path / 'beta').resolve()
    git(alpha.root, 'worktree', 'add', '-q', '-b', 'beta-work', str(beta_root), 'main')
    beta = Project.__new__(Project)
    beta.root, beta.context = beta_root, ProjectContext(ROOT, beta_root, 'beta')
    beta.context.tracker_path.parent.mkdir(parents=True)
    beta.store = StateStore.in_directory(beta.context.state_dir)
    try:
        for item in (alpha, beta):
            create = Mock()
            decision = ask(item, 'open', HU_A, operation=create)
            assert (decision.code, create.called) == (SHARED, False)
            assert preflight(item.context, HU_A).code == SHARED
        assert [b for b in branches(alpha.root) if b.startswith('feat/')] == []
    finally:
        alpha.store.close()
        beta.store.close()


# ------------------------------------------------------------------------------ evidencia externa y bootstrap
def test_branch_deleted_externally_blocks_and_never_hydrates(project):
    open_hu(project, HU_A)
    git(project.root, 'checkout', '-q', 'main')
    git(project.root, 'branch', '-q', '-D', f'feat/{HU_A}')
    assert ask(project, 'open', HU_B).code == RECONCILE
    assert enforcer(project).hydration_branch() is None


def test_external_commits_on_the_open_branch_keep_it_open(project):
    open_hu(project, HU_A)
    project.commit(f'feat/{HU_A}', 'externo.txt', 'x\n')
    assert enforcer(project).hydration_branch() == f'feat/{HU_A}'
    assert ask(project, 'open', HU_B).code == ANOTHER_OPEN


def test_bootstrap_of_an_existing_project_adopts_the_observed_open_hu(project):
    project.watcher_create(HU_A)                    # historial anterior a E4 (evento sin hu_gate)
    gate = enforcer(project)
    assert gate.hydration_branch() == f'feat/{HU_A}' and authority(project) == {}
    assert ask(project, 'open', HU_B).code == ANOTHER_OPEN
    assert ask(project, 'open', HU_A).code == RESUME and authority(project)['hu'] == HU_A


def test_bootstrap_with_an_untracked_branch_needs_human_reconciliation(project):
    git(project.root, 'checkout', '-q', '-b', f'feat/{HU_A}')
    project.commit(f'feat/{HU_A}', 'a.txt', 'a\n')
    assert ask(project, 'open', HU_B).code == UNKNOWN
    reconcile(project.context, project.store, HU_A, 'active', reason='rama previa a E4', actor='lead', confirm=True)
    assert authority(project)['hu'] == HU_A and project.observe()['status'] == 'one_open_hu'
    assert ask(project, 'open', HU_C).code == ANOTHER_OPEN
    assert ask(project, 'open', HU_A).code == RESUME


# --------------------------------------------------------------------------------------- reconciliación
def test_reconciliation_validates_evidence_and_dry_run_writes_nothing(project):
    open_hu(project, HU_A)
    before = rows(project.store)
    plan = reconcile(project.context, project.store, HU_A, 'active')
    assert plan['dry_run'] and plan['evidence']['git']['exists'] and rows(project.store) == before
    for target, match in (('closed', 'no demuestra'), ('abandoned', 'sigue existiendo')):
        with pytest.raises(ReconciliationRequired, match=match):
            reconcile(project.context, project.store, HU_A, target, reason='x', confirm=True)
    with pytest.raises(ReconciliationRequired, match='--reason'):
        reconcile(project.context, project.store, HU_A, 'active', confirm=True)
    with pytest.raises(ReconciliationRequired, match='identificador'):
        reconcile(project.context, project.store, 'HU_mal', 'active')
    git(project.root, 'checkout', '-q', '-b', f'feat/{HU_B}', 'main')
    project.commit(f'feat/{HU_B}', 'b.txt', 'b\n')
    with pytest.raises(ReconciliationRequired, match='otras HU'):
        reconcile(project.context, project.store, HU_B, 'active', reason='x', confirm=True)
    assert rows(project.store) == before


def test_external_merge_reconciled_as_closed_keeps_history(project):
    open_hu(project, HU_A)
    project.merge(HU_A, delete=False)
    assert ask(project, 'open', HU_B).code == RECONCILE
    reconcile(project.context, project.store, HU_A, 'closed', reason='merge manual revisado', actor='lead',
              confirm=True)
    record = project.store.get(RESOLUTION_PREFIX + HU_A)
    assert (record['resolution'], record['actor'], record['reason'], record['from_state']) == \
        ('closed', 'lead', 'merge manual revisado', 'reconcile_required')
    assert record['evidence']['close_proof']['kind'] == 'branch_tip_integrated'
    assert authority(project)['history'][-1]['reason'] == 'human_reconciled:closed'
    observation = project.observe()
    assert observation['hus'][HU_A]['causes'] == ['human_reconciled:closed'] and observation['status'] == 'no_open_hu'
    reconcile(project.context, project.store, HU_A, 'closed', reason='revisión 2', actor='qa', confirm=True)
    assert project.store.get(RESOLUTION_PREFIX + HU_A)['history'][-1]['actor'] == 'lead'
    assert open_hu(project, HU_B).code == ALLOWED


def test_resolution_stops_applying_when_the_evidence_changes(project):
    open_hu(project, HU_A)
    project.merge(HU_A, delete=False)
    reconcile(project.context, project.store, HU_A, 'closed', reason='merge revisado', confirm=True)
    project.commit(f'feat/{HU_A}', 'tarde.txt', 'x\n')                # la rama cerrada vuelve a moverse
    assert project.observe()['hus'][HU_A]['observed_state'] != 'closed'
    assert ask(project, 'open', HU_B).rejected


def test_abandoned_requires_the_branch_to_be_gone(project):
    open_hu(project, HU_A)
    git(project.root, 'checkout', '-q', 'main')
    git(project.root, 'branch', '-q', '-D', f'feat/{HU_A}')            # el humano descartó la HU
    reconcile(project.context, project.store, HU_A, 'abandoned', reason='HU descartada', confirm=True)
    assert project.observe()['hus'][HU_A]['causes'] == ['human_reconciled:abandoned']
    assert authority(project)['state'] == 'free' and open_hu(project, HU_B).code == ALLOWED


def test_reconciliation_cli_inspects_read_only_and_requires_a_stopped_watcher(project):
    (project.root / 'project.json').write_text(json.dumps({'schema_version': 1, 'project_id': 'alpha'}),
                                               encoding='utf-8')
    open_hu(project, HU_A)
    project.merge(HU_A, delete=False)
    scope = ['--root', str(ROOT), '--workspace', str(project.root), '--project', 'alpha']
    before = rows(project.store)
    for extra in (['--inspect'], ['--reconcile', HU_A, '--as', 'closed']):
        output = io.StringIO()
        with redirect_stdout(output):
            assert hu_enforcement.main(scope + extra) == 0
        assert rows(project.store) == before
    report = json.loads(output.getvalue())
    assert report['dry_run'] and report['evidence']['close_proof']['kind'] == 'branch_tip_integrated'
    confirm = scope + ['--reconcile', HU_A, '--as', 'closed', '--reason', 'revisado', '--actor', 'lead', '--confirm']
    with project_lock(project.context, 'watcher'), pytest.raises(SystemExit), redirect_stdout(io.StringIO()):
        hu_enforcement.main(confirm)                                   # watcher en marcha: nada se escribe
    assert rows(project.store) == before
    with redirect_stdout(io.StringIO()):
        assert hu_enforcement.main(confirm) == 0
    assert project.store.get(RESOLUTION_PREFIX + HU_A)['actor'] == 'lead'


def test_inspect_explains_cause_and_proposes_a_resolution(project):
    open_hu(project, HU_A)
    project.merge(HU_A, delete=False)
    report = hu_enforcement.inspect(project.context, project.store)
    assert report['view']['status'] == 'reconcile_required'
    proposal = report['proposals'][HU_A]
    assert proposal['proposal'] == 'closed' and 'merged_outside_watcher' in proposal['causes']
    assert report['operations'][0]['state'] == 'confirmed'


# ------------------------------------------------------------------------------------------ modos y config
def watcher_runtime(root, mode):
    ai = {'defaults': {'provider': 'fake'}, 'providers': {'fake': {'executable': 'fake-cli'}},
          'tracker': {'settle_seconds': 3600, 'rewrite_grace_seconds': 0}, 'hu_lifecycle': {'mode': mode}}
    (root / 'config_bmad.json').write_text(json.dumps({'ai': ai}), encoding='utf-8')
    registry = default_registry()
    registry.register('fake', FakeProvider)
    runner = Mock()
    runner.run.return_value = Result(0, '')
    rt = Runtime(root, registry=registry, gateway=Mock(), runner=runner)
    rt.context.tracker_path.parent.mkdir(parents=True, exist_ok=True)
    return rt


@pytest.fixture
def make_watcher(tmp_path):
    git(tmp_path, 'init', '-q', '-b', 'main')
    (tmp_path / 'README.md').write_text('base\n', encoding='utf-8')
    git(tmp_path, 'add', 'README.md')
    git(tmp_path, 'commit', '-q', '-m', 'init')
    built = []

    def build(mode='enforce'):
        for rt in built:
            rt.close()
        built.append(watcher_runtime(tmp_path, mode))
        if not built[-1].context.tracker_path.exists():      # tracker presente desde el primer arranque
            built[-1].context.tracker_path.write_text('', encoding='utf-8')
        return built[-1]

    yield build
    for rt in built:
        rt.close()


@pytest.mark.parametrize('mode', ['off', 'observe', 'enforce'])
def test_only_enforce_builds_the_authority_and_off_observes_nothing(make_watcher, mode):
    rt = make_watcher(mode)
    with patch.multiple(workflow, _runtime=rt):
        built = workflow.crear_enforcer()
    assert isinstance(built, Enforcer) if mode == 'enforce' else built is None
    assert (hu_lifecycle.observe_runtime(rt, 'startup') is None) == (mode == 'off')


def test_project_json_opts_in_without_touching_the_engine_config(tmp_path):
    engine, workspace = tmp_path / 'engine', tmp_path / 'ws'
    engine.mkdir()
    workspace.mkdir()
    engine_config = json.dumps({'ai': {'defaults': {'provider': 'claude'}}})
    (engine / 'config_bmad.json').write_text(engine_config, encoding='utf-8')
    (workspace / 'project.json').write_text(json.dumps({'schema_version': 1, 'project_id': 'iso', 'config': {
        'ai': {'hu_lifecycle': {'mode': 'enforce'}}}}), encoding='utf-8')
    context = ProjectContext(engine, workspace, 'iso')
    assert load_policy(context) == {'mode': 'enforce'}
    assert RuntimeConfig.load(engine, context=context).data['hu_lifecycle'] == {'mode': 'enforce'}
    assert (engine / 'config_bmad.json').read_text(encoding='utf-8') == engine_config
    (workspace / 'project.json').write_text(json.dumps({'schema_version': 1, 'project_id': 'iso'}), encoding='utf-8')
    assert load_policy(context) == {'mode': 'observe'}


# ----------------------------------------------------------------------------------- watcher: defecto D5
def append(rt, author, *lines):
    def action():
        with rt.context.tracker_path.open('a', encoding='utf-8') as handle:
            handle.write(f'### [11-10-2026] {author}\n- **Hora:** 10:00:00\n' + ''.join(f'{line}\n' for line in lines))
    return action


def open_a(rt):
    return append(rt, 'HUMANO', '- **Estado:** APPROVE', f'- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/{HU_A}')


def d5_block(rt):
    """El bloque del defecto D5: BRANCH-CREATE de otra HU y, debajo, la instrucción dependiente para @BA."""
    return append(rt, 'HUMANO', '- **Estado:** APPROVE', f'- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/{HU_B}',
                  f'@BA: El MVP fue aprobado. La rama feat/{HU_B} ha sido creada. Continúa con la épica {HU_B}.')


def ba_handoffs(rt):
    found = []
    for key, raw in rt.state.db.execute("SELECT id,data FROM records WHERE id LIKE 'queued:%' OR id LIKE 'dispatch:%'"):
        data = json.loads(raw)
        if data.get('agent_id') == 'business-analyst' and data.get('outcome') != 'suppressed':
            found.append(key)
    return found


def unfinished_events(rt):
    return [key for key, raw in rt.state.db.execute("SELECT id,data FROM records WHERE id LIKE 'event:%'")
            if json.loads(raw)['state'] != 'done']


def checkout_root(root):
    def create(branch):
        exists = git(root, 'branch', '--list', branch).stdout.strip()
        git(root, 'checkout', '-q', *([] if exists else ['-b']), branch)
    return create


def run(rt, root, actions, expect=KeyboardInterrupt, create=None):
    with patch.multiple(workflow, _runtime=rt, DIRECTORIO_RAIZ=root, TRACKER_PATH=str(rt.context.tracker_path)), \
            patch.object(workflow, 'gitops_branch_create', create or Mock(side_effect=checkout_root(root))):
        run_watcher(rt, root, actions, expect=expect)


def rejected_ops(rt):
    return [json.loads(raw) for _, raw in rt.state.db.execute("SELECT id,data FROM records WHERE id LIKE 'hu_op:%'")
            if json.loads(raw)['state'] == 'rejected']


def test_d5_reproduced_in_observe_mode(make_watcher, tmp_path):
    """Antes de E4 (y en observe): se abre una segunda HU y la instrucción dependiente llega a la cola de @BA."""
    rt = make_watcher('observe')
    run(rt, tmp_path, [open_a(rt), d5_block(rt), lambda: None])
    assert {f'feat/{HU_A}', f'feat/{HU_B}'} <= set(branches(tmp_path))
    assert ba_handoffs(rt)


def test_d5_rejected_branch_create_dispatches_nothing_from_its_block(make_watcher, tmp_path):
    rt = make_watcher('enforce')
    create = Mock(side_effect=checkout_root(tmp_path))
    run(rt, tmp_path, [open_a(rt), d5_block(rt), lambda: None, lambda: None], create=create)
    create.assert_called_once_with(f'feat/{HU_A}')
    assert f'feat/{HU_B}' not in branches(tmp_path) and head(tmp_path) == f'feat/{HU_A}'
    assert ba_handoffs(rt) == [] and unfinished_events(rt) == []
    [op] = rejected_ops(rt)
    assert (op['hu'], op['decision']['code'], op['notice']['state']) == (HU_B, ANOTHER_OPEN, 'delivered')
    lines = read_tracker(rt.context.tracker_path).lines
    number = next(i for i, line in enumerate(lines) if line.startswith('@BA:'))
    ba_event = rt.state.get('event:' + StateStore.fingerprint(number, lines[number]))
    assert (ba_event['state'], ba_event['outcome'], ba_event['hu_op']) == ('done', 'suppressed', op['key'])
    text = rt.context.tracker_path.read_text(encoding='utf-8')
    assert text.count('] WATCHER') == 1 and '- **Handoff:** @HUMANO:' in text[text.index('] WATCHER'):]
    assert rt.state.get(AUTHORITY)['hu'] == HU_A
    with patch.object(workflow, 'TRACKER_PATH', str(rt.context.tracker_path)):
        assert workflow.is_tracker_paused_for_human()               # el aviso deja el flujo esperando al humano


def test_d5_instruction_on_the_same_line_as_the_rejected_macro_is_not_dispatched(make_watcher, tmp_path):
    rt = make_watcher('enforce')
    same_line = append(rt, 'HUMANO', f'- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/{HU_B} @BA: Continúa con {HU_B}.')
    run(rt, tmp_path, [open_a(rt), same_line, lambda: None, lambda: None])
    assert ba_handoffs(rt) == [] and f'feat/{HU_B}' not in branches(tmp_path)
    assert [op['hu'] for op in rejected_ops(rt)] == [HU_B]


def test_restart_and_acknowledge_never_dispatch_the_rejected_block(make_watcher, tmp_path):
    rt = make_watcher('enforce')
    run(rt, tmp_path, [open_a(rt), d5_block(rt), lambda: None])
    [op] = rejected_ops(rt)
    acknowledge(rt.state, op['event'])
    append(rt, 'HUMANO', '- **Estado:** APPROVE', '- **Feedback:** visto')()       # el humano responde al aviso
    git(tmp_path, 'checkout', '-q', 'main')
    rt = make_watcher('enforce')                                                    # reinicio
    create = Mock()
    run(rt, tmp_path, [lambda: None], create=create)
    assert not create.called and ba_handoffs(rt) == [] and f'feat/{HU_B}' not in branches(tmp_path)
    # Git del watcher pasa por el runner (doble): la hidratación pide la HU abierta y nunca la rechazada.
    git_calls = str(rt.runner.run.call_args_list)
    assert f'feat/{HU_A}' in git_calls and f'feat/{HU_B}' not in git_calls
    assert len(rejected_ops(rt)) == 1


def test_crash_after_rejection_resumes_without_dispatch_and_emits_the_notice_once(make_watcher, tmp_path):
    rt = make_watcher('enforce')
    with patch.object(Enforcer, 'notify', side_effect=RuntimeError('caída al escribir el aviso')):
        run(rt, tmp_path, [open_a(rt), d5_block(rt), lambda: None, lambda: None], expect=ReconciliationRequired)
    [op] = rejected_ops(rt)
    assert op['notice']['state'] == 'pending'
    rt = make_watcher('enforce')
    run(rt, tmp_path, [lambda: None, lambda: None])
    assert ba_handoffs(rt) == [] and unfinished_events(rt) == []
    assert rejected_ops(rt)[0]['notice']['state'] == 'delivered'
    assert rt.context.tracker_path.read_text(encoding='utf-8').count('HU BLOQUEADA') == 1


def test_failed_branch_create_then_acknowledged_still_holds_its_dependents(make_watcher, tmp_path):
    rt = make_watcher('enforce')
    block = append(rt, 'HUMANO', '- **Estado:** APPROVE', f'- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/{HU_A}',
                   f'@BA: La rama feat/{HU_A} ha sido creada. Procede.')
    run(rt, tmp_path, [block, lambda: None, lambda: None], expect=ReconciliationRequired,
        create=Mock(side_effect=ReconciliationRequired('GitOps no pudo crear la rama')))
    [event] = unfinished_events(rt)
    assert rt.state.get(op_key_for(event))['state'] == 'failed'
    rt = make_watcher('enforce')
    run(rt, tmp_path, [], expect=ReconciliationRequired)              # in_flight: no se repite ni se despacha
    acknowledge(rt.state, event)
    rt = make_watcher('enforce')
    run(rt, tmp_path, [lambda: None])
    assert ba_handoffs(rt) == [] and f'feat/{HU_A}' not in branches(tmp_path)


def test_enforce_watcher_resumes_the_same_hu_and_lets_agents_work_on_it(make_watcher, tmp_path):
    rt = make_watcher('enforce')
    resume = append(rt, 'HUMANO', '- **Estado:** APPROVE', f'- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/{HU_A}',
                    f'@BA: Continúa con {HU_A}.')
    run(rt, tmp_path, [open_a(rt), resume, lambda: None])
    assert ba_handoffs(rt) and rejected_ops(rt) == []
    assert rt.state.get(AUTHORITY)['state'] == 'active' and branches(tmp_path) == [f'feat/{HU_A}', 'main']
