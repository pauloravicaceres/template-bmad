import os

filepath = "bmad-control-center/backend/api/routes.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("anlisis", "análisis")
content = content.replace("estratgico", "estratégico")
content = content.replace("creacin", "creación")
content = content.replace("redaccin", "redacción")
content = content.replace("auditora", "auditoría")
content = content.replace("xito", "éxito")
content = content.replace("diseo", "diseño")
content = content.replace("tecnolgico", "tecnológico")
content = content.replace("arquitectnicas", "arquitectónicas")
content = content.replace("tcnica", "técnica")
content = content.replace("implementacin", "implementación")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)