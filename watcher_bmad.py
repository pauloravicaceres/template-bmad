import time
import os
import sys
import json
import subprocess
import random
import re
from pathlib import Path

# Configuración de codificación UTF-8 para stdout/stderr en Windows
if sys.platform.startswith('win'):
    try:
        if sys.stdout and hasattr(sys.stdout, 'reconfigure'):
            sys.stdout.reconfigure(encoding='utf-8', errors='replace')
        if sys.stderr and hasattr(sys.stderr, 'reconfigure'):
            sys.stderr.reconfigure(encoding='utf-8', errors='replace')
    except Exception:
        pass


# ==========================================
# RUTAS Y DIRECTORIOS DINÁMICOS
# ==========================================
DIRECTORIO_RAIZ = Path(__file__).resolve().parent
TRACKER_PATH = str(DIRECTORIO_RAIZ / "documents" / "tracker_bmad.md")

def write_watcher_log(mensaje):
    from datetime import datetime
    dt_str = datetime.now().strftime("%d-%m-%Y")
    hr_str = datetime.now().strftime("%H:%M:%S")
    block = f"\n### [{dt_str}] WATCHER\n- **Hora:** {hr_str}\n- **Mensaje:** {mensaje}\n"
    with open(TRACKER_PATH, "a", encoding="utf-8") as f:
        f.write(block)

SKILLS_DIR = DIRECTORIO_RAIZ / "skills"  # NUEVO: Directorio global de habilidades

# ==========================================
# NUEVO: MOTOR DE COMPILACIÓN CON INYECCIÓN DE SKILLS
# ==========================================
def compilar_agentes_modulares():
    print("\n🛠️ [Build] Iniciando ensamblaje de agentes modulares...")
    agentes_modulares = [
        "business-storyteller", "product-analyst", "product-manager",
        "business-analyst", "qa-documental", "designer-ux",
        "solutions-architect", "data-architect", "api-architect", "qa-tech",
        "dev-backend", "dev-frontend", "qa-auto", "code-review", "devops"
    ]
    
    # Aseguramos que la carpeta de skills exista para no generar errores
    SKILLS_DIR.mkdir(parents=True, exist_ok=True)
    
    # Función interna inteligente para Local y Global
    def inyectar_skill(match):
        ruta_relativa = match.group(1).strip() # ej: "skills/hu-validator/SKILL.md"
        
        # 1. Intentar buscar en la carpeta LOCAL del agente (ej. /business-analyst/skills/... o /skill/...)
        skill_local_path = ruta_agente / ruta_relativa
        if not skill_local_path.exists():
            if ruta_relativa.startswith("skills/"):
                alt_rel = "skill/" + ruta_relativa[len("skills/"):]
                if (ruta_agente / alt_rel).exists():
                    skill_local_path = ruta_agente / alt_rel
            elif ruta_relativa.startswith("skill/"):
                alt_rel = "skills/" + ruta_relativa[len("skill/"):]
                if (ruta_agente / alt_rel).exists():
                    skill_local_path = ruta_agente / alt_rel
        
        # 2. Intentar buscar en la carpeta GLOBAL del proyecto (ej. /skills/...)
        skill_global_path = DIRECTORIO_RAIZ / ruta_relativa
        
        if skill_local_path.exists():
            print(f"   🧩 [Skill Local] Inyectando '{ruta_relativa}'...")
            return f"\n\n## 🛠️ SKILL LOCAL: {skill_local_path.parent.name.upper()}\n" + skill_local_path.read_text(encoding='utf-8')
            
        elif skill_global_path.exists():
            print(f"   🌍 [Skill Global] Inyectando '{ruta_relativa}'...")
            return f"\n\n## 🌍 SKILL GLOBAL: {skill_global_path.parent.name.upper()}\n" + skill_global_path.read_text(encoding='utf-8')
            
        else:
            print(f"   ⚠️ [Skill] Error: No se encontró '{ruta_relativa}' ni local ni globalmente.")
            return f"\n\n> ⚠️ **ERROR DE ENSAMBLAJE:** No se encontró la skill `{ruta_relativa}`.\n"
        
    
    for nombre in agentes_modulares:
        ruta_agente = DIRECTORIO_RAIZ / nombre
        if not ruta_agente.exists():
            continue
            
        agent_file = ruta_agente / "agents" / f"{nombre}.agent.md"
        instrucciones_dir = ruta_agente / "instructions"
        target_file = ruta_agente / "AGENTS.md"
        
        if agent_file.exists():
            contenido = agent_file.read_text(encoding='utf-8')
            # Procesar skills si existen en el propio agent.md
            contenido = re.sub(r"\[IMPORT_SKILL:\s*(.+?)\]", inyectar_skill, contenido)
            
            if instrucciones_dir.exists():
                archivos_instrucciones = list(instrucciones_dir.glob("*.instructions.md"))
                if archivos_instrucciones:
                    contenido += "\n\n## ==========================================\n"
                    contenido += "## REGLAS Y ESTÁNDARES ADJUNTOS (AUTO-ENSAMBLADO)\n"
                    contenido += "## ==========================================\n"
                    
                    for inst_file in archivos_instrucciones:
                        titulo = inst_file.stem.upper().replace('-', ' ').replace('.INSTRUCTIONS', '')
                        inst_contenido = inst_file.read_text(encoding='utf-8')
                        inst_contenido = re.sub(r"\[IMPORT_SKILL:\s*(.+?)\]", inyectar_skill, inst_contenido)
                        contenido += f"\n\n## {titulo}\n"
                        contenido += inst_contenido
                
            target_file.write_text(contenido, encoding='utf-8')
            print(f"✅ [Build] AGENTS.md ensamblado exitosamente en la raíz de /{nombre}.")

def guardar_historial(agente_id, instruccion):
    max_reintentos = 5
    for intento in range(max_reintentos):
        try:
            subprocess.run("git add .", shell=True, check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            mensaje_commit = f"BMAD Auto-Save: {agente_id} tarea despachada"
            comando_commit = f'git commit -m "{mensaje_commit}" -m "Instrucción: {instruccion[:50]}..."'
            subprocess.run(comando_commit, shell=True, check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"📦 [Control de Cambios] Commit automático para {agente_id}.")
            break 
        except subprocess.CalledProcessError:
            espera = random.uniform(0.5, 2.0)
            time.sleep(espera)

def obtener_info_agente(nombre_agente):
    try:
        resultado = subprocess.run("herdr agent list", shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace")
        if resultado.returncode != 0:
            return None, None

        datos = json.loads(resultado.stdout)
        agentes = datos.get("result", {}).get("agents", [])

        for agente in agentes:
            if agente.get("name") == nombre_agente:
                return agente.get("pane_id"), agente.get("agent_status")

        return None, None
    except Exception as e:
        print(f"⚠️ [Watcher] Error al consultar agentes: {e}")
        return None, None

def determinar_handoff_fase_a(tracker_path: str, config_path: str = "config_bmad.json") -> str:
    """
    Determina si el proyecto es UI o Headless y retorna el handoff correcto.
    """
    try:
        config_full_path = DIRECTORIO_RAIZ / config_path
        if config_full_path.exists():
            with open(config_full_path, encoding="utf-8") as f:
                config = json.load(f)
            project_type = config.get("project_type", "").lower()
            if project_type == "headless":
                return "@SA:"
            if project_type == "ui":
                return "@UX:"
    except Exception:
        pass

    try:
        if os.path.exists(tracker_path):
            with open(tracker_path, encoding="utf-8") as f:
                ultimas_lineas = f.readlines()[-50:]
            contenido = " ".join(ultimas_lineas).lower()
            if "headless" in contenido:
                return "@SA:"
    except Exception:
        pass

    return "@UX:"

def ejecutar_sdd_fase_negocio(ruta_hu: str):
    """
    Hito 1 del SDD Auto-Runner: Fase de Negocio (Post-QA).
    """
    print(f"\n🚀 [SDD Negocio] Iniciando specify/clarify para: {ruta_hu}")
    try:
        # 1. Specify
        write_watcher_log("⚙️ [SDD Auto-Runner] Ejecutando análisis funcional (/speckit.specify)...")
        subprocess.run(f'agy --dangerously-skip-permissions --print "/speckit.specify {ruta_hu}"', shell=True, check=True, cwd=DIRECTORIO_RAIZ)
        
        # 2. Clarify (HITL por Excepción)
        write_watcher_log("⚙️ [SDD Auto-Runner] Verificando ambigüedades (/speckit.clarify)...")
        res_clarify = subprocess.run('agy --dangerously-skip-permissions --print "/speckit.clarify"', shell=True, capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=DIRECTORIO_RAIZ)
        if "?" in res_clarify.stdout or "ambiguity" in res_clarify.stdout.lower() or res_clarify.returncode != 0:
            print("⚠️ [HITL] Ambigüedad detectada en /speckit.clarify. Pausando para intervención humana.")
            print(res_clarify.stdout)
            
            from datetime import datetime
            dt_str = datetime.now().strftime("%d-%m-%Y")
            hr_str = datetime.now().strftime("%H:%M:%S")
            block = f"""
### [{dt_str}] WATCHER
- **Hora:** {hr_str}
- **Mensaje:** ⚠️ [HITL] Ambigüedad detectada por Spec Kit.
- **Handoff:** @HUMANO: El motor de análisis funcional encontró ambigüedades o vacíos en la Historia de Usuario. Por favor, revisa la matriz y responde la pregunta a continuación para que la IA pueda cerrar el análisis.

{res_clarify.stdout}
"""
            with open(TRACKER_PATH, "a", encoding="utf-8") as f:
                f.write(block)
                
            return False

        # 3. Handoff Dinámico (UX o SA)
        handoff = determinar_handoff_fase_a(TRACKER_PATH)
        msg = f"{handoff} La especificación inicial SDD ha concluido con éxito. Procede con tu diseño."
        
        with open(TRACKER_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n{msg}\n")
        print(f"✅ [SDD Negocio] Handoff despachado: {handoff}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ [SDD Negocio] Error en subproceso: {e}")
        return False
    except Exception as e:
        print(f"❌ [SDD Negocio] Error inesperado: {e}")
        return False

def ejecutar_sdd_fase_arquitectura(ruta_hu: str = ""):
    """
    Hito 2 del SDD Auto-Runner: Fase de Arquitectura (Post-SA).
    """
    print(f"\n🚀 [SDD Arquitectura] Iniciando plan/tasks/analyze...")
    try:
        # 1. Plan & Tasks
        write_watcher_log("⚙️ [SDD Auto-Runner] Estructurando plan de arquitectura técnica (/speckit.plan)...")
        subprocess.run('agy --dangerously-skip-permissions --print "/speckit.plan"', shell=True, check=True, cwd=DIRECTORIO_RAIZ)
        
        write_watcher_log("⚙️ [SDD Auto-Runner] Desglosando tareas de implementación (/speckit.tasks)...")
        subprocess.run('agy --dangerously-skip-permissions --print "/speckit.tasks"', shell=True, check=True, cwd=DIRECTORIO_RAIZ)

        # 2. Analyze (Auditoría Técnica)
        print("🔍 [SDD Arquitectura] Ejecutando auditoría /speckit.analyze...")
        write_watcher_log("⚙️ [SDD Auto-Runner] Ejecutando auditoría técnica (/speckit.analyze)...")
        res_analyze = subprocess.run('agy --dangerously-skip-permissions --print "/speckit.analyze"', shell=True, cwd=DIRECTORIO_RAIZ)
        if res_analyze.returncode != 0:
            print("🛑 [HITL] Auditoría fallida. Violación de constitución técnica. Pausando.")
            return False

        # 3. Spec Freeze Automático
        print("❄️ [Spec Freeze] Congelando especificación (Plan & Tasks)...")
        subprocess.run("git add specs/ .specify/", shell=True, check=True, cwd=DIRECTORIO_RAIZ)
        # Asegurar que el commit no falle si no hay cambios (permitir empty si es necesario, pero agregando specs/ debería haberlos)
        subprocess.run(['git', 'commit', '-m', f"spec: [SPEC-FREEZE] Ciclo SDD Arquitectura completado"], check=False, cwd=DIRECTORIO_RAIZ)
        
        # 4. Handoff a DA
        handoff = "@DA:"
        msg = f"{handoff} El plan técnico y las tareas han sido congeladas. Procede con el diseño de persistencia basándote en los nuevos archivos."
        
        with open(TRACKER_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n{msg}\n")
        print(f"✅ [SDD Arquitectura] Handoff despachado: {handoff}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ [SDD Arquitectura] Error en subproceso: {e}")
        return False
    except Exception as e:
        print(f"❌ [SDD Arquitectura] Error inesperado: {e}")
        return False

def ejecutar_sdd_fase_implementacion():
    """
    Hito 3 del SDD Auto-Runner: Fase D (Implementación) usando SpecKit + Soul Mounting.
    """
    print(f"\n⚙️ [SDD Implementación] Iniciando Fase D (Fuerza Bruta + Alma Agéntica)...")
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
                tarea_fantasma_back = """
\n\n# TASK-FINAL: Generación de Documentación Viva
Lee obligatoriamente la plantilla maestra en dev-backend/templates/backend-architecture-template.md (si existe) o básate en tus reglas. Luego, crea o edita obligatoriamente el archivo 'documents/dev-backend/backend-architecture.md'. APLICA RENDERIZADO SELECTIVO: No regeneres la arquitectura base; únicamente documenta y genera los diagramas Mermaid para las rutas, esquemas o componentes que alteraste en las tareas anteriores. Este paso es un requisito crítico arquitectónico para finalizar.
"""
                active_directive_path.write_text(alma_backend + tarea_fantasma_back, encoding="utf-8")
            
            try:
                print("🏃 [SpecKit] Ejecutando implementación de Backend...")
                write_watcher_log("⚡ [SDD Auto-Runner] Ejecutando implementación Backend (/speckit.implement)...")
                
                subprocess.run('agy --dangerously-skip-permissions "/speckit.implement"', shell=True, check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                from datetime import datetime
                dt_str = datetime.now().strftime("%d-%m-%Y")
                hr_str = datetime.now().strftime("%H:%M:%S")
                handoff_target = "@DEV-FRONT:" if involucra_frontend else "@CODE-REVIEW:"
                handoff_text = "Inicia implementación frontend." if involucra_frontend else "Backend completado sin frontend."
                block = f"""
### [{dt_str}] Senior Backend Developer
- **Hora:** {hr_str}
- **Artefacto generado:** ackend-architecture.md
- **Estado:** Implementación backend finalizada exitosamente mediante SDD SpecKit.
- **Handoff:** {handoff_target} {handoff_text}
"""
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
                tarea_fantasma_front = """
\n\n# TASK-FINAL: Generación de Documentación Viva
Lee obligatoriamente la plantilla maestra en dev-frontend/templates/frontend-architecture-template.md (si existe) o básate en tus reglas. Luego, crea o edita obligatoriamente el archivo 'documents/dev-frontend/frontend-architecture.md'. APLICA RENDERIZADO SELECTIVO: No regeneres la arquitectura base; únicamente documenta y genera los diagramas Mermaid para las rutas, esquemas o componentes que alteraste en las tareas anteriores. Este paso es un requisito crítico arquitectónico para finalizar.
"""
                active_directive_path.write_text(alma_frontend + tarea_fantasma_front, encoding="utf-8")
            
            try:
                print("🏃 [SpecKit] Ejecutando implementación de Frontend...")
                write_watcher_log("⚡ [SDD Auto-Runner] Ejecutando implementación Frontend (/speckit.implement)...")
                
                subprocess.run('agy --dangerously-skip-permissions "/speckit.implement"', shell=True, check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
                
                from datetime import datetime
                dt_str = datetime.now().strftime("%d-%m-%Y")
                hr_str = datetime.now().strftime("%H:%M:%S")
                block = f"""
### [{dt_str}] Senior Frontend Developer
- **Hora:** {hr_str}
- **Artefacto generado:** `documents/dev-frontend/frontend-architecture.md`
- **Estado:** Implementación frontend finalizada exitosamente mediante SDD SpecKit.
- **Handoff:** @CODE-REVIEW: Procede con la auditoría de seguridad y GitOps.
"""
                with open(TRACKER_PATH, "a", encoding="utf-8") as f:
                    f.write(block)
            finally:
                if active_directive_path.exists():
                    active_directive_path.unlink()
                    print("🧹 [Soul Mounting] Alma de @DEV-FRONT desmontada.")

        # 3. Handoff Final (El Pase de Testigo)
        print("✅ [Handoff Final] Despachando a @CODE-REVIEW y @QA-AUTO...")
        handoff_msg = """
@CODE-REVIEW: La Fase D (Implementación) ha finalizado exitosamente mediante motor SDD. Inicia la auditoría de seguridad, arquitectura estricta e impacto.
@QA-AUTO: Inicia el diseño de la matriz de pruebas automatizadas basándote en los criterios de la HU.
"""
        with open(TRACKER_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n{handoff_msg}\n")
            
        print("✅ [SDD Implementación] Fase D completada con éxito.")
        return True

    except Exception as e:
        print(f"❌ [SDD Implementación] Error inesperado: {e}")
        return False

def is_tracker_paused_for_human() -> bool:
    """
    Verifica si el último bloque registrado en tracker_bmad.md está esperando respuesta del @HUMANO:
    """
    if not os.path.exists(TRACKER_PATH):
        return False
    try:
        with open(TRACKER_PATH, "r", encoding="utf-8", errors="replace") as f:
            content = f.read()
        blocks = [b.strip() for b in content.split("### [") if b.strip()]
        if not blocks:
            return False
        last_block = blocks[-1]
        header_line = last_block.split("\n")[0]
        if "HUMANO" not in header_line and "@HUMANO:" in last_block:
            return True
    except Exception:
        pass
    return False

def extraer_instrucciones(linea):
    agentes = {
        "@BS:": "business-storyteller",
        "@PA:": "product-analyst",
        "@PM:": "product-manager",
        "@BA:": "business-analyst",
        "@QA:": "qa-documental",
        "@UX:": "designer-ux",
        "@SA:": "solutions-architect",
        "@DA:": "data-architect",
        "@API:": "api-architect",
        "@QT:": "qa-tech",
        "@QA-AUTO:": "qa-auto",
        "@CODE-REVIEW:": "code-review",
        "@CR:": "code-review",
        "@DEVOPS:": "devops",
    }

    tareas = []
    todas_las_etiquetas = list(agentes.keys())

    # Salvaguarda Global: Si el tracker está en estado pausado esperando al @HUMANO:
    paused = is_tracker_paused_for_human()
    linea_lower = linea.lower()

    # Si la línea contiene @HUMANO:, no despachar agentes
    if "@HUMANO:" in linea:
        pos_humano = linea.find("@HUMANO:")
        pos_agentes = [linea.find(tag) for tag in todas_las_etiquetas if linea.find(tag) != -1]
        if not pos_agentes or pos_humano < min(pos_agentes):
            return []
    # ==========================================
    # SDD GATEKEEPER 0: Respuesta a Clarify desde el Frontend
    # ==========================================
    respuesta_inferida = ""
    if "@watcher: /speckit.clarify" in linea_lower:
        match = re.search(r'/speckit\.clarify\s+(.+)', linea, re.IGNORECASE)
        respuesta_inferida = match.group(1).strip() if match else ""
    elif linea.strip().startswith("- **Handoff:**") or linea.strip().startswith("- **Feedback:**"):
        posible_resp = linea.replace("- **Handoff:**", "").replace("- **Feedback:**", "").strip()
        if posible_resp and len(posible_resp) < 50 and "@" not in posible_resp:
            try:
                with open(TRACKER_PATH, "r", encoding="utf-8", errors="replace") as f:
                    ultimas = f.readlines()[-50:]
                for l in reversed(ultimas):
                    if "Ambigüedad detectada por Spec Kit" in l:
                        respuesta_inferida = posible_resp
                        break
                    if "Artefacto generado" in l:
                        break
            except Exception:
                pass

    if respuesta_inferida:
        print("\n" + "=" * 80)
        print("🚀 [PAUSA SDD INTERCEPTADA] RESPUESTA HUMANA RECIBIDA PARA CLARIFY")
        print("=" * 80)
        write_watcher_log(f"⚙️ [SDD Auto-Runner] Inyectando respuesta humana a Spec Kit: {respuesta_inferida}")
        res = subprocess.run(f'agy --dangerously-skip-permissions -p "/speckit.clarify {respuesta_inferida}"', shell=True, cwd=DIRECTORIO_RAIZ)
        
        # Continuar con el handoff dinámico a UX o SA
        handoff = determinar_handoff_fase_a(TRACKER_PATH)
        
        from datetime import datetime
        dt_str = datetime.now().strftime("%d-%m-%Y")
        hr_str = datetime.now().strftime("%H:%M:%S")
        msg = f"{handoff} La ambigüedad ha sido resuelta por el Humano y la especificación SDD ha concluido con éxito. Procede con tu diseño."
        
        with open(TRACKER_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n### [{dt_str}] WATCHER\n- **Hora:** {hr_str}\n- **Mensaje:** ⚙️ [SDD Auto-Runner] Resolución aplicada exitosamente.\n- **Handoff:** {msg}\n")
        
        print(f"✅ [SDD Negocio] Handoff despachado: {handoff}")
        return []

    # ==========================================
    # SDD GATEKEEPER 1: Intercepción de Aprobación de QA Documental (Negocio)
    # ==========================================
    es_transicion_a_arquitectura = "@UX:" in linea or "@SA:" in linea
    es_aprobacion_qa = (
        "aprobado_qa_" in linea_lower
        or "aprobada por qa" in linea_lower
        or "aprobado por qa" in linea_lower
        or ("@qa:" in linea_lower and "aprobad" in linea_lower)
        or ("aprobad" in linea_lower and es_transicion_a_arquitectura and "ciclo sdd" not in linea_lower)
    )

    if es_transicion_a_arquitectura and es_aprobacion_qa:
        print("\n" + "=" * 80)
        print("🛑 [PAUSA SDD INTERCEPTADA - NEGOCIO] CERTIFICADO QA REGISTRADO")
        print("=" * 80)
        
        # Buscar la ruta de la HU en el mensaje
        match_hu = re.search(r'(?:documents[/\\]business-analyst[/\\])?((?:[0-9]{3}-HU_|hu_)[a-zA-Z0-9_-]+\.md)', linea, re.IGNORECASE)
        if match_hu:
            nombre_hu = match_hu.group(1)
            ruta_hu = f"documents/business-analyst/{nombre_hu}"
            print(f"Iniciando SDD Fase de Negocio para: {ruta_hu}\n")
            
            exito = ejecutar_sdd_fase_negocio(ruta_hu)
            if not exito:
                print("🛑 [HITL] Fallo o ambigüedad en SDD Negocio. Pausando el orquestador.")
                print("Resuelva manualmente y use utils/approve_step.py para reanudar.")
        else:
            print("⚠️ No se pudo extraer la ruta de la HU del mensaje de aprobación.")
            print("Ejecute Spec Kit manualmente y use utils/approve_step.py para reanudar.")
            
        print("=" * 80 + "\n")
        return []

    # ==========================================
    # SDD GATEKEEPER 2: Intercepción de SA (Arquitectura)
    # ==========================================
    if "@watcher: sdd-freeze" in linea_lower:
        print("\n" + "=" * 80)
        print("🛑 [PAUSA SDD INTERCEPTADA - ARQUITECTURA] GUIDELINES SA REGISTRADOS")
        print("=" * 80)
        
        match_hu = re.search(r'((?:[0-9]{3}-HU_|hu_)[a-zA-Z0-9_-]+\.md)', linea, re.IGNORECASE)
        ruta_hu = match_hu.group(1) if match_hu else ""
        
        print(f"Iniciando SDD Fase de Arquitectura...\n")
        exito = ejecutar_sdd_fase_arquitectura(ruta_hu)
        if not exito:
            print("🛑 [HITL] Fallo en SDD Arquitectura. Pausando el orquestador.")
            print("Resuelva manualmente y envíe un handoff a @DA: para reanudar.")
        print("=" * 80 + "\n")
        return []

    # ==========================================
    # SDD GATEKEEPER 3: Intercepción de QT (Implementación Automática)
    # ==========================================
    if ("@dev-back:" in linea_lower or "@dev-front:" in linea_lower) and "arquitectura" in linea_lower:
        print("\n" + "=" * 80)
        print("💡 [GATILLO SDD DETECTADO] INICIANDO FASE D AUTOMÁTICA")
        print("=" * 80)
        print(f"Iniciando SDD Fase de Implementación...\n")
        exito = ejecutar_sdd_fase_implementacion()
        if not exito:
            print("❌ [HITL] Fallo en SDD Implementación. Pausando el orquestador.")
        print("=" * 80 + "\n")
        return []

    
    if paused:
        return []

    for etiqueta, agente_nombre in agentes.items():
        if etiqueta in linea:
            inicio = linea.find(etiqueta)
            fin = len(linea)
            
            for otra_etiqueta in todas_las_etiquetas:
                if otra_etiqueta != etiqueta:
                    pos_otra = linea.find(otra_etiqueta, inicio + len(etiqueta))
                    if pos_otra != -1 and pos_otra < fin:
                        fin = pos_otra
                        
            mensaje = linea[inicio:fin].strip()
            tareas.append({'agente': agente_nombre, 'mensaje': mensaje})
            
    return tareas

# ==========================================
# GITOPS EVENT SOURCING CONTROLLER
# ==========================================
def get_current_branch():
    try:
        result = subprocess.run(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True, cwd=DIRECTORIO_RAIZ)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_all_branches():
    try:
        result = subprocess.run(["git", "branch", "--format=%(refname:short)"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True, cwd=DIRECTORIO_RAIZ)
        return [b for b in result.stdout.split('\n') if b.strip()]
    except subprocess.CalledProcessError:
        return []

def get_base_branch():
    branches = get_all_branches()
    if "dev" in branches:
        return "dev"
    elif "main" in branches:
        return "main"
    elif "master" in branches:
        return "master"
    return "main"

def check_working_directory_clean():
    res = subprocess.run(["git", "status", "--porcelain"], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=DIRECTORIO_RAIZ)
    return len(res.stdout.strip()) == 0

def auto_commit_security():
    if not check_working_directory_clean():
        print("🔒 [GITOPS] Cambios sin guardar detectados. Realizando auto-commit de seguridad...")
        subprocess.run(["git", "add", "."], check=True, cwd=DIRECTORIO_RAIZ)
        subprocess.run(["git", "commit", "-m", "chore: auto-commit pre-branch switch"], check=True, cwd=DIRECTORIO_RAIZ)

def gitops_branch_create(branch_name):
    print(f"\n🌿 [GITOPS] Interceptada macro de creación de rama: {branch_name}")
    auto_commit_security()
    
    base_branch = get_base_branch()
    current = get_current_branch()
    if current != base_branch:
        subprocess.run(["git", "checkout", base_branch], check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    try:
        existing = subprocess.run(["git", "branch", "--list", branch_name], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=DIRECTORIO_RAIZ)
        if existing.stdout.strip() and branch_name in existing.stdout:
            subprocess.run(["git", "checkout", branch_name], check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ [GITOPS] Rama {branch_name} existente reactivada.")
        else:
            subprocess.run(["git", "checkout", "-b", branch_name], check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ [GITOPS] Rama {branch_name} creada y activa.")
    except Exception as e:
        print(f"⚠️ [WATCHER-GIT] Error al crear la rama: {e}")

def gitops_merge_close(branch_name):
    print(f"\n🚀 [GITOPS] Interceptada macro de fusión (merge-close): {branch_name}")
    auto_commit_security()
    
    base_branch = get_base_branch()
    subprocess.run(["git", "checkout", "-f", base_branch], check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        subprocess.run(["git", "merge", "--no-ff", "--no-edit", branch_name], check=True, cwd=DIRECTORIO_RAIZ)
        subprocess.run(["git", "branch", "-d", branch_name], check=True, cwd=DIRECTORIO_RAIZ)
        print(f"✅ [GITOPS] Fusión exitosa. Rama {branch_name} eliminada.")
    except subprocess.CalledProcessError:
        print("🛑 [GITOPS] Conflicto de fusión detectado. Abortando merge...")
        subprocess.run(["git", "merge", "--abort"], cwd=DIRECTORIO_RAIZ, stderr=subprocess.DEVNULL)
        subprocess.run(["git", "checkout", "-f", branch_name], cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        with open(TRACKER_PATH, "a", encoding="utf-8") as f:
            f.write(f"\n@HUMANO: ⚠️ ALERTA GITOPS: Conflicto de fusión detectado al intentar cerrar la rama {branch_name}.\nEl Watcher ha abortado el merge por seguridad y se ha detenido.\nPASOS DE RECUPERACIÓN PARA EL HUMANO:\n1. Abre tu terminal y ejecuta manualmente el merge o rebase hacia dev o main.\n2. Resuelve los conflictos en tu editor y haz el commit final.\n3. Vuelve a encender el Watcher (python watcher_bmad.py).\nNota: NO necesitas borrar ni agregar ninguna línea en este tracker. El sistema asumirá el cierre exitoso y continuará su operación normal.\n")
        print(f"⏸️ [HITL] Se requiere intervención humana. Pausando el orquestador.")
        sys.exit(1)

def hydration_gitops():
    if not os.path.exists(TRACKER_PATH):
        return None
    with open(TRACKER_PATH, "r", encoding="utf-8", errors="replace") as f:
        lineas = f.readlines()
    
    orphaned_branch = None
    for linea in lineas:
        if "@WATCHER: GITOPS-BRANCH-CREATE" in linea:
            match = re.search(r"@WATCHER:\s*GITOPS-BRANCH-CREATE\s+([^\s]+)", linea)
            if match:
                orphaned_branch = match.group(1)
        elif "@WATCHER: GITOPS-MERGE-CLOSE" in linea:
            match = re.search(r"@WATCHER:\s*GITOPS-MERGE-CLOSE\s+([^\s]+)", linea)
            if match and match.group(1) == orphaned_branch:
                orphaned_branch = None
    return orphaned_branch

def validar_constitucion_gitops():
    const_dir = DIRECTORIO_RAIZ / ".specify" / "memory"
    const_dir.mkdir(parents=True, exist_ok=True)
    const_path = const_dir / "constitution.md"
    
    template_path = DIRECTORIO_RAIZ / "utils" / "gitops-constitution.template.md"
    if not template_path.exists():
        return
        
    plantilla_gitops = template_path.read_text(encoding='utf-8')
    if const_path.exists():
        contenido = const_path.read_text(encoding='utf-8')
        if "ESTÁNDAR GITOPS" not in contenido:
            print("🛡️ [GITOPS] Restaurando cláusula constitucional de Feature Branching...")
            with open(const_path, "a", encoding="utf-8") as f:
                f.write("\n" + plantilla_gitops)
    else:
        print("🛡️ [GITOPS] Creando constitución técnica inicial...")
        with open(const_path, "w", encoding="utf-8") as f:
            f.write("# 📜 Constitución Técnica Global de BMAD\n" + plantilla_gitops)

def iniciar_watcher():
    compilar_agentes_modulares()
    validar_constitucion_gitops()
    print("-" * 50)
    
    print(f"👁️ Watcher BMAD (Sequential Token-Passing) iniciado.")
    print(f"📂 Escuchando cambios en: {TRACKER_PATH}")
    
    # State Hydration
    orphaned = hydration_gitops()
    if orphaned:
        current = get_current_branch()
        if current != orphaned:
            print(f"🔄 [GITOPS] Retomando estado no finalizado. Cambiando a rama {orphaned}")
            auto_commit_security()
            try:
                subprocess.run(["git", "checkout", orphaned], check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception:
                pass
        else:
            print(f"✅ [GITOPS] Estado sincronizado. Continuando en la rama {orphaned}")

    num_lineas_leidas = 0
    cola_tareas = []
    hash_tareas_historicas = set()
    
    if os.path.exists(TRACKER_PATH):
        with open(TRACKER_PATH, 'r', encoding='utf-8', errors='replace') as f:
            lineas = [l for l in f.readlines() if l.strip()]
            
        if lineas:
            ultima_linea = lineas[-1]
            print(f"\n📂 Tracker detectado con {len(lineas)} eventos históricos.")
            print(f"Última instrucción registrada:\n>> {ultima_linea}\n")
            
            # Preguntar siempre al usuario si desea reanudar la ejecución (incluso si está en GitOps)
            respuesta = input("🔄 ¿Deseas reanudar la ejecución desde esta última instrucción? (s/n): ")
            
            if respuesta.lower() == 's':
                num_lineas_leidas = len(lineas) - 1
                print("🔓 Modo Recuperación: Re-encolando la última tarea...\n")
            else:
                num_lineas_leidas = len(lineas)
                print("🔒 Candado activado: Histórico ignorado. Esperando nuevas instrucciones...\n")
        else:
            num_lineas_leidas = 0
            
    while True:
        try:
            if os.path.exists(TRACKER_PATH):
                with open(TRACKER_PATH, 'r', encoding='utf-8', errors='replace') as f:
                    lineas = [l for l in f.readlines() if l.strip()]
                    
                    if len(lineas) > num_lineas_leidas:
                        nuevas_lineas = lineas[num_lineas_leidas:]
                        for idx, linea in enumerate(nuevas_lineas):
                            
                            # GITOPS Live Interception
                            if "@WATCHER: GITOPS-BRANCH-CREATE" in linea:
                                match = re.search(r"@WATCHER:\s*GITOPS-BRANCH-CREATE\s+([^\s]+)", linea)
                                if match:
                                    gitops_branch_create(match.group(1))
                            elif "@WATCHER: GITOPS-MERGE-CLOSE" in linea:
                                match = re.search(r"@WATCHER:\s*GITOPS-MERGE-CLOSE\s+([^\s]+)", linea)
                                if match:
                                    gitops_merge_close(match.group(1))

                            nuevas_tareas = extraer_instrucciones(linea)
                            numero_linea_absoluta = num_lineas_leidas + idx
                            
                            for tarea in nuevas_tareas:
                                id_tarea = hash(f"{numero_linea_absoluta}_{tarea['agente']}_{tarea['mensaje']}")
                                if id_tarea not in hash_tareas_historicas:
                                    cola_tareas.append(tarea)
                                    hash_tareas_historicas.add(id_tarea)
                                    print(f"📥 [Cola] Tarea encolada para '{tarea['agente']}'.")
                                    
                        num_lineas_leidas = len(lineas)
                    elif len(lineas) < num_lineas_leidas:
                        num_lineas_leidas = len(lineas)
                        
            tareas_no_procesadas = []
            candado_disparo = False
            
            for tarea in cola_tareas:
                if candado_disparo:
                    tareas_no_procesadas.append(tarea)
                    continue

                agente = tarea['agente']
                mensaje = tarea['mensaje']
                
                pane_id, estado = obtener_info_agente(agente)
                
                if not pane_id:
                    print(f"❌ [Watcher] Agente '{agente}' no encontrado.")
                    tareas_no_procesadas.append(tarea)
                    continue
                    
                if estado not in ["idle", "done"]:
                    print(f"⏳ [Watcher] '{agente}' está {estado}. Esperando turno...")
                    tareas_no_procesadas.append(tarea)
                    continue 

                print(f"\n🚀 [Watcher] Inyectando tarea a '{agente}'...")
                linea_escapada = mensaje.replace('"', '\\"')
                comando = f'herdr pane run {pane_id} "{linea_escapada}"'

                try:
                    subprocess.run(comando, shell=True, check=True)
                    print(f"✅ [Watcher] Éxito. Tarea despachada a {agente}.")
                    
                    candado_disparo = True
                except subprocess.CalledProcessError as e:
                    print(f"❌ [Watcher] Error de inyección. Código: {e.returncode}")
                    tareas_no_procesadas.append(tarea)

            cola_tareas = tareas_no_procesadas
                                
        except KeyboardInterrupt:
            print("\n🛑 Watcher detenido por el usuario.")
            break
        except Exception as e:
            print(f"⚠️ [Watcher] Error general: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    iniciar_watcher()


