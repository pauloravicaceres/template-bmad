import os

filepath = "watcher_bmad.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

broken_block1 = "print(\"\n\" + \"=\" * 80)"
fixed_block1 = "print(\"\\n\" + \"=\" * 80)"
content = content.replace(broken_block1, fixed_block1)

broken_block2 = "print(f\"Iniciando SDD Fase de Implementación...\n\")"
fixed_block2 = "print(f\"Iniciando SDD Fase de Implementación...\\n\")"
content = content.replace(broken_block2, fixed_block2)

# I should use regex to replace all literal newlines inside prints
# Actually, the simplest is just to replace the whole block again safely using python strings.
