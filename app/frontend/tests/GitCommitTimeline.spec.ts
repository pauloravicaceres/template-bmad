import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import GitCommitTimeline from '../components/git/GitCommitTimeline.vue'
import type { GitCommitItem } from '../types'

describe('GitCommitTimeline Component', () => {
  const mockCommits: GitCommitItem[] = [
    {
      commit_hash: 'a7c4e91d830b8ef29e92d77cb31940918ef83921',
      short_hash: 'a7c4e91',
      author_name: 'Business Analyst',
      author_email: 'ba@bmad.local',
      committed_at: '2026-10-01T08:06:15Z',
      message: 'feat(git): add spec for telemetry panel (HU-004)',
      agent_role: 'Business Analyst',
      files_changed_count: 2,
      insertions: 239,
      deletions: 0,
      files: [
        {
          relative_path: 'files/business-analyst/004-HU_panel.md',
          change_type: 'added',
          is_binary: false,
          is_diff_omitted: false,
          insertions: 144,
          deletions: 0,
        },
        {
          relative_path: 'assets/large_diagram.png',
          change_type: 'modified',
          is_binary: true,
          is_diff_omitted: true,
          insertions: 0,
          deletions: 0,
          size_bytes: 2800000,
        },
      ],
    },
    {
      commit_hash: '9f3e2b0c1a8d4e7f6b5c3d2e1f0a9b8c7d6e5f4a',
      short_hash: '9f3e2b0',
      author_name: 'Watcher BMAD',
      author_email: 'watcher@bmad.local',
      committed_at: '2026-10-01T07:59:45Z',
      message: 'merge: close branch feat/003-HU_observabilidad',
      agent_role: 'Watcher BMAD',
      files_changed_count: 1,
      insertions: 10,
      deletions: 5,
      files: [],
    },
  ]

  it('DebeRenderizarListaDeCommitsYMarcarHead', () => {
    // Act
    const wrapper = mount(GitCommitTimeline, {
      props: {
        commits: mockCommits,
        selectedCommit: mockCommits[0],
        totalCount: 2,
      },
    })

    // Assert
    expect(wrapper.text()).toContain('a7c4e91')
    expect(wrapper.text()).toContain('HEAD')
    expect(wrapper.text()).toContain('feat(git): add spec for telemetry panel (HU-004)')
    expect(wrapper.text()).toContain('Business Analyst')
    expect(wrapper.text()).toContain('9f3e2b0')
    expect(wrapper.text()).toContain('Watcher BMAD')
  })

  it('DebeRenderizarDetalleDelCommitSeleccionadoYArchivosAfectados', () => {
    // Act
    const wrapper = mount(GitCommitTimeline, {
      props: {
        commits: mockCommits,
        selectedCommit: mockCommits[0],
        totalCount: 2,
      },
    })

    // Assert
    expect(wrapper.text()).toContain('Detalle del Commit Seleccionado')
    expect(wrapper.text()).toContain('[ a7c4e91 ]')
    expect(wrapper.text()).toContain('a7c4e91d830b8ef29e92d77cb31940918ef83921')
    expect(wrapper.text()).toContain('ba@bmad.local')
    expect(wrapper.text()).toContain('+239')
    expect(wrapper.text()).toContain('files/business-analyst/004-HU_panel.md')
    // Elisión de diff binario
    expect(wrapper.text()).toContain('[ ARCHIVO BINARIO - DIFF TEXTUAL OMITIDO ]')
  })

  it('AlFiltrarPorInputDeBusqueda_DebeMostrarSoloCoincidencias', async () => {
    // Act
    const wrapper = mount(GitCommitTimeline, {
      props: {
        commits: mockCommits,
        selectedCommit: mockCommits[0],
        totalCount: 2,
      },
    })

    const input = wrapper.find('input[type="text"]')
    await input.setValue('merge')

    // Assert
    expect(wrapper.text()).toContain('9f3e2b0')
    expect(wrapper.text()).not.toContain('a7c4e91 [HEAD]')
  })

  it('AlHacerClicEnCommit_DebeEmitirSelectCommit', async () => {
    // Act
    const wrapper = mount(GitCommitTimeline, {
      props: {
        commits: mockCommits,
        selectedCommit: mockCommits[0],
        totalCount: 2,
      },
    })

    const secondCommitEl = wrapper.findAll('.cursor-pointer').find((el) => el.text().includes('9f3e2b0'))
    await secondCommitEl?.trigger('click')

    // Assert
    expect(wrapper.emitted('select-commit')).toBeTruthy()
    expect(wrapper.emitted('select-commit')?.[0]).toEqual([mockCommits[1]])
  })

  it('AlHacerClicEnBotonesPaginacion_DebeEmitirEventosCorrespondientes', async () => {
    // Act
    const wrapper = mount(GitCommitTimeline, {
      props: {
        commits: mockCommits,
        selectedCommit: mockCommits[0],
        totalCount: 150,
        page: 2,
        totalPages: 3,
        hasMore: true,
      },
    })

    const prevBtn = wrapper.findAll('button').find((b) => b.text().includes('◀ Anterior'))
    const nextBtn = wrapper.findAll('button').find((b) => b.text().includes('Siguiente ▶'))
    const firstBtn = wrapper.findAll('button').find((b) => b.text().includes('◀◀ Primera'))
    const lastBtn = wrapper.findAll('button').find((b) => b.text().includes('Última ▶▶'))
    const loadMoreBtn = wrapper.findAll('button').find((b) => b.text().includes('⚡ Cargar 50 Más'))

    await prevBtn?.trigger('click')
    expect(wrapper.emitted('prev-page')).toBeTruthy()

    await nextBtn?.trigger('click')
    expect(wrapper.emitted('next-page')).toBeTruthy()

    await firstBtn?.trigger('click')
    expect(wrapper.emitted('go-to-page')?.[0]).toEqual([1])

    await lastBtn?.trigger('click')
    expect(wrapper.emitted('go-to-page')?.[1]).toEqual([3])

    await loadMoreBtn?.trigger('click')
    expect(wrapper.emitted('load-more')).toBeTruthy()
  })
})
