import sys
from pathlib import Path

path = Path("app/backend/services/workflow_service.py")
content = path.read_text(encoding="utf-8")

old_can = """CANONICAL_STAGES = [
    {"key": "PM", "name": "Product Manager", "role": "Product Manager", "order": 1},
    {"key": "BA", "name": "Business Analyst", "role": "Business Analyst", "order": 2},
    {"key": "QA", "name": "QA Documental", "role": "QA Documental", "order": 3},
    {"key": "UX", "name": "Designer UX", "role": "Designer UX", "order": 4},
    {"key": "SA", "name": "Solutions Architect", "role": "Solutions Architect", "order": 5},
    {"key": "DA", "name": "Data Architect", "role": "Data Architect", "order": 6},
    {"key": "API", "name": "API Architect", "role": "API Architect", "order": 7},
    {"key": "QT", "name": "QA-Tech Senior", "role": "QA-Tech Senior", "order": 8},
]"""

new_can = """CANONICAL_STAGES = [
    {"key": "PM", "name": "Product Manager", "role": "Product Manager", "order": 1},
    {"key": "BA", "name": "Business Analyst", "role": "Business Analyst", "order": 2},
    {"key": "QA", "name": "QA Documental", "role": "QA Documental", "order": 3},
    {"key": "UX", "name": "Designer UX", "role": "Designer UX", "order": 4},
    {"key": "SA", "name": "Solutions Architect", "role": "Solutions Architect", "order": 5},
    {"key": "DA", "name": "Data Architect", "role": "Data Architect", "order": 6},
    {"key": "API", "name": "API Architect", "role": "API Architect", "order": 7},
    {"key": "QT", "name": "QA-Tech Senior", "role": "QA-Tech Senior", "order": 8},
    {"key": "DEV-BACK", "name": "Dev Backend", "role": "Senior Backend Developer", "order": 9},
    {"key": "DEV-FRONT", "name": "Dev Frontend", "role": "Senior Frontend Developer", "order": 10},
    {"key": "QA-AUTO", "name": "QA Automation", "role": "QA Automation", "order": 11},
    {"key": "CR", "name": "Code Review", "role": "SecOps", "order": 12},
]"""
content = content.replace(old_can, new_can)

old_role = """ROLE_TO_KEY = {
    "Product Manager": "PM",
    "Business Analyst": "BA",
    "QA Documental": "QA",
    "Designer UX": "UX",
    "Solutions Architect": "SA",
    "Data Architect": "DA",
    "API Architect": "API",
    "QA-Tech Senior": "QT",
    "QA-Tech": "QT",
}"""

new_role = """ROLE_TO_KEY = {
    "Product Manager": "PM",
    "Business Analyst": "BA",
    "QA Documental": "QA",
    "Designer UX": "UX",
    "Solutions Architect": "SA",
    "Data Architect": "DA",
    "API Architect": "API",
    "QA-Tech Senior": "QT",
    "QA-Tech": "QT",
    "Senior Backend Developer": "DEV-BACK",
    "Senior Frontend Developer": "DEV-FRONT",
    "QA Automation": "QA-AUTO",
    "SecOps": "CR",
}"""
content = content.replace(old_role, new_role)

old_token = """TOKEN_TO_KEY = {
    "PM": "PM",
    "BA": "BA",
    "QA": "QA",
    "UX": "UX",
    "SA": "SA",
    "DA": "DA",
    "API": "API",
    "QT": "QT",
    "HUMANO": "HUMANO",
}"""

new_token = """TOKEN_TO_KEY = {
    "PM": "PM",
    "BA": "BA",
    "QA": "QA",
    "UX": "UX",
    "SA": "SA",
    "DA": "DA",
    "API": "API",
    "QT": "QT",
    "DEV-BACK": "DEV-BACK",
    "DEV-FRONT": "DEV-FRONT",
    "QA-AUTO": "QA-AUTO",
    "CODE-REVIEW": "CR",
    "CR": "CR",
    "HUMANO": "HUMANO",
}"""
content = content.replace(old_token, new_token)

import re
content = re.sub(
    r'# Check if all completed \(e\.g\. QT hands off to SPEC-KIT or DEV-BACK\).*?overall_status = "COMPLETED"',
    r'# Check if all completed (e.g. Code Review hands off to WATCHER or PM)\n            if last_block["author_role"] == "SecOps" and target in ["WATCHER", "PM"]:\n                overall_status = "COMPLETED"',
    content,
    flags=re.DOTALL
)

content = content.replace("if completed_count == 8:", "if completed_count >= len(CANONICAL_STAGES):")
content = content.replace("total_stages=8,", "total_stages=len(CANONICAL_STAGES),")

path.write_text(content, encoding="utf-8")
print("Updated successfully")