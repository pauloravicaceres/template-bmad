import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import GitTelemetryOverview from '../components/git/GitTelemetryOverview.vue'
import type { GitStatusResponse } from '../types'

describe('GitTelemetryOverview Component', () => {
  const mockStatus: GitStatusResponse = {
    current_branch: 'feat/004-HU_panel_telemetria_control_versiones_git',
    head_commit_hash: 'a7c4e91d830b8ef29e92d77cb31940918ef83921',
    head_commit_short: 'a7c4e91',
    head_commit_message: 'feat(git): add spec for telemetry panel',
    head_commit_author: 'Business Analyst',
    head_committed_at: '2026-10-01T08:06:15Z',
    upstream_branch: 'dev',
    is_detached: false,
    is_conflicted: false,
    is_syncing: false,
    staged_count: 2,
    unstaged_count: 1,
    untracked_count: 1,
    total_modified_files: 4,
    working_tree: {
      staged: [],
      unstaged: [],
      untracked: [],
      conflicts: [],
    },
    captured_at_utc: '2026-10-01T08:42:00Z',
  }

  it('DebeRenderizarRamaActivaYBaseSincronizada', () => {
    // Act
    const wrapper = mount(GitTelemetryOverview, {
      props: { status: mockStatus },
    })

    // Assert
    expect(wrapper.text()).toContain('feat/004-HU_panel_telemetria_control_versiones_git')
    expect(wrapper.text()).toContain('Sincronizada con base: dev')
  })

  it('DebeRenderizarCommitHeadYAutor', () => {
    // Act
    const wrapper = mount(GitTelemetryOverview, {
      props: { status: mockStatus },
    })

    // Assert
    expect(wrapper.text()).toContain('a7c4e91')
    expect(wrapper.text()).toContain('feat(git): add spec for telemetry panel')
    expect(wrapper.text()).toContain('Business Analyst')
  })

  it('DebeRenderizarDesgloseDeArchivosMutados', () => {
    // Act
    const wrapper = mount(GitTelemetryOverview, {
      props: { status: mockStatus },
    })

    // Assert
    expect(wrapper.text()).toContain('4 Archivos Mutados')
    expect(wrapper.text()).toContain('2 Staged')
    expect(wrapper.text()).toContain('1 Unstaged')
    expect(wrapper.text()).toContain('1 Untracked')
  })

  it('AlHacerClicEnBotonRefrescar_DebeEmitirRefresh', async () => {
    // Act
    const wrapper = mount(GitTelemetryOverview, {
      props: { status: mockStatus },
    })

    const refreshBtn = wrapper.find('button[title="Actualizar telemetría Git"]')
    await refreshBtn.trigger('click')

    // Assert
    expect(wrapper.emitted('refresh')).toBeTruthy()
  })

  it('AlEstarEnEstadoDetachedOConflicted_DebeMostrarBadgesEspeciales', () => {
    // Arrange
    const specialStatus: GitStatusResponse = {
      ...mockStatus,
      is_detached: true,
      is_conflicted: true,
      is_syncing: true,
    }

    // Act
    const wrapper = mount(GitTelemetryOverview, {
      props: { status: specialStatus },
    })

    // Assert
    expect(wrapper.text()).toContain('[DETACHED HEAD]')
    expect(wrapper.text()).toContain('[CONFLICTO DE FUSIÓN]')
    expect(wrapper.text()).toContain('[SINCRONIZANDO]')
  })
})
