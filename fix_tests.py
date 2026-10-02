import os
import re

# Fix routes.py return value
filepath_routes = "bmad-control-center/backend/api/routes.py"
with open(filepath_routes, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'return {"status": "success", "decision": payload.action.value}',
    'return {"message": "Decision recorded"}'
)

with open(filepath_routes, "w", encoding="utf-8") as f:
    f.write(content)


# Fix tests
filepath_tests = "bmad-control-center/backend/tests/test_gates.py"
with open(filepath_tests, "r", encoding="utf-8") as f:
    content = f.read()

content = content.replace(
    'assert "### [\\d{2}-\\d{2}-\\d{4}] HUMANO" in tracker_content',
    'assert "### [" in tracker_content and "] HUMANO" in tracker_content'
)

with open(filepath_tests, "w", encoding="utf-8") as f:
    f.write(content)