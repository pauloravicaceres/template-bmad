import sys
import re
from pathlib import Path

content = Path("watcher_bmad.py").read_text(encoding="utf-8")

sdd_impl_func = """def ejecutar_sdd_fase_implementacion():
    \"\"\"
    Hito 3 del SDD Auto-Runner: Fase D (Implementación) usando SpecKit + Soul Mounting.
    \"\"\"
    print(f"\\n⚙️ [SDD Implementación] Iniciando Fase D (Fuerza Bruta + Alma Agéntica)...")
    import json
    import subprocess
    try:
        memory_dir = DIRECTORIO_RAIZ / ".specify" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        active_directive_path = memory_dir / "active_agent_directive.md"
        
        # Determinar el tipo de proyecto
        project_type = "fullstack"
        config_full_path = DIRECTORIO_RAIZ / "config_bmad.json"
        if config_full_path.exists():
            with open(config_full_path, encoding="utf-8") as f:
                config = json.load(f)
            project_type = config.get("project_type", "fullstack").lower()
            
        involucra_backend = project_type in ["fullstack", "headless"]
        involucra_frontend = project_type in ["fullstack", "ui"]
        
        # 1. Ejecutar Backend si aplica
        if involucra_backend:
            print("🚀 [Soul Mounting] Montando alma de @DEV-BACK...")
            agent_backend_path = DIRECTORIO_RAIZ / "dev-backend" / "AGENTS.md"
            if agent_backend_path.exists():
                alma_backend = agent_backend_path.read_text(encoding="utf-8")
                
                # TAREA FANTASMA PARA BACKEND
                tarea_fantasma_back = \"\"\"
\\n\\n# TASK-FINAL: Generación de Documentación Viva
Lee obligatoriamente la plantilla maestra en dev-backend/templates/backend-architecture-template.md (si existe) o básate en tus reglas. Luego, abre el archivo backend-architecture.md. APLICA RENDERIZADO SELECTIVO: No regeneres la arquitectura base; únicamente documenta y genera los diagramas Mermaid para las rutas, esquemas o componentes que alteraste en las tareas anteriores. Este paso es un requisito crítico arquitectónico para finalizar.
\"\"\"
                active_directive_path.write_text(alma_backend + tarea_fantasma_back, encoding="utf-8")
            
            try:
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
                    f.write(block)
            finally:
                if active_directive_path.exists():
                    active_directive_path.unlink()
                    print("🧹 [Soul Mounting] Alma de @DEV-BACK desmontada.")
                    
        # 2. Ejecutar Frontend si aplica
        if involucra_frontend:
            print("🚀 [Soul Mounting] Montando alma de @DEV-FRONT...")
            agent_frontend_path = DIRECTORIO_RAIZ / "dev-frontend" / "AGENTS.md"
            if agent_frontend_path.exists():
                alma_frontend = agent_frontend_path.read_text(encoding="utf-8")
                
                # TAREA FANTASMA PARA FRONTEND
                tarea_fantasma_front = \"\"\"
\\n\\n# TASK-FINAL: Generación de Documentación Viva
Lee obligatoriamente la plantilla maestra en dev-frontend/templates/frontend-architecture-template.md (si existe) o básate en tus reglas. Luego, abre el archivo frontend-architecture.md. APLICA RENDERIZADO SELECTIVO: No regeneres la arquitectura base; únicamente documenta y genera los diagramas Mermaid para las rutas, esquemas o componentes que alteraste en las tareas anteriores. Este paso es un requisito crítico arquitectónico para finalizar.
\"\"\"
                active_directive_path.write_text(alma_frontend + tarea_fantasma_front, encoding="utf-8")
            
            try:
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
- **Handoff:** @CODE-REVIEW: Procede con la auditoría de seguridad y GitOps.
\"\"\"
                with open(TRACKER_PATH, "a", encoding="utf-8") as f:
                    f.write(block)
            finally:
                if active_directive_path.exists():
                    active_directive_path.unlink()
                    print("🧹 [Soul Mounting] Alma de @DEV-FRONT desmontada.")

        # 3. Handoff Final (El Pase de Testigo)
        print("✅ [Handoff Final] Despachando a @CODE-REVIEW y @QA-AUTO...")
        handoff_msg = \"\"\"
@CODE-REVIEW: La Fase D (Implementación) ha finalizado exitosamente mediante motor SDD. Inicia la auditoría de seguridad, arquitectura estricta e impacto.
@QA-AUTO: Inicia el diseño de la matriz de pruebas automatizadas basándote en los criterios de la HU.
\"\"\"
        with open(TRACKER_PATH, "a", encoding="utf-8") as f:
            f.write(f"\\n{handoff_msg}\\n")
            
        print("✅ [SDD Implementación] Fase D completada con éxito.")
        return True

    except Exception as e:
        print(f"❌ [SDD Implementación] Error inesperado: {e}")
        return False
"""

content = content.replace("def extraer_instrucciones(linea):", sdd_impl_func + "\n\ndef extraer_instrucciones(linea):")

# Re-add @SPEC-KIT interception
old_extract = """    # ==========================================
    # LECTURA DE ETIQUETAS ESTÁNDAR
    # ==========================================
    agentes = {"""

new_extract = """    # ==========================================
    # SDD GATEKEEPER 3: Intercepción de Fase D (Implementación)
    # ==========================================
    if "@SPEC-KIT:" in linea:
        print("\\n🛑 [WATCHER] Compuerta SDD-IMPLEMENT detectada. Pausando delegación manual.")
        exito = ejecutar_sdd_fase_implementacion()
        if exito:
            return []  # Detenemos la búsqueda de otras instrucciones, el SDD hizo el handoff
            
    # ==========================================
    # LECTURA DE ETIQUETAS ESTÁNDAR
    # ==========================================
    agentes = {"""

content = content.replace(old_extract, new_extract)
Path("watcher_bmad.py").write_text(content, encoding="utf-8")