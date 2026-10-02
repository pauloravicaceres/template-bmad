import sys
from pathlib import Path

content = Path("watcher_bmad.py").read_text(encoding="utf-8")

old_back = """                try:
                print("🏃 [SpecKit] Ejecutando implementación de Backend...")
                with open(TRACKER_PATH, "a", encoding="utf-8") as f:
                    f.write("\\n@WATCHER: ⚡ [SDD Auto-Runner] Ejecutando implementación Backend (/speckit.implement)...\\n")
                
                subprocess.run('agy --dangerously-skip-permissions --print "/speckit.implement"', shell=True, check=True, cwd=DIRECTORIO_RAIZ)"""

new_back = """                try:
                print("🏃 [SpecKit] Ejecutando implementación de Backend...")
                with open(TRACKER_PATH, "a", encoding="utf-8") as f:
                    f.write("\\n@WATCHER: ⚡ [SDD Auto-Runner] Ejecutando implementación Backend (/speckit.implement)...\\n")
                
                subprocess.run('agy --dangerously-skip-permissions --print "/speckit.implement"', shell=True, check=True, cwd=DIRECTORIO_RAIZ)
                
                from datetime import datetime
                dt_str = datetime.now().strftime("%d-%m-%Y")
                hr_str = datetime.now().strftime("%H:%M:%S")
                handoff_target = "@DEV-FRONT:" if involucra_frontend else "@CODE-REVIEW:"
                handoff_text = "Inicia implementación frontend." if involucra_frontend else "Backend completado sin frontend."
                block = f\"\"\"
### [{dt_str}] Senior Backend Developer
- **Hora:** {hr_str}
- **Artefacto generado:** `backend-architecture.md`
- **Estado:** Implementación backend finalizada exitosamente mediante SDD SpecKit.
- **Handoff:** {handoff_target} {handoff_text}
\"\"\"
                with open(TRACKER_PATH, "a", encoding="utf-8") as f:
                    f.write(block)"""

content = content.replace(old_back, new_back)

old_front = """                try:
                print("🏃 [SpecKit] Ejecutando implementación de Frontend...")
                with open(TRACKER_PATH, "a", encoding="utf-8") as f:
                    f.write("\\n@WATCHER: ⚡ [SDD Auto-Runner] Ejecutando implementación Frontend (/speckit.implement)...\\n")
                
                subprocess.run('agy --dangerously-skip-permissions --print "/speckit.implement"', shell=True, check=True, cwd=DIRECTORIO_RAIZ)"""

new_front = """                try:
                print("🏃 [SpecKit] Ejecutando implementación de Frontend...")
                with open(TRACKER_PATH, "a", encoding="utf-8") as f:
                    f.write("\\n@WATCHER: ⚡ [SDD Auto-Runner] Ejecutando implementación Frontend (/speckit.implement)...\\n")
                
                subprocess.run('agy --dangerously-skip-permissions --print "/speckit.implement"', shell=True, check=True, cwd=DIRECTORIO_RAIZ)
                
                from datetime import datetime
                dt_str = datetime.now().strftime("%d-%m-%Y")
                hr_str = datetime.now().strftime("%H:%M:%S")
                block = f\"\"\"
### [{dt_str}] Senior Frontend Developer
- **Hora:** {hr_str}
- **Artefacto generado:** `frontend-architecture.md`
- **Estado:** Implementación frontend finalizada exitosamente mediante SDD SpecKit.
- **Handoff:** @CODE-REVIEW: Procede con la auditoría.
\"\"\"
                with open(TRACKER_PATH, "a", encoding="utf-8") as f:
                    f.write(block)"""

content = content.replace(old_front, new_front)

Path("watcher_bmad.py").write_text(content, encoding="utf-8")