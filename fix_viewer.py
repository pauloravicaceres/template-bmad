import os
import re

filepath = "bmad-control-center/frontend/components/artifacts/ArtifactViewer.vue"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

broken = "const html = marked.parse(sanitizedPart) as string"
fixed = "const html = marked.parse(sanitizedPart, { breaks: true, gfm: true }) as string"

content = content.replace(broken, fixed)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)