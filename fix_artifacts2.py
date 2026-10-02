import os

filepath = "bmad-control-center/frontend/composables/useArtifacts.ts"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

broken = "if (selectedPath.value && payload.relative_path === selectedPath.value) {"
fixed = """if (
      selectedPath.value && 
      (payload.relative_path === selectedPath.value || 
       payload.relative_path.endsWith('/' + selectedPath.value) ||
       selectedPath.value.endsWith('/' + payload.relative_path))
    ) {"""

content = content.replace(broken, fixed)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)