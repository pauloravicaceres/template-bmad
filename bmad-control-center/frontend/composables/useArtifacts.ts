import { ref, computed } from 'vue'
import type {
  DirectoryNode,
  ArtifactContent,
  ArtifactTreeChangedPayload,
  ArtifactChangedPayload,
  FileMetadataRecord,
} from '../types'
import {
  fetchArtifactsTree,
  fetchArtifactContent,
  ApiClientError,
} from '../services/api_client'

export function useArtifacts(apiBase?: string) {
  const tree = ref<DirectoryNode | null>(null)
  const isLoadingTree = ref<boolean>(false)
  const treeError = ref<string | null>(null)

  const selectedPath = ref<string | null>(null)
  const selectedNode = ref<DirectoryNode | null>(null)
  const artifactContent = ref<ArtifactContent | null>(null)
  const isLoadingContent = ref<boolean>(false)
  const contentError = ref<ApiClientError | null>(null)
  const lastValidPath = ref<string | null>(null)

  // HU-003: Estado reactivo de artefactos mutados recientemente y archivos masivos (>5MB)
  const recentlyMutatedPaths = ref<Set<string>>(new Set())
  const largeFileMetadata = ref<FileMetadataRecord | null>(null)

  const isFolderSelected = computed<boolean>(() => {
    return selectedNode.value?.node_type === 'DIRECTORY'
  })

  const isEmptyFolder = computed<boolean>(() => {
    return (
      selectedNode.value?.node_type === 'DIRECTORY' &&
      (selectedNode.value.is_empty || selectedNode.value.child_file_count === 0)
    )
  })

  const is404Error = computed<boolean>(() => {
    return (
      contentError.value?.statusCode === 404 ||
      contentError.value?.errorCode === 'ARTIFACT_NOT_FOUND'
    )
  })

  const is403Error = computed<boolean>(() => {
    return (
      contentError.value?.statusCode === 403 ||
      contentError.value?.errorCode === 'PATH_TRAVERSAL_DETECTED'
    )
  })

  const is413Error = computed<boolean>(() => {
    return (
      contentError.value?.statusCode === 413 ||
      contentError.value?.errorCode === 'PAYLOAD_TOO_LARGE'
    )
  })

  const is415Error = computed<boolean>(() => {
    return (
      contentError.value?.statusCode === 415 ||
      contentError.value?.errorCode === 'UNSUPPORTED_MEDIA_TYPE'
    )
  })

  const loadTree = async (root = 'all'): Promise<void> => {
    isLoadingTree.value = true
    treeError.value = null
    try {
      const response = await fetchArtifactsTree(root, apiBase)
      tree.value = response.root_node
    } catch (err: unknown) {
      treeError.value = err instanceof Error ? err.message : 'Error al cargar el árbol de artefactos'
    } finally {
      isLoadingTree.value = false
    }
  }

  const selectArtifact = async (path: string, node?: DirectoryNode): Promise<void> => {
    selectedPath.value = path
    if (node) {
      selectedNode.value = node
    }

    if (node && node.node_type === 'DIRECTORY') {
      artifactContent.value = null
      contentError.value = null
      largeFileMetadata.value = null
      return
    }

    isLoadingContent.value = true
    contentError.value = null
    largeFileMetadata.value = null

    try {
      const data = await fetchArtifactContent(path, apiBase)
      artifactContent.value = data
      lastValidPath.value = path
    } catch (err: unknown) {
      artifactContent.value = null
      if (err instanceof ApiClientError) {
        contentError.value = err
        if (err.statusCode === 404 || err.errorCode === 'ARTIFACT_NOT_FOUND') {
          // Auto-sync automático del árbol según criterio SC-02 / ADR-02 UX
          loadTree().catch(() => {})
        }
      } else {
        contentError.value = new ApiClientError(
          err instanceof Error ? err.message : 'Error de lectura de archivo',
          'UNKNOWN_ERROR',
          500,
          new Date().toISOString(),
          path
        )
      }
    } finally {
      isLoadingContent.value = false
    }
  }

  const revertToLastValid = async (): Promise<void> => {
    if (lastValidPath.value) {
      await selectArtifact(lastValidPath.value)
    }
  }

  const handleTreeChanged = async (_payload?: ArtifactTreeChangedPayload): Promise<void> => {
    await loadTree()
  }

  const handleArtifactChanged = async (payload: ArtifactChangedPayload): Promise<void> => {
    // Registrar path mutado para el tag [? NUEVO] (Estado 2 UX)
    recentlyMutatedPaths.value.add(payload.relative_path)
    setTimeout(() => {
      recentlyMutatedPaths.value.delete(payload.relative_path)
    }, 5000)

    // Refrescar el arbol
    await loadTree()

    // Manejo de eliminacion en caliente
    if (payload.change_type === 'deleted' && (selectedPath.value === payload.relative_path || (selectedPath.value && payload.relative_path.endsWith('/' + selectedPath.value)))) {
      artifactContent.value = null
      contentError.value = new ApiClientError(
        `El artefacto '${payload.relative_path}' fue eliminado.`,
        'ARTIFACT_NOT_FOUND',
        404,
        new Date().toISOString(),
        payload.relative_path
      )
      return
    }

    // Manejo de archivo masivo (>5MB / Metadata-Only ADR-012)
    if (
      (payload.file_metadata?.is_large_file || payload.file_metadata?.metadata_only) &&
      (selectedPath.value === payload.relative_path || (selectedPath.value && payload.relative_path.endsWith('/' + selectedPath.value)))
    ) {
      largeFileMetadata.value = payload.file_metadata
      artifactContent.value = null
      return
    }

    // Si el usuario tiene el visor abierto en el archivo modificado, recargar en caliente (SC-02)
    // Usamos endsWith / includes para tolerar paths parciales como "tracker_bmad.md" vs "docs/tracker_bmad.md"
    const currentPath = selectedPath.value
    if (
      currentPath &&
      (payload.relative_path === currentPath ||
        payload.relative_path.endsWith('/' + currentPath) ||
        currentPath.endsWith('/' + payload.relative_path) ||
        (currentPath.includes('tracker_bmad.md') && payload.relative_path.includes('tracker_bmad.md')))
    ) {
      await selectArtifact(currentPath, selectedNode.value || undefined)
    }
  }

  return {
    tree,
    isLoadingTree,
    treeError,
    selectedPath,
    selectedNode,
    artifactContent,
    isLoadingContent,
    contentError,
    lastValidPath,
    recentlyMutatedPaths,
    largeFileMetadata,
    isFolderSelected,
    isEmptyFolder,
    is404Error,
    is403Error,
    is413Error,
    is415Error,
    loadTree,
    selectArtifact,
    revertToLastValid,
    handleTreeChanged,
    handleArtifactChanged,
  }
}
