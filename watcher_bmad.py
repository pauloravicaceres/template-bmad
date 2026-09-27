import time
import os
import sys
import json
import subprocess
import random
import re  # NUEVO: Necesario para procesar las etiquetas de inyección de Skills
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
TRACKER_PATH = str(DIRECTORIO_RAIZ / "files" / "tracker_bmad.md")
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
        resultado = subprocess.run("herdr agent list", shell=True, capture_output=True, text=True)
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
        "@DEV-BACK:": "dev-backend",
        "@DEV-BACKEND:": "dev-backend",
        "@DEV-FRONT:": "dev-frontend",
        "@DEV-FRONTEND:": "dev-frontend",
        "@QA-AUTO:": "qa-auto",
        "@CODE-REVIEW:": "code-review",
        "@CR:": "code-review",
        "@DEVOPS:": "devops",
        "@DEV:": "dev-backend"
    }

    tareas = []
    todas_las_etiquetas = list(agentes.keys())

    # Salvaguarda: Si el Handoff está dirigido al @HUMANO:, no despachar ningún agente
    if "@HUMANO:" in linea:
        pos_humano = linea.find("@HUMANO:")
        pos_agentes = [linea.find(tag) for tag in todas_las_etiquetas if linea.find(tag) != -1]
        if not pos_agentes or pos_humano < min(pos_agentes):
            return []

    # ==========================================
    # SDD GATEKEEPER: Intercepción de Aprobación de QA Documental
    # ==========================================
    linea_lower = linea.lower()
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
        print("🛑 [PAUSA SDD INTERCEPTADA] CERTIFICADO QA DOCUMENTAL REGISTRADO")
        print("=" * 80)
        print("El agente 'qa-documental' ha emitido la aprobación de la Historia de Usuario.")
        print("El avance automático hacia UX / Arquitectura ha sido DETENIDO para el ciclo SDD.\n")
        print("📋 SECUENCIA REQUERIDA EN GITHUB SPEC KIT (CLI / HERDR):")
        print("   1. /speckit.specify files/business-analyst/hu_[ID]_[nombre].md")
        print("   2. /speckit.clarify")
        print("   3. /speckit.plan")
        print("   4. /speckit.tasks")
        print("   5. /speckit.analyze (Auditoría automática contra constitution.md)\n")
        print("🔓 PARA LIBERAR LA TRANSICIÓN HACIA FASE A (UX / ARQUITECTURA):")
        print("   Una vez concluido /speckit.analyze, ejecute en otra terminal:")
        print("   python utils/approve_step.py")
        print("   y seleccione la opción: [5] Spec Kit (SDD Bridge) -> UX  (o [6] para Headless)")
        print("=" * 80 + "\n")
        return []

    # Notificación informativa para gatillo de implementacion Spec Kit
    if "@SPEC-KIT:" in linea:
        print("\n" + "=" * 80)
        print("⚡ [GATILLO SDD DETECTADO] ARQUITECTURA TÉCNICA LISTA PARA IMPLEMENTACIÓN")
        print("=" * 80)
        print("El QA Técnico ha certificado y compilado el Tech Design maestro.")
        print("Ejecute en la terminal / CLI de Spec Kit:")
        print("   /speckit.implement")
        print("para iniciar el despacho coordinado de tareas a la Fase D (@DEV-BACK, @DEV-FRONT, @DEVOPS).")
        print("=" * 80 + "\n")

    
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

def iniciar_watcher():
    compilar_agentes_modulares()
    print("-" * 50)
    
    print(f"👁️ Watcher BMAD (Sequential Token-Passing) iniciado.")
    print(f"📂 Escuchando cambios en: {TRACKER_PATH}")
    
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