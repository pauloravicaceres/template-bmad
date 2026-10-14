import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import GitWorkingTreeClassifier from '../components/git/GitWorkingTreeClassifier.vue'
import type { GitWorkingTree } from '../types'

describe('GitWorkingTreeClassifier Component', () => {
  const mockTree: GitWorkingTree = {
    staged: [
      {
        relative_path: 'docs/business-analyst/004-HU_panel_telemetria.md',
        category: 'staged',
        status_code: '+',
        lines_added: 144,
        lines_deleted: 0,
      },
    ],
    unstaged: [
      {
        relative_path: 'docs/tracker_bmad.md',
        category: 'unstaged',
        status_code: 'M',
      },
    ],
    untracked: [
      {
        relative_path: 'docs/qa-documental/aprobado_qa.md',
        category: 'untracked',
        status_code: '??',
      },
    ],
    conflicts: [],
  }

  it('DebeMostrarMensajeLimpioSiNoHayArchivos', () => {
    // Act
    const wrapper = mount(GitWorkingTreeClassifier, {
      props: {
        workingTree: {
          staged: [],
          unstaged: [],
          untracked: [],
          conflicts: [],
        },
      },
    })

    // Assert
    expect(wrapper.text()).toContain('Repositorio limpio')
  })

  it('DebeRenderizarCategoriasStagedUnstagedYUntrackedConConteo', () => {
    // Act
    const wrapper = mount(GitWorkingTreeClassifier, {
      props: { workingTree: mockTree },
    })

    // Assert
    expect(wrapper.text()).toContain('STAGED CHANGES (1)')
    expect(wrapper.text()).toContain('UNSTAGED CHANGES (1)')
    expect(wrapper.text()).toContain('UNTRACKED FILES (1)')
    expect(wrapper.text()).toContain('004-HU_panel_telemetria.md')
    expect(wrapper.text()).toContain('+144')
    expect(wrapper.text()).toContain('tracker_bmad.md')
    expect(wrapper.text()).toContain('aprobado_qa.md')
  })

  it('AlHaberConflictos_DebeRenderizarSeccionDeConflictos', () => {
    // Arrange
    const treeWithConflicts: GitWorkingTree = {
      ...mockTree,
      conflicts: [
        {
          relative_path: 'specs/004-panel-telemetria-git/spec.md',
          category: 'conflict',
          status_code: 'UU',
        },
      ],
    }

    // Act
    const wrapper = mount(GitWorkingTreeClassifier, {
      props: { workingTree: treeWithConflicts },
    })

    // Assert
    expect(wrapper.text()).toContain('ARCHIVOS EN CONFLICTO (1)')
    expect(wrapper.text()).toContain('Requiere resolución humana')
    expect(wrapper.text()).toContain('spec.md')
  })

  it('AlHacerClicEnEncabezadoDeAcordeon_DebeAlternarVisibilidad', async () => {
    // Act
    const wrapper = mount(GitWorkingTreeClassifier, {
      props: { workingTree: mockTree },
    })

    const stagedHeader = wrapper.findAll('button').find((b) => b.text().includes('STAGED CHANGES'))
    expect(wrapper.text()).toContain('004-HU_panel_telemetria.md')

    // Click to collapse
    await stagedHeader?.trigger('click')
    expect(wrapper.text()).not.toContain('004-HU_panel_telemetria.md')

    // Click to expand again
    await stagedHeader?.trigger('click')
    expect(wrapper.text()).toContain('004-HU_panel_telemetria.md')
  })
})
