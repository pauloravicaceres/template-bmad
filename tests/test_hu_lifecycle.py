"""Fase 4F-E3: ciclo de vida observado de las HU por proyecto (modo OBSERVE) con repositorios Git temporales reales."""
import io
import json
import os
from contextlib import redirect_stdout
from pathlib import Path
import subprocess
from types import SimpleNamespace
from unittest.mock import patch

import pytest

from bmad_runtime import hu_lifecycle, watcher_service, workflow
from bmad_runtime.context import ProjectContext
from bmad_runtime.errors import ConfigurationError, ReconciliationRequired
from bmad_runtime.hu_lifecycle import (CONFLICT_ALERT, PREFIX, STATES, SUMMARY, GitReader, observe, observe_runtime,
                                       policy_from_config, record, shared_repositories)
from bmad_runtime.hu_naming import is_hu_id
from bmad_runtime.state import StateStore
from tests.test_tracker_integrity import make_runtime
from tests.test_tracker_io import run_watcher

ROOT = Path(__file__).resolve().parents[1]
HU_A, HU_B = '001-registrar-cliente', '002-gestion-pagos'


def git(root, *args, check=True, **extra_env):
    env = {k: v for k, v in os.environ.items() if k not in hu_lifecycle._GIT_REDIRECTS}
    env.update(GIT_CEILING_DIRECTORIES=str(Path(root).parent), **extra_env)
    return subprocess.run(['git', '-C', str(root), '-c', 'user.name=BMAD Test', '-c', 'user.email=bmad@example.invalid',
                           '-c', 'commit.gpgsign=false', '-c', 'core.autocrlf=false', *args],
                          capture_output=True, text=True, check=check, env=env)


class Project:
    """Workspace de prueba: repositorio Git real, tracker del proyecto y SQLite del proyecto."""

    def __init__(self, base, project_id='alpha', repo=True):
        self.root = (base / project_id).resolve()
        self.root.mkdir(parents=True)
        self.context = ProjectContext(ROOT, self.root, project_id)
        self.context.tracker_path.parent.mkdir(parents=True)
        self.store = StateStore.in_directory(self.context.state_dir)
        if repo:
            git(self.root, 'init', '-q', '-b', 'main')
            self.commit('main', 'README.md', 'base\n')

    def commit(self, branch, name, text):
        if git(self.root, 'symbolic-ref', '--short', 'HEAD').stdout.strip() != branch:
            git(self.root, 'checkout', '-q', branch)
        (self.root / name).write_text(text, encoding='utf-8')
        git(self.root, 'add', name)
        git(self.root, 'commit', '-q', '-m', f'{branch}: {name}')

    def block(self, author, *lines):
        with self.context.tracker_path.open('a', encoding='utf-8', newline='') as handle:
            handle.write(f'\n### [11-10-2026] {author}\n- **Hora:** 10:00:00\n' + ''.join(f'{line}\n' for line in lines))

    def lines(self):
        return watcher_service.read_tracker(self.context.tracker_path).lines

    def macro(self, action, hu):
        macro = 'BRANCH-CREATE' if action == 'create' else 'MERGE-CLOSE'
        self.block('Product Manager' if action == 'create' else 'Code Review',
                   f'- **Handoff:** @WATCHER: GITOPS-{macro} feat/{hu}')
        return len(self.lines()) - 1

    def event(self, number):
        return 'event:' + StateStore.fingerprint(number, self.lines()[number])

    def run_event(self, number, state='done'):
        """Lo que hace el watcher: claim (in_flight) y, al terminar la línea, done; luego avanza el cursor."""
        key = self.event(number)
        self.store.claim(key)
        if state == 'done':
            self.store.finish(key, 'done')
        self.store.put('tracker_cursor', {'count': len(self.lines()), 'prefix_hash': 'x'})
        return key

    def watcher_create(self, hu, commit=True):
        number = self.macro('create', hu)
        exists = git(self.root, 'branch', '--list', f'feat/{hu}').stdout.strip()
        git(self.root, 'checkout', '-q', *([] if exists else ['-b']), f'feat/{hu}')
        if commit:
            self.commit(f'feat/{hu}', f'{hu}.txt', f'{hu}\n')
        return self.run_event(number)

    def merge(self, hu, delete=True):
        git(self.root, 'checkout', '-q', 'main')
        git(self.root, 'merge', '--no-ff', '--no-edit', f'feat/{hu}')
        if delete:
            git(self.root, 'branch', '-d', f'feat/{hu}')

    def watcher_close(self, hu):
        number = self.macro('close', hu)
        self.merge(hu)
        return self.run_event(number)

    def observe(self):
        return observe(self.context, self.store, sleep=lambda _s: None)

    def git_state(self):
        # El índice se mide primero y `status` corre sin locks opcionales: la propia comprobación no lo reescribe.
        index = self.root / '.git' / 'index'
        mtime = index.stat().st_mtime_ns if index.exists() else None
        return (mtime, git(self.root, 'for-each-ref').stdout,
                git(self.root, 'symbolic-ref', '-q', 'HEAD', check=False).stdout,
                git(self.root, 'status', '--porcelain', GIT_OPTIONAL_LOCKS='0').stdout)


def hu(observation, name):
    return observation['hus'][name]


@pytest.fixture
def project(tmp_path):
    item = Project(tmp_path)
    yield item
    item.store.close()


# ----------------------------------------------------------------------------- bootstrap y estados
def test_new_project_without_history_proves_no_open_hu(project):
    observation = project.observe()
    assert (observation['status'], observation['certainty'], observation['hus']) == ('no_open_hu', 'high', {})
    assert observation['authoritative'] is False and observation['git']['base'] == 'main'


def test_workspace_without_repository_is_unknown_never_no_open_hu(tmp_path):
    item = Project(tmp_path, repo=False)
    try:
        observation = item.observe()
    finally:
        item.store.close()
    assert observation['status'] == 'unknown' and observation['causes'] == ['git_no_repository']


def test_hu_documents_alone_do_not_open_a_hu(project):
    (project.root / 'docs' / 'business-analyst').mkdir(parents=True)
    (project.root / 'docs' / 'business-analyst' / f'{HU_A}.md').write_text('# HU', encoding='utf-8')
    (project.root / 'specs' / HU_A).mkdir(parents=True)
    assert project.observe()['status'] == 'no_open_hu'


def test_branch_create_pending_is_opening(project):
    project.macro('create', HU_A)
    observation = project.observe()
    assert hu(observation, HU_A)['observed_state'] == 'opening'
    assert 'create_pending' in hu(observation, HU_A)['causes']
    assert (observation['status'], observation['open']) == ('one_open_hu', [HU_A])


def test_created_branch_is_active_with_full_evidence(project):
    project.watcher_create(HU_A)
    (project.root / 'docs' / 'business-analyst').mkdir(parents=True)
    (project.root / 'docs' / 'business-analyst' / f'{HU_A}.md').write_text('# HU', encoding='utf-8')
    data = hu(project.observe(), HU_A)
    assert (data['observed_state'], data['certainty'], data['authoritative']) == ('active', 'high', False)
    assert (data['project_id'], data['branch'], data['base']) == ('alpha', f'feat/{HU_A}', 'main')
    evidence = data['evidence']
    assert evidence['git']['exists'] and evidence['git']['head'] and evidence['git']['ahead'] == 1
    assert evidence['tracker'] == {'creates': [3], 'closes': [], 'last': 'create'}
    assert evidence['sqlite']['create']['event_state'] == 'done'
    assert evidence['documents'] == {'hu_file': True, 'spec_dir': False}


def test_repeated_branch_create_keeps_one_active_hu(project):
    project.watcher_create(HU_A)
    project.watcher_create(HU_A, commit=False)       # el watcher reactiva la rama existente
    observation = project.observe()
    assert hu(observation, HU_A)['observed_state'] == 'active'
    assert hu(observation, HU_A)['evidence']['tracker']['creates'] == [3, 6]
    assert (observation['status'], observation['open']) == ('one_open_hu', [HU_A])


def test_several_agents_on_the_same_hu_keep_it_active(project):
    project.watcher_create(HU_A)
    for author in ('Business Analyst', 'Solutions Architect', 'Dev Backend'):
        project.block(author, f'- **Mensaje:** trabajo sobre {HU_A}.md', '- **Handoff:** @QA: revisa')
    project.store.put('tracker_cursor', {'count': len(project.lines()), 'prefix_hash': 'x'})
    observation = project.observe()
    assert (observation['status'], hu(observation, HU_A)['observed_state']) == ('one_open_hu', 'active')


def test_merge_close_requested_is_closing(project):
    project.watcher_create(HU_A)
    project.macro('close', HU_A)
    observation = project.observe()
    assert hu(observation, HU_A)['observed_state'] == 'closing'
    assert observation['status'] == 'one_open_hu'


def test_completed_merge_close_is_closed(project):
    project.watcher_create(HU_A)
    project.watcher_close(HU_A)
    observation = project.observe()
    data = hu(observation, HU_A)
    assert (data['observed_state'], data['certainty']) == ('closed', 'high')
    assert not data['evidence']['git']['exists'] and data['evidence']['git']['merge_commits']
    assert (observation['status'], observation['open']) == ('no_open_hu', [])


def test_reopened_hu_after_close_is_active_not_merged_outside(project):
    project.watcher_create(HU_A)
    project.watcher_close(HU_A)
    project.watcher_create(HU_A, commit=False)      # nueva rama desde la base que ya contiene la merge anterior
    data = hu(project.observe(), HU_A)
    assert data['observed_state'] == 'active' and not data['evidence']['git']['tip_merged']


def test_merge_conflict_alert_requires_reconciliation(project):
    project.watcher_create(HU_A)
    number = project.macro('close', HU_A)
    key = project.run_event(number, state='in_flight')
    project.store.put(CONFLICT_ALERT + key[len('event:'):][:64], {'state': 'done'})
    observation = project.observe()
    data = hu(observation, HU_A)
    assert data['observed_state'] == 'reconcile_required'
    assert 'merge_conflict' in data['causes'] and 'conflict_alert_done' in data['causes']
    assert observation['status'] == 'reconcile_required' and observation['unresolved'] == [HU_A]


def test_real_git_conflict_in_progress_is_attributed_to_the_hu(project):
    project.watcher_create(HU_A)
    project.commit(f'feat/{HU_A}', 'README.md', 'rama\n')
    project.commit('main', 'README.md', 'base cambiada\n')
    number = project.macro('close', HU_A)
    project.run_event(number, state='in_flight')
    assert git(project.root, 'merge', '--no-ff', '--no-edit', f'feat/{HU_A}', check=False).returncode != 0
    observation = project.observe()
    data = hu(observation, HU_A)
    assert data['observed_state'] == 'reconcile_required'
    assert {'merge_conflict', 'merge_in_progress'} <= set(data['causes'])
    assert 'git_operation_in_progress' not in observation['causes']
    git(project.root, 'merge', '--abort')


def test_unattributed_git_operation_in_progress_is_unknown(project):
    project.commit('main', 'README.md', 'base\nmas\n')
    git(project.root, 'checkout', '-q', '-b', 'tmp', 'HEAD~1')
    project.commit('tmp', 'README.md', 'otra\n')
    git(project.root, 'merge', 'main', check=False)
    observation = project.observe()
    assert (observation['status'], observation['causes']) == ('unknown', ['git_operation_in_progress'])
    git(project.root, 'merge', '--abort')


def test_external_merge_is_never_closed_automatically(project):
    project.watcher_create(HU_A)
    project.merge(HU_A, delete=True)               # fusionada y borrada fuera del watcher
    data = hu(project.observe(), HU_A)
    assert data['observed_state'] == 'reconcile_required'
    assert {'merged_outside_watcher', 'branch_absent'} <= set(data['causes'])


def test_external_merge_with_retained_branch_needs_reconciliation(project):
    project.watcher_create(HU_A)
    project.merge(HU_A, delete=False)
    data = hu(project.observe(), HU_A)
    assert data['observed_state'] == 'reconcile_required'
    assert {'merged_outside_watcher', 'branch_retained'} <= set(data['causes'])


def test_branch_deleted_manually(project):
    project.watcher_create(HU_A)
    git(project.root, 'checkout', '-q', 'main')
    git(project.root, 'branch', '-q', '-D', f'feat/{HU_A}')
    data = hu(project.observe(), HU_A)
    assert (data['observed_state'], data['causes']) == ('reconcile_required', ['branch_absent'])


def test_head_on_another_branch_does_not_close(project):
    project.watcher_create(HU_A)
    git(project.root, 'checkout', '-q', 'main')
    data = hu(project.observe(), HU_A)
    assert data['observed_state'] == 'active' and 'head_elsewhere' in data['causes']


def test_two_open_hus_require_reconciliation(project):
    project.watcher_create(HU_A)
    project.watcher_create(HU_B)
    observation = project.observe()
    assert [hu(observation, name)['observed_state'] for name in (HU_A, HU_B)] == ['active', 'active']
    assert observation['status'] == 'reconcile_required' and 'multiple_open_hu' in observation['causes']
    assert observation['open'] == [HU_A, HU_B]


def test_close_done_with_unmerged_branch_is_contradictory(project):
    project.watcher_create(HU_A)
    project.run_event(project.macro('close', HU_A))      # evento done sin merge real
    data = hu(project.observe(), HU_A)
    assert (data['observed_state'], data['causes'][0]) == ('reconcile_required', 'close_done_branch_unmerged')


def test_close_done_without_git_evidence_is_not_closed(project):
    project.watcher_create(HU_A, commit=False)
    git(project.root, 'checkout', '-q', 'main')
    git(project.root, 'branch', '-q', '-D', f'feat/{HU_A}')
    project.run_event(project.macro('close', HU_A))
    data = hu(project.observe(), HU_A)
    assert (data['observed_state'], data['causes']) == ('reconcile_required', ['merge_evidence_missing'])


def test_acknowledged_conflict_resolved_by_hand_is_closed(project):
    project.watcher_create(HU_A)
    key = project.run_event(project.macro('close', HU_A), state='in_flight')
    project.merge(HU_A)                                      # el humano fusiona y reconoce el evento
    project.store.finish(key, 'done')
    project.store.put(key, {**project.store.get(key), 'acknowledged': 1.0, 'acknowledged_state': 'in_flight'})
    data = hu(project.observe(), HU_A)
    assert (data['observed_state'], data['certainty']) == ('closed', 'medium')
    assert 'close_acknowledged' in data['causes']


# ----------------------------------------------------------------------------- historial incompleto
def test_untracked_branch_is_unknown(project):
    git(project.root, 'branch', f'feat/{HU_B}')
    observation = project.observe()
    assert hu(observation, HU_B)['observed_state'] == 'unknown'
    assert hu(observation, HU_B)['causes'] == ['untracked_branch', 'no_commits']
    assert observation['status'] == 'unknown'


def test_untracked_branch_plus_active_hu_are_potentially_two_open(project):
    project.watcher_create(HU_A)
    project.commit('main', 'x.txt', 'x\n')
    git(project.root, 'checkout', '-q', '-b', f'feat/{HU_B}')
    project.commit(f'feat/{HU_B}', 'y.txt', 'y\n')
    observation = project.observe()
    assert observation['status'] == 'reconcile_required' and 'multiple_open_hu' in observation['causes']


def test_create_skipped_by_cursor_without_branch_is_unknown(project):
    project.macro('create', HU_A)
    project.store.put('tracker_cursor', {'count': len(project.lines()), 'prefix_hash': 'x'})
    data = hu(project.observe(), HU_A)
    assert (data['observed_state'], data['causes']) == ('unknown', ['create_not_executed_by_watcher', 'branch_absent'])


def test_unstable_tracker_is_unknown(project):
    project.watcher_create(HU_A)
    unstable = watcher_service.TrackerSnapshot([], None, False)
    with patch.object(watcher_service, 'read_tracker', return_value=unstable):
        observation = project.observe()
    assert (observation['status'], observation['causes'], observation['hus']) == ('unknown', ['tracker_unstable'], {})


def test_invalid_names_are_reported_and_never_become_hus(project):
    git(project.root, 'branch', 'feat/003-HU_mal')
    project.block('Product Manager', '- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/004_mal')
    observation = project.observe()
    assert observation['hus'] == {} and observation['status'] == 'no_open_hu'
    assert {'invalid_feature_branches', 'invalid_gitops_macros'} <= set(observation['causes'])
    assert observation['certainty'] == 'medium'


# ----------------------------------------------------------------------------- reinicio
def test_watcher_restart_during_opening(project):
    number = project.macro('create', HU_A)
    git(project.root, 'checkout', '-q', '-b', f'feat/{HU_A}')
    project.run_event(number, state='in_flight')           # el proceso murió antes de complete_line
    data = hu(project.observe(), HU_A)
    assert (data['observed_state'], data['causes']) == ('opening', ['event_in_flight', 'branch_present'])


def test_watcher_restart_during_closing_before_merge(project):
    project.watcher_create(HU_A)
    project.run_event(project.macro('close', HU_A), state='in_flight')
    data = hu(project.observe(), HU_A)
    assert (data['observed_state'], data['causes']) == ('closing', ['event_in_flight'])


def test_watcher_restart_after_merge_is_not_closed_automatically(project):
    project.watcher_create(HU_A)
    number = project.macro('close', HU_A)
    project.merge(HU_A)
    project.run_event(number, state='in_flight')
    data = hu(project.observe(), HU_A)
    assert (data['observed_state'], data['causes']) == ('reconcile_required', ['close_interrupted_after_merge'])


def test_previous_observation_only_keeps_closed_and_flags_the_rest(project):
    project.store.put(PREFIX + HU_A, {'observed_state': 'closed'})
    project.store.put(PREFIX + HU_B, {'observed_state': 'active'})
    observation = project.observe()                          # tracker rotado y ramas borradas
    assert hu(observation, HU_A)['observed_state'] == 'closed'
    assert hu(observation, HU_A)['causes'] == ['previous_observation_only']
    assert hu(observation, HU_B)['observed_state'] == 'unknown'
    assert observation['status'] == 'unknown'


def test_every_state_is_reachable_and_ids_are_kebab_case(tmp_path):
    seen = set()
    for index, scenario in enumerate([
            lambda p: p.macro('create', HU_A),                                         # opening
            lambda p: p.watcher_create(HU_A),                                          # active
            lambda p: (p.watcher_create(HU_A), p.macro('close', HU_A)),                # closing
            lambda p: (p.watcher_create(HU_A), p.watcher_close(HU_A)),                 # closed
            lambda p: git(p.root, 'branch', f'feat/{HU_A}'),                           # unknown
            lambda p: (p.watcher_create(HU_A), p.merge(HU_A))]):                       # reconcile_required
        item = Project(tmp_path, f'p{index}')
        try:
            scenario(item)
            observation = item.observe()
        finally:
            item.store.close()
        seen.update(data['observed_state'] for data in observation['hus'].values())
        assert all(is_hu_id(name) for name in observation['hus'])
    assert seen == set(STATES)


# ----------------------------------------------------------------------------- aislamiento
def test_two_projects_keep_independent_observations(tmp_path):
    alpha, beta = Project(tmp_path, 'alpha'), Project(tmp_path, 'beta')
    try:
        alpha.watcher_create(HU_A)
        beta.watcher_create(HU_A)                 # mismo identificador de HU en otro proyecto
        beta.watcher_create(HU_B)
        record(alpha.store, alpha.observe(), 'test')
        observation_b = beta.observe()
        record(beta.store, observation_b, 'test')
        summary_a, summary_b = alpha.store.get(SUMMARY), beta.store.get(SUMMARY)
        assert (summary_a['project_id'], summary_a['status'], summary_a['open']) == ('alpha', 'one_open_hu', [HU_A])
        assert (summary_b['project_id'], summary_b['status']) == ('beta', 'reconcile_required')
        assert alpha.store.get(PREFIX + HU_B) is None
        assert alpha.store.get(PREFIX + HU_A)['project_id'] == 'alpha'
        assert beta.store.get(PREFIX + HU_A)['project_id'] == 'beta'
        assert shared_repositories([summary_a, summary_b]) == {}
    finally:
        alpha.store.close()
        beta.store.close()


def test_projects_sharing_a_repository_through_worktrees_are_not_independent(tmp_path):
    alpha = Project(tmp_path, 'alpha')
    beta_root = (tmp_path / 'beta').resolve()
    git(alpha.root, 'worktree', 'add', '-q', '-b', 'beta-work', str(beta_root), 'main')
    beta = Project.__new__(Project)
    beta.root, beta.context = beta_root, ProjectContext(ROOT, beta_root, 'beta')
    beta.context.tracker_path.parent.mkdir(parents=True)
    beta.store = StateStore.in_directory(beta.context.state_dir)
    try:
        alpha.watcher_create(HU_A)
        observation_a, observation_b = alpha.observe(), beta.observe()
        assert observation_a['status'] == 'one_open_hu'
        data = hu(observation_b, HU_A)                # la rama de alpha es visible desde beta
        assert data['observed_state'] == 'unknown' and 'shared_repository' in data['causes']
        assert observation_b['git']['worktree'] and 'shared_repository' in observation_b['causes']
        assert observation_b['status'] == 'unknown'
        assert observation_a['git']['repository'] == observation_b['git']['repository']
        assert shared_repositories([observation_a, observation_b]) == {'alpha': ['beta'], 'beta': ['alpha']}
    finally:
        alpha.store.close()
        beta.store.close()


# ----------------------------------------------------------------------------- persistencia
def rows(store):
    return {key: raw for key, raw in store.db.execute('SELECT id,data FROM records')}


def test_records_are_idempotent_across_polls_and_restarts(project):
    project.watcher_create(HU_A)
    assert record(project.store, project.observe(), 'startup', now=1.0) == 2
    before = rows(project.store)
    assert record(project.store, project.observe(), 'startup', now=2.0) == 0
    project.store.close()
    project.store = StateStore.in_directory(project.context.state_dir)     # reinicio del watcher
    assert record(project.store, project.observe(), 'startup', now=3.0) == 0
    assert rows(project.store) == before


def test_state_transition_keeps_previous_state_and_does_not_touch_other_records(project):
    key = project.watcher_create(HU_A)
    record(project.store, project.observe(), 'startup', now=1.0)
    event_before = project.store.get(key)
    project.watcher_close(HU_A)
    record(project.store, project.observe(), 'gitops', now=5.0)
    data, summary = project.store.get(PREFIX + HU_A), project.store.get(SUMMARY)
    assert (data['observed_state'], data['previous_state'], data['changed_at'], data['reason']) == \
        ('closed', 'active', 5.0, 'gitops')
    assert (summary['status'], summary['previous_state']) == ('no_open_hu', 'one_open_hu')
    assert project.store.get(key) == event_before
    assert not [k for k in rows(project.store) if k.startswith(('queued:', 'dispatch:', 'tracker_append:'))]


def test_observation_never_modifies_the_repository(project):
    project.watcher_create(HU_A)
    (project.root / 'sucio.txt').write_text('sin confirmar', encoding='utf-8')
    before = project.git_state()
    project.observe()
    assert project.git_state() == before


def test_git_reader_refuses_mutating_commands(project):
    reader = GitReader(project.root)
    for command in ('checkout', 'branch', 'merge', 'reset', 'status'):
        with pytest.raises(ValueError):
            reader(command)


# ----------------------------------------------------------------------------- política, hook y CLI
def test_policy_defaults_to_observe_and_accepts_enforce_only_explicitly():
    assert policy_from_config(None) == {'mode': 'observe'}
    assert policy_from_config({'mode': 'off'}) == {'mode': 'off'}
    assert policy_from_config({'mode': 'enforce'}) == {'mode': 'enforce'}       # Fase 4F-E4
    for value in ({'mode': 'x'}, {'mode': 'observe', 'extra': 1}, []):
        with pytest.raises(ConfigurationError):
            policy_from_config(value)


def test_runtime_config_accepts_the_policy(tmp_path):
    rt = make_runtime(tmp_path)
    try:
        assert rt.config.data['hu_lifecycle'] == {'mode': 'observe'}
    finally:
        rt.close()


def test_off_mode_records_nothing(project):
    project.watcher_create(HU_A)
    rt = SimpleNamespace(config=SimpleNamespace(data={'hu_lifecycle': {'mode': 'off'}}), state=project.store,
                         context=project.context)
    assert observe_runtime(rt, 'startup') is None and project.store.get(SUMMARY) is None


def test_failed_observation_is_recorded_as_unknown(project):
    rt = SimpleNamespace(config=SimpleNamespace(data={}), state=project.store, context=project.context)
    with patch.object(hu_lifecycle, 'observe', side_effect=RuntimeError('boom')):
        observation, written = observe_runtime(rt, 'startup')
    assert written == 1 and observation['status'] == 'unknown'
    assert project.store.get(SUMMARY)['causes'] == ['observation_failed:RuntimeError']


def test_cli_status_is_read_only(project):
    (project.root / 'project.json').write_text(json.dumps({'schema_version': 1, 'project_id': 'alpha'}), encoding='utf-8')
    project.watcher_create(HU_A)
    record(project.store, project.observe(), 'startup')
    before = rows(project.store)
    output = io.StringIO()
    with redirect_stdout(output):
        code = hu_lifecycle.main(['--root', str(ROOT), '--workspace', str(project.root), '--project', 'alpha', '--status'])
    result = json.loads(output.getvalue())
    assert code == 0 and (result['status'], result['open'], result['drift']) == ('one_open_hu', [HU_A], False)
    assert result['hus'][HU_A] == {'observed_state': 'active', 'certainty': 'high', 'causes': []}
    assert result['recorded']['status'] == 'one_open_hu'
    assert rows(project.store) == before


def test_cli_does_not_create_state_for_a_project_never_observed(tmp_path):
    item = Project(tmp_path, 'gamma')
    item.store.close()
    (item.context.state_dir / 'state.sqlite3').unlink()
    (item.root / 'project.json').write_text(json.dumps({'schema_version': 1, 'project_id': 'gamma'}), encoding='utf-8')
    with redirect_stdout(io.StringIO()):
        assert hu_lifecycle.main(['--root', str(ROOT), '--workspace', str(item.root), '--status']) == 0
    assert not (item.context.state_dir / 'state.sqlite3').exists()


# ----------------------------------------------------------------------------- watcher
@pytest.fixture
def watcher_rt(tmp_path):
    rt = make_runtime(tmp_path, {'settle_seconds': 3600, 'rewrite_grace_seconds': 0})
    git(tmp_path, 'init', '-q', '-b', 'main')
    git(tmp_path, 'add', 'config_bmad.json')
    git(tmp_path, 'commit', '-q', '-m', 'init')
    rt.context.tracker_path.write_text('', encoding='utf-8')
    with patch.multiple(workflow, _runtime=rt, DIRECTORIO_RAIZ=tmp_path, TRACKER_PATH=str(rt.context.tracker_path)):
        yield rt
    rt.close()


def append_create(rt, name):
    def action():
        with rt.context.tracker_path.open('a', encoding='utf-8') as handle:
            handle.write(f'### [11-10-2026] Product Manager\n- **Handoff:** @WATCHER: GITOPS-BRANCH-CREATE feat/{name}\n')
    return action


def test_watcher_observes_startup_and_branch_create(watcher_rt, tmp_path):
    create = lambda branch: git(tmp_path, 'checkout', '-q', '-b', branch)  # noqa: E731
    with patch.object(workflow, 'gitops_branch_create', side_effect=create):
        run_watcher(watcher_rt, tmp_path, [append_create(watcher_rt, HU_A), lambda: None])
    summary, data = watcher_rt.state.get(SUMMARY), watcher_rt.state.get(PREFIX + HU_A)
    assert (summary['status'], summary['open'], summary['reason'], summary['previous_state']) == \
        ('one_open_hu', [HU_A], 'gitops', 'no_open_hu')
    assert (data['observed_state'], data['certainty']) == ('active', 'high')


def test_watcher_observes_a_failed_gitops_and_keeps_failing_the_same_way(watcher_rt, tmp_path):
    with patch.object(workflow, 'gitops_branch_create', side_effect=ReconciliationRequired('git')):
        run_watcher(watcher_rt, tmp_path, [append_create(watcher_rt, HU_A)], expect=ReconciliationRequired)
    data = watcher_rt.state.get(PREFIX + HU_A)
    assert (data['observed_state'], data['reason'], data['causes']) == \
        ('opening', 'gitops-error', ['event_in_flight', 'branch_absent'])


def test_watcher_behaviour_is_unchanged_when_observation_fails(watcher_rt, tmp_path):
    create = lambda branch: git(tmp_path, 'checkout', '-q', '-b', branch)  # noqa: E731
    with patch.object(workflow, 'gitops_branch_create', side_effect=create) as gitops, \
            patch.object(hu_lifecycle, 'observe', side_effect=RuntimeError('boom')):
        run_watcher(watcher_rt, tmp_path, [append_create(watcher_rt, HU_A), lambda: None])
    gitops.assert_called_once_with(f'feat/{HU_A}')
    assert watcher_rt.state.get(SUMMARY)['status'] == 'unknown'
