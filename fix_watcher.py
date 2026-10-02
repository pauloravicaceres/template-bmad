import re

filepath = "watcher_bmad.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Fix the broken string block
broken_str = """    block = f"
### [{dt_str}] WATCHER
- **Hora:** {hr_str}
- **Mensaje:** {mensaje}
\""""

fixed_str = """    block = f"\\n### [{dt_str}] WATCHER\\n- **Hora:** {hr_str}\\n- **Mensaje:** {mensaje}\\n\""""

content = content.replace(broken_str, fixed_str)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)