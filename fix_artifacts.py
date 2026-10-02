import os
import re

filepath = "bmad-control-center/frontend/composables/useArtifacts.ts"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# I will find handleArtifactChanged and inject the reload logic at the end.
# Look for "return\n    }\n  }" and replace.
# Wait, let's just find the end of handleArtifactChanged.

match_str = r"""      if \(payload\.change_type === 'deleted' && selectedPath\.value === payload\.relative_path\) \{\s*artifactContent\.value = null\s*contentError\.value = new ApiClientError\([^)]+\)\s*return\s*\}"""

def replacer(match):
    return match.group(0) + """
    
    // Si el artefacto mutado es el que estamos visualizando actualmente, lo recargamos automáticamente en vivo
    if (payload.change_type !== 'deleted' && selectedPath.value === payload.relative_path) {
      // Mantenemos el mismo selectedPath pero obligamos la recarga de contenido
      await selectArtifact(selectedPath.value, selectedNode.value || undefined)
    }"""

content = re.sub(match_str, replacer, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)