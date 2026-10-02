import os
import re

filepath = "bmad-control-center/backend/services/workflow_service.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

old_search = "target_match = re.search(r'Handoff:\\s*(@[A-Z\\-]+:)', chunk)\n            if target_match:\n                target = target_match.group(1)[:-1]  # Remove trailing colon"
new_search = "target_matches = re.findall(r'Handoff:\\s*(@[A-Z\\-]+:)', chunk)\n            if target_matches:\n                target = target_matches[-1][:-1]  # Remove trailing colon"

content = content.replace(old_search, new_search)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)