import os
import re

filepath = "bmad-control-center/backend/tests/test_workflow_api.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Replace QA-Tech with Code Review for completion test
content = re.sub(r'QA-Tech Senior', r'SecOps', content)
content = re.sub(r'@SPEC-KIT: Gatillar /speckit\.implement', r'@HUMANO: Fin', content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)