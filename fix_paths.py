import os
import re

filepath = "watcher_bmad.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace backend ghost task
old_back = """Luego, abre el archivo backend-architecture.md."""
new_back = """Luego, crea o edita obligatoriamente el archivo 'files/dev-backend/backend-architecture.md'."""
content = content.replace(old_back, new_back)

# Replace frontend ghost task
old_front = """Luego, abre el archivo frontend-architecture.md."""
new_front = """Luego, crea o edita obligatoriamente el archivo 'files/dev-frontend/frontend-architecture.md'."""
content = content.replace(old_front, new_front)

# Fix the tracker output strings so they map correctly to the tree
old_back_tracker = """- **Artefacto generado:** `backend-architecture.md`"""
new_back_tracker = """- **Artefacto generado:** `files/dev-backend/backend-architecture.md`"""
content = content.replace(old_back_tracker, new_back_tracker)

old_front_tracker = """- **Artefacto generado:** `frontend-architecture.md`"""
new_front_tracker = """- **Artefacto generado:** `files/dev-frontend/frontend-architecture.md`"""
content = content.replace(old_front_tracker, new_front_tracker)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)