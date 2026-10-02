import os
import re

filepath = "bmad-control-center/frontend/services/api_client.ts"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

pattern = re.compile(r"const url = `\$\{apiBase\}/artifacts/content\?path=\$\{encodeURIComponent\(filePath\)\}`\s*const response = await fetch\(url, \{\s*headers: \{ Accept: 'application/json' \},\s*\}\)")

new_code = """const url = `${apiBase}/artifacts/content?path=${encodeURIComponent(filePath)}&_t=${Date.now()}`
    const response = await fetch(url, {
      headers: { Accept: 'application/json', 'Cache-Control': 'no-cache' },
      cache: 'no-store'
    })"""

content = re.sub(pattern, new_code, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)