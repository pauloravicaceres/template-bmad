import os

filepath = "bmad-control-center/frontend/components/artifacts/ArtifactViewer.vue"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

injection = """  let raw = props.artifact.raw_content

  // [REQUERIMIENTO] Invertir orden del tracker (acciones recientes primero)
  if (props.artifact.filename === 'tracker_bmad.md' || props.artifact.relative_path.includes('tracker_bmad.md')) {
    const blocks = raw.split(/(?=^###\\s+\\[)/m)
    // Reordenar: bloques con ### primero (en orden inverso), y cualquier texto inicial al final
    raw = blocks.reverse().join('\\n---\\n\\n') // Add a separator for better readability if desired, or just join('\\n')
  }"""

content = content.replace("  const raw = props.artifact.raw_content", injection)
# Change let to let if it already had const? Wait, I am replacing the exact string "  const raw = props.artifact.raw_content".

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)