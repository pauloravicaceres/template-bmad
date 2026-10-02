import re

filepath = "watcher_bmad.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix literal newlines in the injected GK3
content = content.replace("print(\"\n\" + \"=\" * 80)", "print(\"\\n\" + \"=\" * 80)")
content = content.replace("print(f\"Iniciando SDD Fase de Implementación...\n\")", "print(f\"Iniciando SDD Fase de Implementación...\\n\")")
content = content.replace("print(\"=\" * 80 + \"\n\")", "print(\"=\" * 80 + \"\\n\")")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)