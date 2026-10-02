import os

filepath = "bmad-control-center/backend/tests/test_gates.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace("Feedback: Subsanar", "**Feedback:** Subsanar")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)