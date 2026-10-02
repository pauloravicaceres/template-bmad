import os

filepath = "bmad-control-center/backend/api/routes.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Swap the lines
old_block = """    lines = [f"\\n### [{dt_str}] HUMANO"]
    lines.append(f"- **Estado:** {payload.action.value}")
    lines.append(f"- **Hora:** {hr_str}")"""

new_block = """    lines = [f"\\n### [{dt_str}] HUMANO"]
    lines.append(f"- **Hora:** {hr_str}")
    lines.append(f"- **Estado:** {payload.action.value}")"""

content = content.replace(old_block, new_block)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)