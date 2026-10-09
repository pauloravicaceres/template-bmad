import { describe, it, expect } from 'vitest'
import { mount } from '@vue/test-utils'
import ArtifactTreeExplorer from '../components/artifacts/ArtifactTreeExplorer.vue'
import type { DirectoryNode } from '../types'

describe('ArtifactTreeExplorer Component', () => {
  const mockTree: DirectoryNode = {
    node_id: 'workspace_root',
    name: 'root',
    node_type: 'DIRECTORY',
    relative_path: '',
    parent_path: null,
    child_file_count: 0,
    is_empty: false,
    last_modified: '2026-09-30T23:36:50Z',
    children: [
      {
        node_id: 'documents',
        name: 'documents',
        node_type: 'DIRECTORY',
        relative_path: 'documents',
        parent_path: '',
        child_file_count: 1,
        is_empty: false,
        last_modified: '2026-09-30T23:36:50Z',
        children: [
          {
            node_id: 'documents/business-analyst',
            name: 'business-analyst',
            node_type: 'DIRECTORY',
            relative_path: 'documents/business-analyst',
            parent_path: 'documents',
            child_file_count: 1,
            is_empty: false,
            last_modified: '2026-09-30T23:14:00Z',
            children: [
              {
                node_id: 'documents/business-analyst/002-HU_monitoreo.md',
                name: '002-HU_monitoreo.md',
                node_type: 'FILE',
                relative_path: 'documents/business-analyst/002-HU_monitoreo.md',
                parent_path: 'documents/business-analyst',
                child_file_count: 0,
                is_empty: false,
                last_modified: '2026-09-30T23:14:00Z',
                children: [],
              },
            ],
          },
          {
            node_id: 'documents/empty-agent',
            name: 'empty-agent',
            node_type: 'DIRECTORY',
            relative_path: 'documents/empty-agent',
            parent_path: 'documents',
            child_file_count: 0,
            is_empty: true,
            last_modified: '2026-09-30T23:20:00Z',
            children: [],
          },
        ],
      },
    ],
  }

  it('DebeRenderizarEstructuraDeCarpetasYBadgesDeConteo', () => {
    // Act
    const wrapper = mount(ArtifactTreeExplorer, {
      props: {
        rootNode: mockTree,
        selectedPath: null,
      },
    })

    // Assert
    expect(wrapper.text()).toContain('Explorador de Artefactos')
    expect(wrapper.text()).toContain('documents')
    expect(wrapper.text()).toContain('business-analyst')
    expect(wrapper.text()).toContain('empty-agent')
    expect(wrapper.text()).toMatch(/empty-agent\s*\(0\)/)
  })

  it('AlEscribirEnFiltroDeBusqueda_DebeFiltrarNodosCoincidentes', async () => {
    // Act
    const wrapper = mount(ArtifactTreeExplorer, {
      props: {
        rootNode: mockTree,
        selectedPath: null,
      },
    })

    const input = wrapper.find('input[type="text"]')
    await input.setValue('002-HU')

    // Assert
    expect(wrapper.text()).toContain('002-HU_monitoreo.md')
    expect(wrapper.text()).not.toContain('empty-agent')
  })

  it('AlHacerClicEnBotonRefrescar_DebeEmitirRefresh', async () => {
    // Act
    const wrapper = mount(ArtifactTreeExplorer, {
      props: {
        rootNode: mockTree,
        selectedPath: null,
      },
    })

    const refreshButton = wrapper.find('button[title="Actualizar árbol de artefactos"]')
    await refreshButton.trigger('click')

    // Assert
    expect(wrapper.emitted('refresh')).toBeTruthy()
  })

  it('AlRecibirPathEnNewPaths_DebeRenderizarBadgeNuevo', async () => {
    // Act
    const newPaths = new Set(['documents/business-analyst/002-HU_monitoreo.md'])
    const wrapper = mount(ArtifactTreeExplorer, {
      props: {
        rootNode: mockTree,
        selectedPath: null,
        newPaths,
      },
    })

    // Expand business-analyst directory
    const dir = wrapper.findAll('span').find(el => el.text().includes('business-analyst'))
    if (dir) {
      await dir.trigger('click')
    }

    // Assert
    expect(wrapper.text()).toContain('[✨ NUEVO]')
  })

  it('NoDebeMostrarLaCarpetaSpecifyEnElArbol', () => {
    const treeWithSpecify: DirectoryNode = {
      ...mockTree,
      children: [
        ...mockTree.children!,
        {
          node_id: '.specify',
          name: '.specify',
          node_type: 'DIRECTORY',
          relative_path: '.specify',
          parent_path: '',
          child_file_count: 1,
          is_empty: false,
          last_modified: '2026-09-30T23:36:50Z',
          children: [],
        },
      ],
    }

    const wrapper = mount(ArtifactTreeExplorer, {
      props: {
        rootNode: treeWithSpecify,
        selectedPath: null,
      },
    })

    expect(wrapper.text()).not.toContain('.specify')
  })
})

