import os
import re

filepath = "bmad-control-center/frontend/composables/useWorkflow.ts"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

old_array_end = "  { key: 'QT', name: 'QA-Tech Senior', role: 'QA-Tech Senior', order: 8 },\n]"
new_array_end = """  { key: 'QT', name: 'QA-Tech Senior', role: 'QA-Tech Senior', order: 8 },
  { key: 'DEV-BACK', name: 'Dev Backend', role: 'Senior Backend Developer', order: 9 },
  { key: 'DEV-FRONT', name: 'Dev Frontend', role: 'Senior Frontend Developer', order: 10 },
  { key: 'QA-AUTO', name: 'QA Automation', role: 'QA Automation', order: 11 },
  { key: 'CR', name: 'Code Review', role: 'SecOps', order: 12 },
]"""

content = content.replace(old_array_end, new_array_end)
content = content.replace("total_stages: totalStages !== undefined ? totalStages : 8", "total_stages: totalStages !== undefined ? totalStages : 12")
content = content.replace("totalStages = computed<number>(() => workflowState.value?.total_stages || 8)", "totalStages = computed<number>(() => workflowState.value?.total_stages || 12)")
content = content.replace("const totalStages = payload.total_stages !== undefined ? payload.total_stages : 8", "const totalStages = payload.total_stages !== undefined ? payload.total_stages : 12")

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)