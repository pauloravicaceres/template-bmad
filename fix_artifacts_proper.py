import os
import re

filepath = "bmad-control-center/frontend/composables/useArtifacts.ts"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Buscamos la funcion handleArtifactChanged
pattern = re.compile(r"const handleArtifactChanged = async \(payload: ArtifactChangedPayload\): Promise<void> => \{.*?\n  \}", re.DOTALL)

new_func = """const handleArtifactChanged = async (payload: ArtifactChangedPayload): Promise<void> => {
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
    // Usamos endsWith para tolerar paths parciales como "tracker_bmad.md" vs "files/tracker_bmad.md"
    const currentPath = selectedPath.value
    if (currentPath && (payload.relative_path === currentPath || payload.relative_path.endsWith('/' + currentPath) || currentPath.endsWith('/' + payload.relative_path))) {
      await selectArtifact(currentPath, selectedNode.value || undefined)
    }
  }"""

content = re.sub(pattern, new_func, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)