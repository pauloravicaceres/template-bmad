import os
import re

filepath = "watcher_bmad.py"
with open(filepath, "r", encoding="utf-8") as f:
    content = f.read()

# I will replace the informative block with GATEKEEPER 3
old_block = """    # Notificación informativa para gatillo de implementacion Spec Kit
    if "@SPEC-KIT:" in linea:
        print("\\n" + "=" * 80)
        print("💡 [GATILLO SDD DETECTADO] ARQUITECTURA TÉCNICA LISTA PARA IMPLEMENTACIÓN")
        print("=" * 80)
        print("El QA Técnico ha certificado y compilado el Tech Design maestro.")
        print("Ejecute en la terminal / CLI de Spec Kit:")
        print("   /speckit.implement")
        print("para iniciar el despacho coordinado de tareas a la Fase D (@DEV-BACK, @DEV-FRONT, @DEVOPS).")
        print("=" * 80 + "\\n")"""

new_block = """    # ==========================================
    # SDD GATEKEEPER 3: Intercepción de QT (Implementación Automática)
    # ==========================================
    if ("@dev-back:" in linea_lower or "@dev-front:" in linea_lower) and "handoff:" in linea_lower:
        print("\\n" + "=" * 80)
        print("💡 [GATILLO SDD DETECTADO] INICIANDO FASE D AUTOMÁTICA")
        print("=" * 80)
        print(f"Iniciando SDD Fase de Implementación...\\n")
        exito = ejecutar_sdd_fase_implementacion()
        if not exito:
            print("❌ [HITL] Fallo en SDD Implementación. Pausando el orquestador.")
        print("=" * 80 + "\\n")
        return []"""

# Replace keeping the original indentations might be tricky with multiline regex.
# Let's use regex.
pattern = re.compile(r'    # Notificaci.n informativa para gatillo de implementacion Spec Kit\n    if "@SPEC-KIT:" in linea:.*?print\("=" \* 80 \+ "\\n"\)', re.DOTALL)
content = re.sub(pattern, new_block, content)

with open(filepath, "w", encoding="utf-8") as f:
    f.write(content)