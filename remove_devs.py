import os
import re

filepath = "watcher_bmad.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# Remove the DEV-BACK and DEV-FRONT entries
content = re.sub(r'\s*"@DEV-BACK:": "dev-backend",', '', content)
content = re.sub(r'\s*"@DEV-BACKEND:": "dev-backend",', '', content)
content = re.sub(r'\s*"@DEV-FRONT:": "dev-frontend",', '', content)
content = re.sub(r'\s*"@DEV-FRONTEND:": "dev-frontend",', '', content)
content = re.sub(r'\s*"@DEV:": "dev-backend",?', '', content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)