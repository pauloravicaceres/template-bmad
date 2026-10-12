import time
import os
import sys
import json
import subprocess
import random
import re
import shutil
from pathlib import Path

import ux_routing
from bmad_runtime import outbox, policy_audit
from bmad_runtime.pane_state import PaneNotReady
from bmad_runtime.config import TRACKER_AUTHORS
from bmad_runtime.runtime import Runtime
from bmad_runtime.errors import AgentBlocked, BMADRuntimeError, ReconciliationRequired
from bmad_runtime.gitops import GitService
from bmad_runtime.hu_lifecycle import GATE as HU_GATE, gitops_macro
from bmad_runtime.hu_naming import find_hu_file, hu_name_error, invalid_hu_reference, is_feature_branch, is_hu_filename
from bmad_runtime.guard import describe as describir_alerta, describe_recommendation as describir_recomendacion
from bmad_runtime.services import block_fields
from bmad_runtime.watcher_service import (HOLD_STATES, SESSION_LOCK, WatcherService, audit_blocks, maintenance_blocks,
                                          mark_handoff, paused_for_human, protocol_violations, watcher_heartbeat)
from bmad_runtime.state import ProjectLock, StateStore, project_lock
from bmad_runtime.context import ProjectContext, add_project_arguments, read_json, resolve_context

_runtime = None

def runtime():
    global _runtime
    if _runtime is None:
        _runtime = Runtime(DIRECTORIO_RAIZ)
    return _runtime

def run_git(argv, **kwargs):
    return GitService(runtime()).run(argv, **kwargs)

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
ENGINE_ROOT = Path(__file__).resolve().parent.parent
DIRECTORIO_RAIZ = ENGINE_ROOT
TRACKER_PATH = str(DIRECTORIO_RAIZ / "docs" / "tracker_bmad.md")

last_implement_trigger = 0

def escritor_tracker():
    """TrackerWriter del tracker de este proceso (TRACKER_PATH puede estar parcheado en pruebas)."""
    from bmad_runtime.tracker_io import TrackerWriter
    if _runtime is not None and Path(TRACKER_PATH) == _runtime.context.tracker_path:
        return TrackerWriter.for_runtime(_runtime)
    return TrackerWriter(TRACKER_PATH)

def anexar_tracker(texto, op_id=None):
    """Única vía de escritura del watcher en el tracker: texto completo, con lock de proyecto y journal."""
    return escritor_tracker().append(texto, op_id=op_id, source='watcher')

def write_watcher_log(mensaje):
    from datetime import datetime
    dt_str = datetime.now().strftime("%d-%m-%Y")
    hr_str = datetime.now().strftime("%H:%M:%S")
    block = f"\n### [{dt_str}] WATCHER\n- **Hora:** {hr_str}\n- **Mensaje:** {mensaje}\n"
    anexar_tracker(block)

SKILLS_DIR = ENGINE_ROOT / "skills"


def configure_project(rt):
    """Bind this watcher process once; A/B run in separate processes."""
    global _runtime, ENGINE_ROOT, SKILLS_DIR, DIRECTORIO_RAIZ, TRACKER_PATH, RETRABAJO_STATE_PATH, RETRABAJO_CLASIFICACION_PATH
    _runtime = rt
    ENGINE_ROOT = rt.context.engine_root
    SKILLS_DIR = ENGINE_ROOT / 'skills'
    DIRECTORIO_RAIZ = rt.context.workspace_root
    TRACKER_PATH = str(rt.context.tracker_path)
    RETRABAJO_STATE_PATH = rt.context.output('.specify/memory/rework_state.json')
    RETRABAJO_CLASIFICACION_PATH = rt.context.output('.specify/memory/rework_last_classification.md')


def project_settings():
    if _runtime is not None:
        return _runtime.config.raw
    try:
        return read_json(DIRECTORIO_RAIZ / 'config_bmad.json')
    except BMADRuntimeError:
        return {}


def project_output(relative):
    if _runtime is not None:
        return _runtime.context.output(relative)
    return ProjectContext(ENGINE_ROOT, DIRECTORIO_RAIZ.resolve(), 'legacy', True).output(relative)

# ==========================================
# SPEC KIT: proveedor y skills resueltos por operación en SpecKitExecutor.
# ==========================================
def ejecutar_speckit(skill, argumentos="", directiva=None, entorno=None):
    from bmad_runtime.commands import Result
    try:
        result = runtime().spec.execute(skill, argumentos, directiva, entorno)
    except BMADRuntimeError as exc:
        write_watcher_log(f"ERROR Spec Kit {skill}: {exc}")
        return Result(1, error=type(exc).__name__)
    if result.returncode:
        write_watcher_log(f"ERROR Spec Kit {skill}: {result.error or 'cli_error'} (código {result.returncode}). Revisar estado parcial; sin reintento automático.")
    return result

ALCANCES_IMPLEMENTACION = {
    "backend": (
        "ALCANCE: SOLO BACKEND (API, dominio, datos, pruebas del servidor, con el stack del workspace). "
        "Ignora y NO ejecutes tareas de frontend/UI (componentes, vistas)."
    ),
    "frontend": (
        "ALCANCE: SOLO FRONTEND (UI: componentes, vistas, servicios y pruebas del cliente). "
        "Ignora y NO ejecutes tareas de backend; no repitas tareas ya marcadas [X] en tasks.md."
    ),
}

def sin_tokens(texto):
    """Quita las '@' de las menciones a agentes. Un Handoff del Watcher debe llevar un único token de despacho
    (el del siguiente agente); cualquier otra referencia va como texto plano para que nada la despache."""
    return re.sub(r"@(?=[A-Za-z])", "", texto or "").replace("  ", " ").strip()

NO_TOCAR_TRACKER = (
    "NO escribas en docs/tracker_bmad.md ni emitas handoffs (@AGENTE:): el Watcher registra tu bloque y "
    "decide el siguiente agente. Un bloque propio despacharía a QA antes de tiempo."
)

CODE_DIRS_POR_DEFECTO = {"backend": "app/backend", "frontend": "app/frontend"}

def ruta_readme_codigo(capa):
    """
    Ruta (relativa a la raíz) del README del código de una capa. La carpeta puede sobrescribirse en
    config_bmad.json con {"code_dirs": {"backend": "...", "frontend": "..."}}; por defecto app/<capa>.
    """
    carpeta = CODE_DIRS_POR_DEFECTO[capa]
    try:
        cfg = project_settings()
        carpeta = cfg.get("code_dirs", {}).get(capa, carpeta)
        if _runtime is not None and not _runtime.context.legacy and capa not in cfg.get('code_dirs', {}):
            from bmad_runtime.technical_context import source_directory
            carpeta = source_directory(_runtime.context, capa)
    except (OSError, ValueError):
        pass
    project_output(carpeta)
    return carpeta.replace("\\", "/").strip("/") + "/README.md"

def instruccion_readme(ruta_readme):
    """Mandato de documentar el código de la capa: crear el README si falta, actualizarlo si ya existe."""
    return (
        f"README DEL CÓDIGO: además del documento de arquitectura, crea o actualiza '{ruta_readme}' (créalo con su "
        "carpeta si no existe). Debe cubrir: propósito de la capa, requisitos previos, configuración (variables de "
        "entorno / appsettings), cómo arrancar, cómo ejecutar las pruebas, estructura de carpetas y, si aplica, "
        "endpoints o rutas principales con un enlace al documento de arquitectura. Si el README ya existe, "
        "actualiza SOLO las secciones que tus cambios alteraron y conserva el resto: no lo reescribas ni borres "
        "contenido vigente. NO inventes comandos: verifica cada uno en los archivos del proyecto "
        "(package.json, .csproj, scripts) antes de escribirlo."
    )

def instruccion_doc_viva(ruta_doc, alcance=None, ruta_readme=None):
    """Argumento de /speckit-implement: delimita el alcance y obliga a generar la documentación viva."""
    prefijo = (ALCANCES_IMPLEMENTACION.get(alcance, "") + " ") if alcance else ""
    texto = prefijo + (NO_TOCAR_TRACKER if _runtime is None or _runtime.context.legacy else NO_TOCAR_TRACKER.replace("docs/tracker_bmad.md", str(_runtime.context.tracker_path))) + " " + (
        f"OBLIGATORIO al finalizar todas las tareas: crea o edita el archivo '{ruta_doc}' "
        "(créalo si no existe, incluida su carpeta) documentando con diagramas Mermaid solo lo que "
        "alteraste. Aunque no hayas cambiado código, debes crear o tocar ese archivo indicando que la "
        "arquitectura actual está vigente. Sin este archivo la ejecución se considera fallida."
    )
    if ruta_readme:
        texto += " " + instruccion_readme(ruta_readme)
    return texto

# ==========================================
# RETRABAJO SDD (RECHAZOS DE CODE-REVIEW / QA-AUTO)
# Un rechazo no se parchea: se clasifica por capa de origen (SPEC/PLAN/TASKS/CODE),
# se reconcilia con /speckit-converge y recién entonces se re-implementa con /speckit-implement.
# ==========================================
AUTORES_REVISORES = ("Code Review", "QA Automation")
MAX_ITERACIONES_RETRABAJO = 2
RETRABAJO_STATE_PATH = DIRECTORIO_RAIZ / ".specify" / "memory" / "rework_state.json"
RETRABAJO_CLASIFICACION_PATH = DIRECTORIO_RAIZ / ".specify" / "memory" / "rework_last_classification.md"
retrabajos_procesados = set()
contexto_bloque = {"autor": None, "hora": None}

def actualizar_contexto_bloque(linea):
    """Recuerda a qué bloque del tracker pertenece la línea que se está procesando."""
    m = re.match(r"###\s+\[[^\]]+\]\s+(.+)", linea.strip())
    if m:
        contexto_bloque.update(autor=m.group(1).strip(), hora=None)
        return
    h = re.search(r"\*\*Hora:\*\*\s+([\d:]+)", linea)
    if h:
        contexto_bloque["hora"] = h.group(1)

def buscar_bloque_tracker(autor=None, hora=None):
    """Devuelve (autor, hora, texto) del bloque indicado, o del último bloque si autor es None."""
    try:
        contenido = Path(TRACKER_PATH).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return None, None, ""
    bloques = [b for b in re.split(r"(?=^### \[)", contenido, flags=re.MULTILINE) if b.startswith("### [")]
    for b in reversed(bloques):
        m = re.match(r"### \[[^\]]+\]\s+([^\n]+)", b)
        h = re.search(r"\*\*Hora:\*\*\s+([\d:]+)", b)
        if not m:
            continue
        if autor is None or (m.group(1).strip() == autor and (hora is None or (h and h.group(1) == hora))):
            return m.group(1).strip(), (h.group(1) if h else None), b
    return None, None, ""

def extraer_segmentos_handoff(bloque):
    """Separa el handoff de un revisor en lo que corresponde a backend, frontend y QA."""
    idx = bloque.find("**Handoff:**")
    seccion = bloque[idx:] if idx != -1 else bloque
    marcas = list(re.finditer(r"@(DEV-BACK|DEV-FRONT|QA-AUTO|CODE-REVIEW|CR|HUMANO):", seccion))
    claves = {"DEV-BACK": "backend", "DEV-FRONT": "frontend", "QA-AUTO": "qa"}
    segmentos = {}
    for i, m in enumerate(marcas):
        fin = marcas[i + 1].start() if i + 1 < len(marcas) else len(seccion)
        clave = claves.get(m.group(1))
        if clave:
            segmentos[clave] = seccion[m.end():fin].strip()
    return segmentos

def _leer_estado_retrabajo():
    try:
        return json.loads(RETRABAJO_STATE_PATH.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return {}

def _guardar_estado_retrabajo(estado):
    RETRABAJO_STATE_PATH.parent.mkdir(parents=True, exist_ok=True)
    temporary = RETRABAJO_STATE_PATH.with_suffix('.json.tmp')
    temporary.write_text(json.dumps(estado, indent=2), encoding="utf-8")
    temporary.replace(RETRABAJO_STATE_PATH)

def resetear_retrabajo(clave):
    estado = _leer_estado_retrabajo()
    if estado.pop(clave, None) is not None:
        _guardar_estado_retrabajo(estado)

def ejecutar_sdd_retrabajo(autor, bloque):
    """
    Ciclo de convergencia ante un rechazo:
      analyze -> converge (clasifica por capa, corrige spec/plan, reabre tasks) -> implement -> QA-AUTO.
    Tras MAX_ITERACIONES_RETRABAJO ciclos escala al humano: la causa suele estar en la spec o el plan.
    """
    segmentos = extraer_segmentos_handoff(bloque)
    if not segmentos.get("backend") and not segmentos.get("frontend"):
        return True

    clave = get_current_branch() or "sin-rama"
    estado = _leer_estado_retrabajo()
    n = estado.get(clave, 0) + 1
    m_art = re.search(r"\*\*Artefacto generado:\*\*\s+`?([^`\n]+)`?", bloque)
    artefacto = m_art.group(1).strip() if m_art else "(sin artefacto)"
    m_est = re.search(r"\*\*Estado:\*\*\s+([^\n]+)", bloque)
    hallazgos = m_est.group(1).strip() if m_est else ""

    if n > MAX_ITERACIONES_RETRABAJO:
        from datetime import datetime
        ahora = datetime.now()
        anexar_tracker(
            f"\n### [{ahora.strftime('%d-%m-%Y')}] WATCHER\n- **Hora:** {ahora.strftime('%H:%M:%S')}\n"
            f"- **Mensaje:** 🛑 [SDD Retrabajo] Límite de {MAX_ITERACIONES_RETRABAJO} iteraciones alcanzado sin aprobación de {autor}.\n"
            f"- **Handoff:** @HUMANO: El retrabajo automático no converge; la causa suele estar en la spec o el plan, no en el código. "
            f"Revisa {artefacto}, corrige spec.md/plan.md si corresponde y define cómo continuar.\n"
        )
        print("🛑 [SDD Retrabajo] Límite de iteraciones alcanzado. Escalando a @HUMANO.")
        return False

    estado[clave] = n
    _guardar_estado_retrabajo(estado)
    write_watcher_log(
        f"🔁 [SDD Retrabajo] Iteración {n}/{MAX_ITERACIONES_RETRABAJO} (origen: {autor}). "
        "Reconciliando spec, plan y tasks (/speckit-converge)..."
    )

    # 1. Analyze: auditoría de consistencia entre artefactos (solo lectura)
    res_analyze = ejecutar_speckit("analyze")
    if res_analyze.returncode:
        return False
    informe = (res_analyze.stdout or "").strip()[-2500:]

    # 2. Converge: clasificar por capa, corregir spec/plan y reconciliar tasks.md
    capas = set(re.findall(r"\[CAPA:(SPEC|PLAN|TASKS|CODE)\]", bloque))
    if capas and capas <= {"CODE", "TASKS"}:
        guia_capas = (
            "Todos los hallazgos vienen etiquetados CODE/TASKS: spec.md y plan.md son correctos, NO los modifiques. "
        )
    elif capas:
        guia_capas = (
            f"El revisor etiquetó capas {sorted(capas)}: respétalas y corrige primero, en spec.md/plan.md, "
            "los hallazgos [CAPA:SPEC] y [CAPA:PLAN] antes de tocar tasks.md. "
        )
    else:
        guia_capas = "El revisor no etiquetó capas: clasifícalas tú con criterio conservador (ante la duda, la capa superior). "
    prompt = (
        guia_capas +
        "La constitución (.specify/memory/constitution.md) es el árbitro: si un hallazgo la viola, se corrige el código; "
        "si la constitución es ambigua, NO la reinterpretes, señálalo para enmendarla con /speckit-constitution. "
        f"MODO RETRABAJO (iteración {n}/{MAX_ITERACIONES_RETRABAJO}). El revisor '{autor}' RECHAZÓ la implementación. "
        f"Informe del revisor: {artefacto}. Hallazgos: {hallazgos[:3000]} "
        f"Asignación: {json.dumps(segmentos, ensure_ascii=False)[:1500]} "
        f"Informe previo de consistencia (/speckit-analyze): {informe} "
        "INSTRUCCIONES: (1) Clasifica cada hallazgo por capa de origen: SPEC (contrato o requisito erróneo/ambiguo), "
        "PLAN (diseño técnico incompleto), TASKS (tarea marcada [X] sin cumplirse o ausente) o CODE (defecto de implementación). "
        "(2) Si hay hallazgos SPEC o PLAN, corrige primero spec.md y plan.md con el cambio mínimo, respetando la constitución. "
        "(3) Desmarca las tareas falsamente cerradas y agrega al final de tasks.md una tarea nueva por hallazgo, con ID consecutivo, "
        "etiqueta [fix:<CAPA>:<n° de hallazgo>] e indicando si es de servidor o de interfaz. "
        "(4) NO implementes código en este paso. (5) Termina con una tabla: hallazgo | capa | tarea. "
        + NO_TOCAR_TRACKER
    )
    res_conv = ejecutar_speckit("converge", prompt)
    if res_conv.returncode != 0:
        return False
    try:
        RETRABAJO_CLASIFICACION_PATH.parent.mkdir(parents=True, exist_ok=True)
        RETRABAJO_CLASIFICACION_PATH.write_text(
            f"# Clasificación de retrabajo (iteración {n}, origen: {autor})\n\n{(res_conv.stdout or '').strip()}\n",
            encoding="utf-8",
        )
    except OSError:
        pass

    if capas & {"SPEC", "PLAN"}:
        # Trazabilidad: la spec/plan cambiaron, los artefactos de diseño derivados deben sincronizarse.
        # Mensaje informativo (sin tokens @TAG:) para que no despache agentes ni reabra la cadena de diseño.
        write_watcher_log(
            "📌 [SDD Retrabajo] spec.md/plan.md actualizados por converge "
            f"(capas: {', '.join(sorted(capas & {'SPEC', 'PLAN'}))}). "
            "Los artefactos de diseño de BA, API y DA deben sincronizarse con el cambio."
        )

    # 3. Implement acotado a las tareas [fix:*]; el último bloque DEV deriva a @QA-AUTO
    return ejecutar_sdd_fase_implementacion(retrabajo={
        "autor": autor, "iteracion": n, "max": MAX_ITERACIONES_RETRABAJO, "segmentos": segmentos,
    })

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
        skill_global_path = ENGINE_ROOT / ruta_relativa
        
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
        ruta_agente = ENGINE_ROOT / nombre
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
    """Legacy API. Autosave is opt-in and never records the prompt in Git."""
    if not runtime().config.data['git']['auto_commit']:
        return
    run_git(['git', 'add', '.'], check=True)
    run_git(['git', 'commit', '-m', f'chore: BMAD autosave {agente_id}'], check=True)

# ==========================================
# VIGILANTE DE CIERRE
# Un agente puede terminar su turno (idle/done) mostrando el dictamen solo en su chat, sin registrar el bloque
# en el tracker. Como el tracker es el único bus, el flujo se detiene en silencio. El vigilante lo detecta,
# le recuerda al agente que registre y, si no lo hace tras MAX_RECORDATORIOS, deja constancia en el tracker.
# ==========================================
ROLES_TRACKER_POR_AGENTE = dict(TRACKER_AUTHORS)   # copia: el outbox valida contra la tabla de config
MAX_RECORDATORIOS = 2
GRACIA_SIN_TRABAJO_S = 90     # si el agente nunca pasa a 'working', se evalúa tras este tiempo
IDLE_MINIMO_S = 20            # tiempo mínimo en idle/done antes de considerarlo terminado
INTERVALO_VIGILANTE_S = 8
seguimiento_agentes = {}
_ultimo_chequeo_vigilante = 0

def autores_en_tracker():
    """Autores de todos los bloques del tracker, en orden."""
    try:
        contenido = Path(TRACKER_PATH).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return []
    return [a.strip() for a in re.findall(r"^###\s+\[[^\]]+\]\s+(.+)$", contenido, flags=re.MULTILINE)]

def agente_registro_bloque(agente, desde_indice):
    roles = ROLES_TRACKER_POR_AGENTE.get(agente)
    if not roles:
        return True  # agente sin rol conocido: no se vigila
    return any(a.lower().startswith(r.lower()) for a in autores_en_tracker()[desde_indice:] for r in roles)

def registrar_seguimiento(agente, pane_id, ahora=None, event_id=None):
    """Llamar justo después de despachar una tarea al agente."""
    if agente not in ROLES_TRACKER_POR_AGENTE:
        return
    ahora = ahora if ahora is not None else time.time()
    seguimiento_agentes[agente] = {
        "pane_id": pane_id, "bloques_al_despachar": len(autores_en_tracker()),
        # 'despachado' se renueva con cada recordatorio; 'inicio' mide la operación completa (guard).
        "despachado": ahora, "inicio": ahora,
        "vio_trabajando": False, "idle_desde": None, "recordatorios": 0,
        "event_id": event_id,
    }
    runtime().state.put('followup', seguimiento_agentes)

def marcar_handoff(est, etapa, **detalles):
    """Metadato de trazabilidad del handoff seguido; no altera el estado canónico."""
    if est.get("event_id"):
        mark_handoff(runtime().state, est["event_id"], etapa, **detalles)

def agente_de_autor(autor):
    """Agente interactivo dueño de un autor de bloque; None para WATCHER, humanos y sesiones headless."""
    autor = (autor or "").lower()
    return next((agente for agente, roles in ROLES_TRACKER_POR_AGENTE.items()
                 if any(autor.startswith(rol.lower()) for rol in roles)), None)

# Fase 4F-E5.1: autores que nunca autorizan nada desde el tracker.
# - Sesiones headless de Spec Kit: su directiva lleva NO_TOCAR_TRACKER; si igualmente escriben, el bloque se audita.
# - Autores del propio motor: sus bloques salen siempre de TrackerWriter; uno sin journal fue escrito por otro proceso.
AUTORES_HEADLESS = ("DEV-BACK", "DEV-FRONT")
AUTORES_MOTOR = ("WATCHER", "Senior Backend Developer", "Senior Frontend Developer")
_CABECERA = re.compile(r"###\s+\[[^\]]+\]\s+(.+)")

def cabecera_en_journal(lineas, inicio):
    """True si la cabecera de la línea `inicio` está dentro de un append `done` del journal de TrackerWriter."""
    previas = sum(1 for linea in lineas[:inicio] if _CABECERA.match(linea.strip()))
    try:
        datos = Path(TRACKER_PATH).read_bytes()
    except OSError:
        return False
    posiciones = [m.start() for m in re.finditer(rb"(?m)^###\s+\[", datos)]
    if previas >= len(posiciones):
        return False
    posicion = posiciones[previas]
    almacen = StateStore.in_directory(escritor_tracker().state_dir)      # el journal del escritor de este tracker
    try:
        for _, raw in almacen.db.execute("SELECT id,data FROM records WHERE id LIKE 'tracker_append:%'"):
            registro = json.loads(raw)
            if registro.get('state') == 'done' and \
                    registro['offset'] <= posicion < registro['offset'] + registro['length']:
                return True
    finally:
        almacen.close()
    return False

def motivo_bloque_no_autorizado(lineas, numero):
    """(motivo | None, línea de cabecera) del bloque que contiene `numero`: headless_write o unjournaled_engine_block."""
    from bmad_runtime.hu_enforcement import block_start
    inicio = block_start(lineas, numero)
    cabecera = _CABECERA.match(lineas[inicio].strip()) if lineas else None
    if not cabecera:
        return None, inicio
    autor = cabecera.group(1).strip()
    if autor in AUTORES_HEADLESS:
        return "headless_write", inicio
    if autor in AUTORES_MOTOR and not cabecera_en_journal(lineas, inicio):
        return "unjournaled_engine_block", inicio
    return None, inicio

def linea_con_macro(linea):
    """La línea ordena una operación del motor (GitOps, freeze, Spec Kit o respuesta a clarify)."""
    baja = linea.lower()
    return bool(macro_gitops(linea, "BRANCH-CREATE") or macro_gitops(linea, "MERGE-CLOSE")
                or "@watcher: sdd-freeze" in baja or "@spec-kit:" in baja or "@watcher: /speckit.clarify" in baja)

def auditar_bloque_no_autorizado(event_key, motivo, lineas, inicio, numero):
    """Nada del bloque se ejecuta ni se despacha; queda auditado en SQLite. Una macro o un bloque del motor sin
    journal además deja un aviso @HUMANO: (pausa el flujo) una sola vez por bloque."""
    estado = runtime().state
    estado.put(event_key, {**(estado.get(event_key) or {}), 'state': 'done', 'outcome': 'suppressed',
                           'reason': motivo, 'updated': time.time()})
    clave = f"blocked_write:{StateStore.fingerprint(inicio, lineas[inicio])[:32]}"
    registro = estado.get(clave) or {'state': 'audited', 'reason': motivo, 'block_line': inicio + 1,
                                     'author': lineas[inicio].strip()[:120], 'time': time.time()}
    grave = motivo == "unjournaled_engine_block" or linea_con_macro(lineas[numero])
    if grave and registro['state'] != 'requiere_intervencion':
        registro = {**registro, 'state': 'requiere_intervencion', 'macro_line': numero + 1}
        estado.put(clave, registro)
        anexar_tracker(aviso_bloque_no_autorizado(registro, clave), op_id='blocked-write-' + clave.split(':')[1])
        print(f"🛑 [Protocolo] Bloque no autorizado ({motivo}) en la línea {inicio + 1}: no se ejecuta ni despacha.")
    elif not estado.get(clave):
        estado.put(clave, registro)
        print(f"⚠️ [Protocolo] Bloque escrito por una sesión headless (línea {inicio + 1}): auditado; no despacha nada.")

def aviso_bloque_no_autorizado(registro, clave):
    from datetime import datetime
    ahora = datetime.now()
    origen = ("una sesión headless de Spec Kit, que no debe escribir el tracker" if registro['reason'] == "headless_write"
              else "un proceso ajeno al motor con autor del motor y sin journal de TrackerWriter")
    return (f"\n### [{ahora:%d-%m-%Y}] WATCHER\n- **Hora:** {ahora:%H:%M:%S}\n"
            f"- **Mensaje:** 🛑 PROTOCOLO: el bloque de la línea {registro['block_line']} del tracker lo escribió {origen}. "
            "Ninguna de sus líneas se ejecutó ni se despachó (macros incluidas).\n"
            f"- **Handoff:** @HUMANO: Revisa ese bloque y el trabajo asociado antes de continuar ({clave}).\n")

def indice_bloque_registrado(agente, desde_indice):
    """Índice del primer bloque del agente desde desde_indice (mismo criterio que agente_registro_bloque)."""
    roles = ROLES_TRACKER_POR_AGENTE.get(agente, ())
    for indice, autor in enumerate(autores_en_tracker()[desde_indice:], start=desde_indice):
        if any(autor.lower().startswith(rol.lower()) for rol in roles):
            return indice
    return None

def bloque_registrado(agente, desde_indice):
    """Primer bloque del agente a partir del índice de autores (mismo criterio que agente_registro_bloque)."""
    roles = ROLES_TRACKER_POR_AGENTE.get(agente, ())
    try:
        contenido = Path(TRACKER_PATH).read_text(encoding="utf-8", errors="replace")
    except OSError:
        return ""
    cabeceras = list(re.finditer(r"^###\s+\[[^\]]+\]\s+(.+)$", contenido, flags=re.MULTILINE))
    for i, m in enumerate(cabeceras[desde_indice:], start=desde_indice):
        if any(m.group(1).strip().lower().startswith(r.lower()) for r in roles):
            fin = cabeceras[i + 1].start() if i + 1 < len(cabeceras) else len(contenido)
            return contenido[m.start():fin]
    return ""

def registrar_resumen_sesion(agente, est):
    """Memoria verificable del handoff confirmado, previa a cualquier rotación de contexto. Nunca detiene el watcher.

    El guard contrasta los artefactos declarados con su contenido: un bloque confirmado no prueba avance por sí solo.
    """
    if not est.get("event_id"):
        return
    bloque = bloque_registrado(agente, est["bloques_al_despachar"])
    try:
        resumen = runtime().sessions.record_summary(agente, est["event_id"], bloque)
    except (OSError, ValueError, BMADRuntimeError) as exc:
        print(f"⚠️ [Sesiones] No se registró el resumen de '{agente}': {exc}")
        resumen = None
    runtime().guard.on_confirmed(agente, est["event_id"], resumen, block_fields(bloque),
                                 est.get("inicio", est.get("despachado")))

def texto_recordatorio(agente):
    return (
        f"[WATCHER] Tu turno terminó pero NO hay un bloque tuyo nuevo en {TRACKER_PATH}, y el flujo no puede "
        "avanzar sin él. Registra ahora tu resultado con la skill tracker-logger (formato estándar: Hora, Artefacto generado, "
        "Estado, Puntos Abiertos y Handoff con el token del siguiente agente). Si tu dictamen es RECHAZADO, etiqueta cada "
        "hallazgo con [CAPA:SPEC|PLAN|TASKS|CODE] y asigna DEV-BACK, DEV-FRONT o QA-AUTO en el Handoff. Si necesitas una "
        "decisión humana, regístralo igualmente con Handoff hacia HUMANO."
    )

def texto_recordatorio_outbox(registro):
    """Recordatorio de un despacho por outbox: publica en la ruta asignada, nunca en el tracker."""
    falta = ("está incompleta: falta la marca final BMAD-OUTBOX-END" if registro["state"] == "writing"
             else "no existe")
    return (f"[WATCHER] Tu turno terminó pero tu respuesta en {registro['path']} {falta}, y el flujo no puede avanzar "
            "sin ella. Publícala ahora siguiendo el CANAL DE SALIDA: OUTBOX de tu archivo de tarea (marcas de inicio y "
            "fin exactas, un único bloque tracker-logger). No escribas en el tracker.")

def confirmar_handoff_outbox(registro):
    """Handoff confirmado por el outbox (Fase 4F-E5): resumen de sesión y fin del seguimiento, una sola vez."""
    agente = registro["agent"]
    est = seguimiento_agentes.get(agente)
    if est and est.get("event_id") == registro["event_id"]:
        registrar_resumen_sesion(agente, est)
        del seguimiento_agentes[agente]
        runtime().state.put('followup', seguimiento_agentes)
    print(f"📬 [Outbox] Respuesta de '{agente}' incorporada al tracker; handoff confirmado ({registro['path']}).")

def incidencia_outbox(registro):
    """Entrega rechazada o incierta: el aviso @HUMANO: ya está persistido; se libera el seguimiento sin confirmar."""
    agente = registro.get("agent")
    est = seguimiento_agentes.get(agente) if agente else None
    if est and est.get("event_id") == registro.get("event_id"):
        del seguimiento_agentes[agente]
        runtime().state.put('followup', seguimiento_agentes)
    if agente:
        runtime().guard.error(agente, "outbox:" + str(registro.get("reason")), event_id=registro.get("event_id"))
    print(f"🛑 [Outbox] {outbox.describe(registro)}: {registro.get('path') or registro.get('name')} "
          f"({registro.get('reason')}). Despachos retenidos hasta reconciliar con python -m bmad_runtime.outbox.")

# Texto de la consola de Claude Code cuando se agota (o se restablece) el límite de uso de la cuenta.
def leer_panel(pane_id, lineas=40):
    return runtime().gateway.read(pane_id, lineas)

def vigilar_agentes_inactivos(ahora=None, forzar=False, solo_confirmar=False):
    """Revisa los agentes con tarea despachada; recuerda o escala si terminaron sin registrar en el tracker.

    `solo_confirmar` (flujo en pausa humana o retenido): solo confirma los bloques ya registrados, sin recordar ni
    escalar. Confirmar el handoff es técnico (el bloque está en el tracker) y no levanta la pausa: esa la levanta
    únicamente un bloque humano posterior (watcher_service.paused_for_human). Igual en ambos canales."""
    global _ultimo_chequeo_vigilante
    ahora = ahora if ahora is not None else time.time()
    if not seguimiento_agentes or (not forzar and ahora - _ultimo_chequeo_vigilante < INTERVALO_VIGILANTE_S):
        return
    _ultimo_chequeo_vigilante = ahora

    for agente in list(seguimiento_agentes):
        est = seguimiento_agentes[agente]
        # Canal del despacho persistido (Fase 4F-E5), nunca el modo actual: un despacho outbox solo se confirma con
        # su entrega ingerida; un bloque del agente en el tracker no lo confirma.
        registro = outbox.for_dispatch(runtime().state, est["event_id"]) if est.get("event_id") else None
        if registro is not None:
            if registro["state"] == "confirmed":
                confirmar_handoff_outbox(registro)        # caída entre la ingesta y la liberación del seguimiento
                continue
            if registro["state"] in outbox.INCIDENT_STATES:
                del seguimiento_agentes[agente]
                continue
            if registro["state"] not in ("expected", "writing"):
                continue                                  # recibido: el watcher lo valida e incorpora
        elif agente_registro_bloque(agente, est["bloques_al_despachar"]):
            # El índice del bloque confirmado lo autoriza ante la auditoría de protocolo (audit_blocks).
            marcar_handoff(est, "confirmado", confirmed_block=indice_bloque_registrado(agente, est["bloques_al_despachar"]))
            registrar_resumen_sesion(agente, est)
            del seguimiento_agentes[agente]
            continue

        if solo_confirmar:
            continue
        pane_id, estado = obtener_info_agente(agente)
        if not pane_id:
            continue
        est["pane_id"] = pane_id

        if estado not in ("idle", "done"):
            if estado == "working" and not est["vio_trabajando"]:
                runtime().guard.event("work_started", agente, event_id=est.get("event_id"))
            if estado == "blocked" and not est.get("vio_bloqueado"):
                # Permiso o diálogo pendiente: solo se registra; nunca se responde automáticamente.
                runtime().guard.event("permission_blocked", agente, event_id=est.get("event_id"),
                                      reason="herdr_blocked")
            est["vio_bloqueado"] = estado == "blocked"
            est["vio_trabajando"] = est["vio_trabajando"] or estado == "working"
            est["idle_desde"] = None
            continue

        if est["idle_desde"] is None:
            est["idle_desde"] = ahora
        terminado = est["vio_trabajando"] or ahora - est["despachado"] >= GRACIA_SIN_TRABAJO_S
        if not terminado or ahora - est["idle_desde"] < IDLE_MINIMO_S:
            continue

        # Límite de uso de la cuenta: el agente no puede trabajar y los recordatorios solo gastarían turnos.
        # Se anota el motivo real una vez por cambio de estado y se deja de insistir hasta que se restablezca.
        texto_panel = leer_panel(pane_id)
        _, provider = runtime().dispatcher.provider(agente)
        limit_state = provider.limit_state(texto_panel)
        if limit_state:
            tipo = "reanudar" if limit_state == "resume" else "limite"
            if est.get("aviso_limite") != tipo:
                est["aviso_limite"] = tipo
                if tipo == "limite":
                    motivo = (f"El agente '{agente}' alcanzó el límite de uso de la cuenta del proveedor: el flujo queda en pausa hasta que "
                              "se restablezca. No se envían recordatorios mientras tanto.")
                else:
                    motivo = (f"El límite de uso de la cuenta ya se restableció, pero '{agente}' espera que pulses Enter en su panel "
                              f"({pane_id}) para continuar. No se envían recordatorios.")
                write_watcher_log(f"⚠️ [Vigilante] {motivo}")
                print(f"⏸️ [Vigilante] {motivo}")
                runtime().guard.error(agente, "provider_limit:" + limit_state, event_id=est.get("event_id"))
            continue
        est["aviso_limite"] = None


        if est["recordatorios"] >= MAX_RECORDATORIOS:
            if registro is not None:
                # Sin respuesta publicada: nunca se inventa un bloque ni se confirma el handoff.
                motivo = "no_response" if registro["state"] == "expected" else "incomplete_file"
                outbox.escalate(runtime().state, registro["key"], motivo)
                write_watcher_log(
                    f"⚠️ [Vigilante] El agente '{agente}' terminó su turno {est['recordatorios'] + 1} veces sin publicar "
                    f"su respuesta completa en {registro['path']} ({motivo}). El flujo está detenido: revisa su trabajo "
                    "con python -m bmad_runtime.outbox --status; una respuesta tardía no se incorpora sin reconciliación."
                )
            else:
                write_watcher_log(
                    f"⚠️ [Vigilante] El agente '{agente}' terminó su turno {est['recordatorios'] + 1} veces sin registrar su "
                    "bloque en el tracker. El flujo está detenido: pídele el registro manualmente o escribe el handoff tú."
                )
            print(f"🛑 [Vigilante] '{agente}' no registró tras {est['recordatorios']} recordatorios. Escalado.")
            marcar_handoff(est, "requiere_intervencion")
            runtime().guard.event("no_progress", agente, event_id=est.get("event_id"), reason="escalated_without_block")
            del seguimiento_agentes[agente]
            continue

        try:
            texto = texto_recordatorio_outbox(registro) if registro is not None else texto_recordatorio(agente)
            evento_recordatorio = StateStore.fingerprint('reminder', agente, est['despachado'], est['recordatorios'])
            # Un recordatorio conserva el canal de su despacho; nunca abre otra entrega esperada en el outbox.
            runtime().dispatcher.dispatch(agente, pane_id, texto, evento_recordatorio, reminder=True,
                                          outbox_record=registro)
            est["recordatorios"] += 1
            print(f"🔔 [Vigilante] '{agente}' terminó sin registrar en el tracker. Recordatorio {est['recordatorios']}/{MAX_RECORDATORIOS}.")
            runtime().guard.event("no_progress", agente, event_id=est.get("event_id"), reason="turn_without_block",
                                  reminder=est["recordatorios"])
        except (subprocess.CalledProcessError, OSError, BMADRuntimeError) as e:
            print(f"⚠️ [Vigilante] No se pudo recordar a '{agente}': {e}")
            runtime().guard.error(agente, "reminder_failed:" + type(e).__name__, event_id=est.get("event_id"))
            continue
        est.update(despachado=ahora, vio_trabajando=False, idle_desde=None)

def limpiar_sesiones_agentes():
    """Al cerrar una HU solo se sugiere el mantenimiento: limpiar o rotar exige confirmación del operador."""
    print("ℹ️ [Sesiones] HU cerrada. Para liberar contexto revisa "
          "'python -m bmad_runtime.maintenance --plan-clear' y confirma --clear/--rotate manualmente.")
    # Sin escribir en el tracker: tras la fusión el árbol queda en la rama base y no debe ensuciarse.

def obtener_info_agente(nombre_agente):
    return runtime().dispatcher.info(nombre_agente)

def hu_desde_feature_json():
    """Ruta de la HU del BA fijada en .specify/feature.json (o None). Lógica en ux_routing.py."""
    return ux_routing.hu_desde_feature_json(DIRECTORIO_RAIZ)

def hu_requiere_interfaz(ruta_hu):
    """True/False según el campo 'Requiere interfaz' de la HU; None si no está declarado. Lógica en ux_routing.py."""
    return ux_routing.hu_requiere_interfaz(ruta_hu, DIRECTORIO_RAIZ)

def decidir_ruta_ux(ruta_hu=None, config_path="config_bmad.json"):
    """
    Decide si la HU pasa por el diseño UX. Devuelve (token, motivo, omitida).
    La regla vive en ux_routing.py (independiente del orquestador); aquí solo se traduce el destino al token del tracker.
    """
    ruta = ux_routing.decidir_ruta_ux(DIRECTORIO_RAIZ, ruta_hu, config_path, config=project_settings())
    return ("@SA:" if ruta.destino == "SA" else "@UX:"), ruta.motivo, ruta.omitida

def determinar_handoff_fase_a(tracker_path: str = None, config_path: str = "config_bmad.json", ruta_hu=None) -> str:
    """Token del siguiente agente tras la fase de negocio (@UX: o @SA:). Se conserva por compatibilidad."""
    return decidir_ruta_ux(ruta_hu, config_path)[0]

def registrar_traspaso_fase_a(ruta_hu=None, resuelta_por_humano=False):
    """
    Escribe en el tracker el traspaso tras specify/clarify. Si el diseño UX se omite, lo deja como un bloque propio
    ('⏭️ [UX] Diseño UX omitido') para que el dashboard marque la etapa como omitida y no como pendiente.
    Ojo: el texto no puede contener 'aprobad…' ni citar una HU aprobada, o la compuerta de negocio se re-dispararía.
    """
    from datetime import datetime
    token, motivo, omitida = decidir_ruta_ux(ruta_hu)
    ahora = datetime.now()
    cabecera = f"\n### [{ahora.strftime('%d-%m-%Y')}] WATCHER\n- **Hora:** {ahora.strftime('%H:%M:%S')}\n"
    if omitida:
        texto = (f"{token} La especificación inicial SDD ha concluido con éxito y el diseño UX se omite ({motivo}). "
                 "Procede con el tech-design y la arquitectura.")
        escrito = cabecera + f"- **Mensaje:** ⏭️ [UX] Diseño UX omitido: {motivo}.\n- **Handoff:** {texto}\n"
    elif resuelta_por_humano:
        texto = f"{token} La ambigüedad ha sido resuelta por el Humano y la especificación SDD ha concluido con éxito. Procede con tu diseño."
        escrito = cabecera + f"- **Mensaje:** ⚙️ [SDD Auto-Runner] Resolución aplicada exitosamente.\n- **Handoff:** {texto}\n"
    else:
        escrito = f"\n{token} La especificación inicial SDD ha concluido con éxito. Procede con tu diseño.\n"
    anexar_tracker(escrito)
    return token, omitida

def carpeta_spec_para_hu(ruta_hu):
    """
    Carpeta de Spec Kit para una HU: specs/<identificador universal>, derivada del nombre del archivo del BA
    (docs/business-analyst/012-motor-reservas.md -> specs/012-motor-reservas). Así la carpeta lleva el mismo número
    y nombre que el ledger y la rama, en lugar del "NNN-nombre-corto" que Spec Kit inventaría por su cuenta.
    Devuelve None si el nombre no cumple el contrato de bmad_runtime/hu_naming.py (NNN-nombre-en-kebab-case.md).
    """
    nombre = Path(str(ruta_hu).replace("\\", "/")).name
    return f"specs/{nombre[:-3]}" if is_hu_filename(nombre) else None

def verificar_carpeta_spec(carpeta_esperada):
    """Comprueba que Spec Kit usó la carpeta fijada: .specify/feature.json la apunta y contiene spec.md."""
    try:
        feature = json.loads((DIRECTORIO_RAIZ / ".specify" / "feature.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return False, "no se pudo leer .specify/feature.json"
    real = str(feature.get("feature_directory", "")).replace("\\", "/").strip("/")
    if Path(real).is_absolute():
        try:
            real = Path(real).relative_to(DIRECTORIO_RAIZ).as_posix()
        except ValueError:
            pass
    if real != carpeta_esperada:
        return False, f".specify/feature.json apunta a '{real or '(vacío)'}'"
    if not (DIRECTORIO_RAIZ / carpeta_esperada / "spec.md").exists():
        return False, "la carpeta no contiene spec.md"
    return True, ""

def ejecutar_sdd_fase_negocio(ruta_hu: str):
    """
    Hito 1 del SDD Auto-Runner: Fase de Negocio (Post-QA).
    """
    print(f"\n🚀 [SDD Negocio] Iniciando specify/clarify para: {ruta_hu}")
    try:
        # 1. Specify
        write_watcher_log("⚙️ [SDD Auto-Runner] Ejecutando análisis funcional (/speckit.specify)...")
        carpeta = carpeta_spec_para_hu(ruta_hu)
        if not carpeta:
            # Sin identificador válido no hay carpeta fijable: no se deja que Spec Kit invente otra.
            msg = (f"🚨 ERROR [SDD Negocio]: nombre de historia inválido: {hu_name_error(Path(str(ruta_hu)).name)}. "
                   "No se ejecuta specify; renombra el archivo manualmente y vuelve a aprobar.")
            print(f"❌ {msg}")
            write_watcher_log(msg)
            return False
        argumentos = (f"{ruta_hu} SPECIFY_FEATURE_DIRECTORY={carpeta} (usa EXACTAMENTE esa carpeta: no generes otro "
                      "nombre ni otro número; esta indicación no forma parte de la descripción de la funcionalidad)")
        if ejecutar_speckit("specify", argumentos, entorno={"SPECIFY_FEATURE_DIRECTORY": carpeta}).returncode != 0:
            return False
        ok, detalle = verificar_carpeta_spec(carpeta)
        if not ok:
            msg = (f"🚨 ERROR [SDD Negocio]: Spec Kit no respetó la carpeta fijada '{carpeta}' ({detalle}). "
                   "Se detiene la fase: revisa specs/ y .specify/feature.json y reintenta.")
            print(f"❌ {msg}")
            write_watcher_log(msg)
            return False

        # 2. Clarify (HITL por Excepción)
        write_watcher_log("⚙️ [SDD Auto-Runner] Verificando ambigüedades (/speckit.clarify)...")
        res_clarify = ejecutar_speckit("clarify")
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
            anexar_tracker(block)
            return False

        # 3. Handoff Dinámico (UX o SA): lo decide ux_phase y el campo 'Requiere interfaz' de la HU
        handoff, _omitida = registrar_traspaso_fase_a(ruta_hu)
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
        if ejecutar_speckit("plan").returncode != 0:
            return False

        write_watcher_log("⚙️ [SDD Auto-Runner] Desglosando tareas de implementación (/speckit.tasks)...")
        if ejecutar_speckit("tasks").returncode != 0:
            return False

        # 2. Analyze (Auditoría Técnica)
        print("🔍 [SDD Arquitectura] Ejecutando auditoría /speckit.analyze...")
        write_watcher_log("⚙️ [SDD Auto-Runner] Ejecutando auditoría técnica (/speckit.analyze)...")
        res_analyze = ejecutar_speckit("analyze")
        if res_analyze.returncode != 0:
            print("🛑 [HITL] Auditoría fallida. Violación de constitución técnica. Pausando.")
            return False

        # 3. Spec Freeze Automático
        print("❄️ [Spec Freeze] Congelando especificación (Plan & Tasks)...")
        GitService(runtime()).freeze()

        # 4. Handoff a DA
        handoff = "@DA:"
        msg = f"{handoff} El plan técnico y las tareas han sido congeladas. Procede con el diseño de persistencia basándote en los nuevos archivos."
        anexar_tracker(f"\n{msg}\n")
        print(f"✅ [SDD Arquitectura] Handoff despachado: {handoff}")
        return True

    except subprocess.CalledProcessError as e:
        print(f"❌ [SDD Arquitectura] Error en subproceso: {e}")
        return False
    except Exception as e:
        print(f"❌ [SDD Arquitectura] Error inesperado: {e}")
        return False

def backend_sin_tareas_pendientes():
    """
    True solo si tasks.md (carpeta de .specify/feature.json) existe y NO queda ninguna tarea sin marcar
    ([ ]) que toque backend. Ante cualquier duda (archivo ausente, ilegible o sin tareas) devuelve False,
    es decir, se conserva el comportamiento anterior y el backend se ejecuta.
    """
    try:
        feature = json.loads((DIRECTORIO_RAIZ / ".specify" / "feature.json").read_text(encoding="utf-8"))
        tasks = project_output(feature["feature_directory"]) / "tasks.md"
        lineas = tasks.read_text(encoding="utf-8", errors="replace").splitlines()
    except (OSError, ValueError, KeyError):
        return False
    tareas = [l for l in lineas if re.match(r"^\s*- \[[ xX]\] T\d+", l)]
    if not tareas:
        return False
    pendientes = [l for l in tareas if re.match(r"^\s*- \[ \]", l)]
    backend = project_settings().get('code_dirs', {}).get('backend')
    if not backend:
        # Without an explicit layout, no technology-specific heuristic may skip tasks.
        return not pendientes
    return not any(backend in line for line in pendientes)

def ejecutar_sdd_fase_implementacion(retrabajo=None):
    """
    Hito 3 del SDD Auto-Runner: Fase D (Implementación) usando SpecKit + Soul Mounting.
    retrabajo: {"autor", "iteracion", "max", "segmentos"} cuando se re-implementa tras un rechazo;
    limita el alcance a las capas con hallazgos y a las tareas [fix:*] de tasks.md.
    """
    print(f"\n⚙️ [SDD Implementación] Iniciando Fase D (Fuerza Bruta + Alma Agéntica)...")
    import json
    import subprocess
    try:
        memory_dir = DIRECTORIO_RAIZ / ".specify" / "memory"
        memory_dir.mkdir(parents=True, exist_ok=True)
        import uuid
        active_directive_path = memory_dir / f"active_agent_directive_{uuid.uuid4().hex}.md"
        
        # Determinar el tipo de proyecto
        project_type = project_settings().get("project_type", "fullstack").lower()
            
        involucra_backend = project_type in ["fullstack", "headless"]
        involucra_frontend = project_type in ["fullstack", "ui"]

        segmentos = retrabajo["segmentos"] if retrabajo else {}
        if retrabajo:
            involucra_backend = involucra_backend and bool(segmentos.get("backend"))
            involucra_frontend = involucra_frontend and bool(segmentos.get("frontend"))
            texto_qa = (
                f"Retrabajo {retrabajo['iteracion']}/{retrabajo['max']} aplicado sobre los hallazgos de {retrabajo['autor']}. "
                f"{sin_tokens(segmentos.get('qa')) or 'Revalida la HU.'} Ejecuta y valida las pruebas y, al aprobar, deriva a Code Review."
            )
        else:
            texto_qa = (
                "La Fase D (Implementación) ha finalizado exitosamente mediante motor SDD. Inicia el diseño de la "
                "matriz de pruebas automatizadas basándote en los criterios de la HU; al terminar, deriva a Code Review."
            )

        def arg_retrabajo(capa):
            if not retrabajo:
                return ""
            return (
                " MODO RETRABAJO: ejecuta SOLO las tareas reabiertas o nuevas con etiqueta [fix:*] de tasks.md "
                f"que correspondan a este alcance; no rehagas tareas ya validadas. Hallazgos a resolver: {segmentos.get(capa, '')}"
            )
        
        # Reintento de solo frontend: si el backend ya no tiene tareas pendientes y su documentación viva
        # existe, se omite. Si no, SpecKit no tocaría backend-architecture.md y el post-check abortaría la
        # fase antes de llegar al frontend. Sin frontend que ejecutar nunca se omite (no habría handoff).
        if involucra_backend and involucra_frontend and backend_sin_tareas_pendientes():
            doc_back = DIRECTORIO_RAIZ / "docs" / "dev-backend" / "backend-architecture.md"
            readme_back = DIRECTORIO_RAIZ / ruta_readme_codigo("backend")
            if doc_back.exists() and doc_back.stat().st_size > 0 and readme_back.exists() and readme_back.stat().st_size > 0:
                involucra_backend = False
                print("⏭️ [SDD Implementación] Backend sin tareas pendientes en tasks.md: se omite y se continúa con Frontend.")
                write_watcher_log("⏭️ [SDD Auto-Runner] Backend sin tareas pendientes en tasks.md; se omite y se continúa con Frontend.")

        # 1. Ejecutar Backend si aplica
        if involucra_backend:
            print("🚀 [Soul Mounting] Montando alma de @DEV-BACK...")
            agent_backend_path = ENGINE_ROOT / "dev-backend" / "AGENTS.md"
            if not agent_backend_path.is_file():
                raise ReconciliationRequired('Falta el perfil de backend; no se ejecuta implementación sin directiva.')
            if agent_backend_path.exists():
                alma_backend = agent_backend_path.read_text(encoding="utf-8")
                
                # TAREA FANTASMA PARA BACKEND (Ruta estricta en docs/)
                tarea_fantasma_back = """
\n\n# TASK-FINAL: Generación de Documentación Viva
Lee obligatoriamente la plantilla maestra compartida en ENGINE_ROOT/dev-backend/templates/backend-architecture-template.md (si existe) o básate en tus reglas. Luego, crea o edita obligatoriamente el archivo 'docs/dev-backend/backend-architecture.md'. APLICA RENDERIZADO SELECTIVO: No regeneres la arquitectura base; únicamente documenta y genera los diagramas Mermaid para las rutas, esquemas o componentes que alteraste en las tareas anteriores. Este paso es un requisito crítico arquitectónico para finalizar. AÚN SI NO HICISTE CAMBIOS EN EL CÓDIGO, DEBES CREAR O TOCAR EL ARCHIVO indicando que la arquitectura actual está vigente.
"""
                tarea_fantasma_back += "\n" + instruccion_readme(ruta_readme_codigo("backend")) + "\n"
                active_directive_path.write_text(alma_backend + tarea_fantasma_back, encoding="utf-8")
            
            ts_inicio_back = time.time()
            try:
                print("🏃 [SpecKit] Ejecutando implementación de Backend...")
                write_watcher_log("⚡ [SDD Auto-Runner] Ejecutando implementación Backend (/speckit.implement)...")
                
                doc_back_path = DIRECTORIO_RAIZ / "docs" / "dev-backend" / "backend-architecture.md"
                doc_back_path.parent.mkdir(parents=True, exist_ok=True)
                res_back = ejecutar_speckit(
                    "implement",
                    instruccion_doc_viva("docs/dev-backend/backend-architecture.md", alcance="backend",
                                         ruta_readme=ruta_readme_codigo("backend")) + arg_retrabajo("backend"),
                    directiva=active_directive_path,
                )
                if res_back.returncode != 0:
                    print("❌ [SpecKit] Falló la ejecución del subproceso para Backend.")
                    return False

                # POST-CHECK DE VALIDACIÓN: Backend Architecture Doc
                if not doc_back_path.exists() or doc_back_path.stat().st_mtime < (ts_inicio_back - 2):
                    salida = (res_back.stdout or "").strip()[-300:].replace("\n", " ")
                    msg_err = f"@WATCHER: 🚨 ERROR: SpecKit omitió la documentación viva de Backend en 'docs/dev-backend/backend-architecture.md'. Salida del proveedor: {salida}"
                    print(f"❌ {msg_err}")
                    write_watcher_log(msg_err)
                    return False

                # POST-CHECK: README del código. Debe existir; si ya existía solo se exige que se mantenga
                # (se actualiza únicamente cuando los cambios lo ameritan, por eso no se exige modificarlo siempre).
                readme_back = DIRECTORIO_RAIZ / ruta_readme_codigo("backend")
                if not readme_back.exists() or readme_back.stat().st_size == 0:
                    msg_err = f"@WATCHER: 🚨 ERROR: SpecKit omitió el README del código de Backend en '{ruta_readme_codigo('backend')}'."
                    print(f"❌ {msg_err}")
                    write_watcher_log(msg_err)
                    return False

                from datetime import datetime
                dt_str = datetime.now().strftime("%d-%m-%Y")
                hr_str = datetime.now().strftime("%H:%M:%S")
                handoff_target = "@DEV-FRONT:" if involucra_frontend else "@QA-AUTO:"
                handoff_text = "Inicia implementación frontend." if involucra_frontend else texto_qa
                block = f"""
### [{dt_str}] Senior Backend Developer
- **Hora:** {hr_str}
- **Artefacto generado:** `docs/dev-backend/backend-architecture.md`
- **Estado:** Implementación backend finalizada exitosamente mediante SDD SpecKit.
- **Handoff:** {handoff_target} {handoff_text}
"""
                anexar_tracker(block)
            finally:
                if active_directive_path.exists():
                    active_directive_path.unlink()
                    print("🧹 [Soul Mounting] Alma de @DEV-BACK desmontada.")
                    
        # 2. Ejecutar Frontend si aplica
        if involucra_frontend:
            print("🚀 [Soul Mounting] Montando alma de @DEV-FRONT...")
            agent_frontend_path = ENGINE_ROOT / "dev-frontend" / "AGENTS.md"
            if not agent_frontend_path.is_file():
                raise ReconciliationRequired('Falta el perfil de frontend; no se ejecuta implementación sin directiva.')
            if agent_frontend_path.exists():
                alma_frontend = agent_frontend_path.read_text(encoding="utf-8")
                
                # TAREA FANTASMA PARA FRONTEND (Ruta estricta en docs/)
                tarea_fantasma_front = """
\n\n# TASK-FINAL: Generación de Documentación Viva
Lee obligatoriamente la plantilla maestra compartida en ENGINE_ROOT/dev-frontend/templates/frontend-architecture-template.md (si existe) o básate en tus reglas. Luego, crea o edita obligatoriamente el archivo 'docs/dev-frontend/frontend-architecture.md'. APLICA RENDERIZADO SELECTIVO: No regeneres la arquitectura base; únicamente documenta y genera los diagramas Mermaid para las rutas, esquemas o componentes que alteraste en las tareas anteriores. Este paso es un requisito crítico arquitectónico para finalizar. AÚN SI NO HICISTE CAMBIOS EN EL CÓDIGO, DEBES CREAR O TOCAR EL ARCHIVO indicando que la arquitectura actual está vigente.
"""
                tarea_fantasma_front += "\n" + instruccion_readme(ruta_readme_codigo("frontend")) + "\n"
                active_directive_path.write_text(alma_frontend + tarea_fantasma_front, encoding="utf-8")
            
            ts_inicio_front = time.time()
            try:
                print("🏃 [SpecKit] Ejecutando implementación de Frontend...")
                write_watcher_log("⚡ [SDD Auto-Runner] Ejecutando implementación Frontend (/speckit.implement)...")
                
                doc_front_path = DIRECTORIO_RAIZ / "docs" / "dev-frontend" / "frontend-architecture.md"
                doc_front_path.parent.mkdir(parents=True, exist_ok=True)
                res_front = ejecutar_speckit(
                    "implement",
                    instruccion_doc_viva("docs/dev-frontend/frontend-architecture.md", alcance="frontend",
                                         ruta_readme=ruta_readme_codigo("frontend")) + arg_retrabajo("frontend"),
                    directiva=active_directive_path,
                )
                if res_front.returncode != 0:
                    print("❌ [SpecKit] Falló la ejecución del subproceso para Frontend.")
                    return False

                # POST-CHECK DE VALIDACIÓN: Frontend Architecture Doc
                if not doc_front_path.exists() or doc_front_path.stat().st_mtime < (ts_inicio_front - 2):
                    salida = (res_front.stdout or "").strip()[-300:].replace("\n", " ")
                    msg_err = f"@WATCHER: 🚨 ERROR: SpecKit omitió la documentación viva de Frontend en 'docs/dev-frontend/frontend-architecture.md'. Salida del proveedor: {salida}"
                    print(f"❌ {msg_err}")
                    write_watcher_log(msg_err)
                    return False

                readme_front = DIRECTORIO_RAIZ / ruta_readme_codigo("frontend")
                if not readme_front.exists() or readme_front.stat().st_size == 0:
                    msg_err = f"@WATCHER: 🚨 ERROR: SpecKit omitió el README del código de Frontend en '{ruta_readme_codigo('frontend')}'."
                    print(f"❌ {msg_err}")
                    write_watcher_log(msg_err)
                    return False

                from datetime import datetime
                dt_str = datetime.now().strftime("%d-%m-%Y")
                hr_str = datetime.now().strftime("%H:%M:%S")
                block = f"""
### [{dt_str}] Senior Frontend Developer
- **Hora:** {hr_str}
- **Artefacto generado:** `docs/dev-frontend/frontend-architecture.md`
- **Estado:** Implementación frontend finalizada exitosamente mediante SDD SpecKit.
- **Handoff:** @QA-AUTO: {texto_qa}
"""
                anexar_tracker(block)
            finally:
                if active_directive_path.exists():
                    active_directive_path.unlink()
                    print("🧹 [Soul Mounting] Alma de @DEV-FRONT desmontada.")

        # 3. Handoff Final: lo emite el último bloque DEV (-> @QA-AUTO:, que luego deriva a @CODE-REVIEW:).
        # No se escribe un handoff extra: duplicaría el despacho y saltaría QA-AUTO.
        print("✅ [Handoff Final] Despachado a @QA-AUTO (luego @CODE-REVIEW).")

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
        # Regla única (watcher_service.paused_for_human): una confirmación técnica del handoff no levanta la pausa.
        return paused_for_human(content)
    except (OSError, ValueError) as exc:
        raise ReconciliationRequired('No se puede determinar el estado HITL del tracker.') from exc

def extraer_instrucciones(linea):
    global last_implement_trigger
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

    # Los bloques "DEV-BACK"/"DEV-FRONT" los escribe por su cuenta la sesión headless de SpecKit (el alma
    # montada trae la skill tracker-logger). El handoff legítimo lo emite el Watcher en los bloques
    # "Senior ... Developer"; despachar también estos duplicaría la tarea y adelantaría a QA-AUTO.
    if contexto_bloque.get("autor") in ("DEV-BACK", "DEV-FRONT"):
        return []

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
        res = ejecutar_speckit("clarify", respuesta_inferida)
        if res.returncode or "?" in res.stdout or "ambiguity" in res.stdout.lower():
            raise ReconciliationRequired("Clarify sigue pendiente; no se emite handoff a arquitectura.")
        
        # Continuar con el handoff dinámico a UX o SA (lo decide ux_phase y el campo 'Requiere interfaz' de la HU)
        handoff, _omitida = registrar_traspaso_fase_a(None, resuelta_por_humano=True)

        print(f"✅ [SDD Negocio] Handoff despachado: {handoff}")
        return []

    if paused:
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
        nombre_hu = find_hu_file(linea)
        if nombre_hu:
            ruta_hu = f"docs/business-analyst/{nombre_hu}"
            print(f"Iniciando SDD Fase de Negocio para: {ruta_hu}\n")
            
            exito = ejecutar_sdd_fase_negocio(ruta_hu)
            if not exito:
                print("🛑 [HITL] Fallo o ambigüedad en SDD Negocio. Pausando el orquestador.")
                raise ReconciliationRequired("Fase SDD negocio pendiente; revisar fallo o preguntas HITL antes de continuar.")
        else:
            motivo = invalid_hu_reference(linea)
            if motivo:
                # Solo se detiene el paso de esta HU: ni specify ni handoff, y el tracker explica el rechazo.
                msg = (f"🚨 ERROR [SDD Negocio]: nombre de historia inválido: {motivo}. "
                       "No se ejecuta specify; renombra el archivo manualmente y vuelve a aprobar.")
                print(f"❌ {msg}")
                write_watcher_log(msg)
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
        
        ruta_hu = find_hu_file(linea) or ""
        
        print(f"Iniciando SDD Fase de Arquitectura...\n")
        exito = ejecutar_sdd_fase_arquitectura(ruta_hu)
        if not exito:
            print("🛑 [HITL] Fallo en SDD Arquitectura. Pausando el orquestador.")
            raise ReconciliationRequired("Fase SDD arquitectura fallida; revisar estado parcial antes de continuar.")
        print("=" * 80 + "\n")
        return []

    # ==========================================
    # SDD GATEKEEPER 4: Retrabajo tras rechazo de CODE-REVIEW / QA-AUTO
    # ==========================================
    if "@dev-back:" in linea_lower or "@dev-front:" in linea_lower:
        autor, hora, bloque = buscar_bloque_tracker(contexto_bloque["autor"], contexto_bloque["hora"])
        if autor is None:
            autor, hora, bloque = buscar_bloque_tracker()
        if autor in AUTORES_REVISORES and "rechaz" in bloque.lower():
            clave_bloque = f"{autor}|{hora}"
            if clave_bloque in retrabajos_procesados:
                return []
            retrabajos_procesados.add(clave_bloque)
            print("\n" + "=" * 80)
            print(f"🔁 [RETRABAJO SDD] RECHAZO DE {autor.upper()} DETECTADO")
            print("=" * 80)
            exito = ejecutar_sdd_retrabajo(autor, bloque)
            if not exito:
                raise ReconciliationRequired("El retrabajo SDD no se completó; revisar estado parcial.")
            print("=" * 80 + "\n")
            return []

    # ==========================================
    # SDD GATEKEEPER 3: Intercepción de QT (Implementación Automática)
    # ==========================================
    if (("@dev-back:" in linea_lower or "@dev-front:" in linea_lower) and "arquitectura" in linea_lower) or "@spec-kit:" in linea_lower:
        if time.time() - last_implement_trigger < 60:
            return []
        last_implement_trigger = time.time()
        print("\n" + "=" * 80)
        print("💡 [GATILLO SDD DETECTADO] INICIANDO FASE D AUTOMÁTICA")
        print("=" * 80)
        print(f"Iniciando SDD Fase de Implementación...\n")
        exito = ejecutar_sdd_fase_implementacion()
        last_implement_trigger = time.time()  # el antirrebote cuenta desde que termina, no desde que empieza
        if not exito:
            raise ReconciliationRequired("Fallo en SDD implementación; revisar estado parcial.")
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
        result = run_git(["git", "rev-parse", "--abbrev-ref", "HEAD"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True, cwd=DIRECTORIO_RAIZ)
        return result.stdout.strip()
    except subprocess.CalledProcessError:
        return None

def get_all_branches():
    try:
        result = run_git(["git", "branch", "--format=%(refname:short)"], capture_output=True, text=True, encoding="utf-8", errors="replace", check=True, cwd=DIRECTORIO_RAIZ)
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
    res = run_git(["git", "status", "--porcelain"], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=DIRECTORIO_RAIZ, check=True)
    return len(res.stdout.strip()) == 0

def auto_commit_security():
    if not check_working_directory_clean():
        if not runtime().config.data['git']['auto_commit']:
            raise ReconciliationRequired('GitOps pausado: hay cambios sin guardar. Confirma tus archivos antes de cambiar de rama; auto_commit está deshabilitado.')
        run_git(['git', 'add', '.'], check=True)
        run_git(['git', 'commit', '-m', 'chore: auto-commit pre-branch switch'], check=True)

def gitops_branch_create(branch_name):
    print(f"\n🌿 [GITOPS] Interceptada macro de creación de rama: {branch_name}")
    if not is_feature_branch(branch_name):
        # Nunca se crea una rama genérica ni se corrige el nombre: el identificador lo fija la HU.
        raise ReconciliationRequired(f"GitOps rechaza la rama '{branch_name}': debe ser feat/NNN-nombre-en-kebab-case "
                                     "(mismo identificador que la HU). No se crea ninguna rama.")
    auto_commit_security()
    run_git(['git', 'check-ref-format', '--branch', branch_name], check=True)
    resetear_retrabajo(branch_name)

    base_branch = get_base_branch()
    current = get_current_branch()
    if current != base_branch:
        run_git(["git", "checkout", base_branch], check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
    try:
        existing = run_git(["git", "branch", "--list", branch_name], capture_output=True, text=True, encoding="utf-8", errors="replace", cwd=DIRECTORIO_RAIZ)
        if existing.stdout.strip() and branch_name in existing.stdout:
            run_git(["git", "checkout", branch_name], check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ [GITOPS] Rama {branch_name} existente reactivada.")
        else:
            run_git(["git", "checkout", "-b", branch_name], check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"✅ [GITOPS] Rama {branch_name} creada y activa.")
    except Exception as e:
        raise ReconciliationRequired("GitOps no pudo crear la rama; no se despacha el siguiente agente.") from e

def comando_reconciliar_evento(evento):
    """Orden exacta (desde la raíz del motor) que marca como atendido un evento in_flight; nunca lo repite."""
    contexto = _runtime.context if _runtime else None
    alcance = '' if contexto is None or contexto.legacy else \
        f' --workspace "{contexto.workspace_root}" --project {contexto.project_id}'
    return f"python -m bmad_runtime.state{alcance} --acknowledge {evento or 'event:<id>'} --confirm"

def gitops_merge_close(branch_name, evento=None):
    confirmar_cierre_rama(branch_name)
    fusionar_rama(branch_name, evento)

def confirmar_cierre_rama(branch_name):
    """Confirmación humana del cierre. En enforce corre sin el lock de HU (nunca se retiene durante una espera)."""
    print(f"\n🚀 [GITOPS] Interceptada macro de fusión (merge-close): {branch_name}")
    run_git(['git', 'check-ref-format', '--branch', branch_name], check=True)
    if input(f"Confirma fusionar y cerrar {branch_name} escribiendo el nombre de rama: ").strip() != branch_name:
        raise ReconciliationRequired('Cierre de rama no confirmado.')

def fusionar_rama(branch_name, evento=None):
    """Fusión --no-ff y borrado de la rama (estrategia sin cambios); en conflicto aborta, alerta y detiene."""
    auto_commit_security()

    base_branch = get_base_branch()
    run_git(["git", "checkout", base_branch], check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
    try:
        run_git(["git", "merge", "--no-ff", "--no-edit", branch_name], check=True, cwd=DIRECTORIO_RAIZ)
        run_git(["git", "branch", "-d", branch_name], check=True, cwd=DIRECTORIO_RAIZ)
        print(f"✅ [GITOPS] Fusión exitosa. Rama {branch_name} eliminada.")
        resetear_retrabajo(branch_name)
        limpiar_sesiones_agentes()
    except subprocess.CalledProcessError:
        print("🛑 [GITOPS] Conflicto de fusión detectado. Abortando merge...")
        run_git(["git", "merge", "--abort"], cwd=DIRECTORIO_RAIZ, stderr=subprocess.DEVNULL)
        run_git(["git", "checkout", branch_name], cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # La macro queda in_flight (fail-closed): reiniciar no la resuelve ni la repite; exige reconciliación manual.
        reconciliar = comando_reconciliar_evento(evento)
        op_id = f"gitops-conflict:{evento[len('event:'):][:64]}" if evento else None
        try:
            # Bloque WATCHER propio: anexado como líneas sueltas quedaba dentro del bloque con la macro de cierre y
            # el watcher y el Control Center lo leían como un cierre completado, no como una consulta al humano.
            # Solo una alerta presente en el tracker cuenta como emitida; una perdida (aunque esté reconocida) no se
            # reemite sola: TrackerWriter exige reconciliarla o autorizar su reemisión, y la pausa se mantiene.
            if not (op_id and escritor_tracker().delivered(op_id)):
                anexar_tracker(alerta_conflicto_gitops(branch_name, base_branch, reconciliar), op_id=op_id)
        except BMADRuntimeError as exc:
            print(f"⚠️ [GITOPS] No se pudo registrar la alerta en el tracker: {exc}")
        print(f"⏸️ [HITL] Se requiere intervención humana. Tras resolver el merge, reconcilia con: {reconciliar}")
        sys.exit(1)

def alerta_conflicto_gitops(branch_name, base_branch, reconciliar):
    """Bloque WATCHER con @HUMANO: tras un conflicto de merge. Nunca contiene la macro de cierre como línea propia."""
    from datetime import datetime
    ahora = datetime.now()
    return (f"\n### [{ahora:%d-%m-%Y}] WATCHER\n- **Hora:** {ahora:%H:%M:%S}\n"
            f"- **Mensaje:** ⚠️ ALERTA GITOPS: conflicto de fusión al cerrar la rama {branch_name}. El Watcher abortó el "
            "merge y se detuvo: la rama NO se fusionó ni se cerró. La macro de cierre queda en curso (in_flight): "
            "reiniciar el Watcher NO la resuelve y volverá a detenerse hasta reconciliarla.\n"
            f"- **Handoff:** @HUMANO: Resuelve manualmente el conflicto de {branch_name} y reconcilia la macro de cierre:\n"
            f"  1. Abre tu terminal y ejecuta manualmente el merge o rebase hacia {base_branch}.\n"
            "  2. Resuelve los conflictos en tu editor y haz el commit final.\n"
            f"  3. Con el Watcher detenido, desde la raíz del motor marca la macro como atendida (no repite el merge): {reconciliar}\n"
            "  4. Vuelve a encender el Watcher con la misma selección (--workspace/--project y --config).\n"
            "  Nota: NO borres ni edites líneas de este tracker.\n")

def macro_gitops(linea, accion):
    """
    Rama de una macro GitOps (`BRANCH-CREATE` / `MERGE-CLOSE`) solo si la línea ES la orden.

    La macro debe abrir la línea (tras viñetas y el prefijo `- **Handoff:**`). Una mención dentro de prosa
    (p. ej. "confirmar si se emite `@WATCHER: GITOPS-MERGE-CLOSE x`") no la ejecuta: antes cualquier cita
    en un dictamen cerraba y fusionaba la rama real. Contrato compartido con hu_lifecycle.
    """
    return gitops_macro(linea, accion)

def observar_ciclo_hu(motivo):
    """Fase 4F-E3 (modo OBSERVE): registra el ciclo de vida observado de las HU del proyecto.

    Nunca bloquea, despacha ni modifica Git o el tracker; un fallo se registra como estado desconocido y
    jamás autoriza abrir otra HU.
    """
    try:
        from bmad_runtime.hu_lifecycle import observe_runtime
        resultado = observe_runtime(runtime(), motivo)
    except Exception as exc:
        print(f"⚠️ [HU] Observación del ciclo de vida no disponible ({type(exc).__name__}); no autoriza nada.")
        return None
    if resultado and resultado[1]:
        observacion = resultado[0]
        abiertas = ', '.join(observacion['open']) or '-'
        print(f"🧭 [HU] Observación ({motivo}): {observacion['status']} · abiertas: {abiertas} "
              "(solo observación; no bloquea)")
    return resultado

def crear_enforcer():
    """Autoridad E4 (una HU abierta por proyecto) solo con ai.hu_lifecycle.mode = enforce; None en observe/off."""
    rt = runtime()
    from bmad_runtime.hu_enforcement import Enforcer, mode_of
    return Enforcer.for_runtime(rt) if mode_of(rt) == 'enforce' else None

def emitir_avisos_hu(enforcer):
    """Bloques WATCHER de rechazos E4 persistidos pero aún no escritos (p. ej. caída tras el rechazo)."""
    for op_key in enforcer.pending_notices():
        enforcer.notify(op_key)

def hydration_gitops():
    if not os.path.exists(TRACKER_PATH):
        return None
    with open(TRACKER_PATH, "r", encoding="utf-8", errors="replace") as f:
        lineas = f.readlines()
    
    orphaned_branch = None
    for linea in lineas:
        rama_crear = macro_gitops(linea, "BRANCH-CREATE")
        rama_cerrar = macro_gitops(linea, "MERGE-CLOSE")
        if rama_crear:
            orphaned_branch = rama_crear
        elif rama_cerrar and rama_cerrar == orphaned_branch:
            orphaned_branch = None
    return orphaned_branch

def validar_constitucion_gitops():
    # GitOps belongs to the framework policy. Never append it to project decisions.
    from bmad_runtime.technical_context import initialize_constitution
    context = _runtime.context if _runtime else ProjectContext(ENGINE_ROOT, DIRECTORIO_RAIZ, 'legacy', True)
    initialize_constitution(context)

def iniciar_watcher():
    rt = runtime()
    from bmad_runtime.config import OPERATIONS
    verified = set()
    for operation in OPERATIONS:
        _, provider, _ = rt.spec.prepare(operation)
        if provider.identifier not in verified:
            provider.verify(rt.runner, DIRECTORIO_RAIZ, headless=True)
            verified.add(provider.identifier)
    print("-" * 50)
    
    print(f"👁️ Watcher BMAD (Sequential Token-Passing) iniciado.")
    print(f"📂 Escuchando cambios en: {TRACKER_PATH}")

    # Escrituras del motor interrumpidas o borradas por una reescritura externa: se resuelven o se detiene sin
    # despachar; nada se reescribe automáticamente (tracker_io).
    escritor = escritor_tracker()
    escritor.recover()
    faltantes_desde = None
    # Fase 4F-E5: políticas efectivas visibles para el Control Center y las CLI (diagnóstico de --config).
    policy_audit.record(rt)
    for diferencia in policy_audit.startup_report(rt):
        print(f"⚠️ [Config] El watcher aplica {diferencia['setting']}={diferencia['watcher']}, pero la configuración "
              f"por defecto (la del Control Center) da {diferencia['local']}.")
    politica_outbox = rt.config.data.get('outbox') or {}
    # El ingestor corre siempre: los despachos outbox se honran aunque el modo haya cambiado tras un reinicio.
    ingestor = outbox.OutboxIngestor(rt.context, rt.state, escritor_tracker,
                                     scan_orphans=politica_outbox.get('mode', 'direct') != 'direct')
    for problema in outbox.publication_compatibility(rt.config):
        print(f"⚠️ [Outbox] '{problema['agent']}' ({problema['provider']}) no podrá publicar su respuesta con sus "
              f"permisos actuales ({problema['issue']}); no se relajan: corrige la selección o usa direct.")
    heredados = [registro for registro in ingestor.pending()
                 if outbox.channel_for(politica_outbox, registro['agent']) != 'outbox']
    if heredados:
        print(f"ℹ️ [Outbox] {len(heredados)} despacho(s) se iniciaron por outbox: se siguen honrando con su canal "
              "original aunque la configuración actual asigne direct.")
    # Bootstrap/recuperación del ciclo de vida de HU: evidencia tal como se encontró, antes de mover HEAD.
    observar_ciclo_hu('startup')
    # Fase 4F-E4: reserva interrumpida resuelta con evidencia Git (o reconcile_required) y avisos pendientes.
    enforcer = crear_enforcer()
    if enforcer is not None:
        recuperado = enforcer.recover()
        if recuperado:
            print(f"🧭 [HU] Reserva interrumpida de {recuperado['hu']}: {recuperado['outcome']} -> {recuperado['state']}.")
        emitir_avisos_hu(enforcer)

    # State Hydration (en enforce solo la HU abierta demostrada: nunca una apertura rechazada o dudosa)
    orphaned = enforcer.hydration_branch() if enforcer is not None else hydration_gitops()
    if orphaned:
        current = get_current_branch()
        if current != orphaned:
            print(f"🔄 [GITOPS] Retomando estado no finalizado. Cambiando a rama {orphaned}")
            auto_commit_security()
            try:
                run_git(["git", "checkout", orphaned], check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            except Exception as exc:
                raise ReconciliationRequired("No se pudo recuperar la rama activa.") from exc
        else:
            print(f"✅ [GITOPS] Estado sincronizado. Continuando en la rama {orphaned}")

    num_lineas_leidas = 0
    avisos_espera = {}
    cola_tareas = []
    service = WatcherService(runtime())
    
    if os.path.exists(TRACKER_PATH):
        lineas = service.startup_lines()
            
        if lineas:
            ultima_linea = lineas[-1]
            print(f"\n📂 Tracker detectado con {len(lineas)} eventos históricos.")
            print(f"Última instrucción registrada:\n>> {ultima_linea}\n")
            
            # First migration asks whether to resume; subsequent restarts restore the cursor.
            respuesta = 'n' if runtime().state.get('tracker_cursor') else input("🔄 ¿Deseas reanudar la ejecución desde esta última instrucción? (s/n): ")
            
            if respuesta.lower() == 's':
                num_lineas_leidas = len(lineas) - 1
                print("🔓 Modo Recuperación: Re-encolando la última tarea...\n")
            else:
                num_lineas_leidas = len(lineas)
                print("🔒 Candado activado: Histórico ignorado. Esperando nuevas instrucciones...\n")
        else:
            num_lineas_leidas = 0
            
    if os.path.exists(TRACKER_PATH):
        initial_lines = service.startup_lines()
        num_lineas_leidas = service.restore_cursor(initial_lines, num_lineas_leidas)
        cola_tareas = service.pending_tasks(initial_lines)
        service.save_cursor(initial_lines, num_lineas_leidas)
        for line in initial_lines[:num_lineas_leidas]:
            actualizar_contexto_bloque(line)
    saved_followup = runtime().state.get('followup')
    if saved_followup:
        seguimiento_agentes.update(saved_followup)

    # Coordinación con el mantenimiento de sesiones (maintenance.py): cada ciclo toma el lock de sesiones y
    # anuncia el protocolo en un latido; mientras un mantenimiento lo retiene, el watcher no lee ni despacha.
    inicio_watcher = time.time()
    lock_sesiones = ProjectLock(runtime().context, SESSION_LOCK)
    aviso_mantenimiento = 0
    watcher_heartbeat(runtime().state, inicio_watcher)

    while True:
        if not lock_sesiones.acquire():
            if time.time() - aviso_mantenimiento >= 60:
                aviso_mantenimiento = time.time()
                print("🔧 [Watcher] Mantenimiento de sesiones en curso; ciclo en pausa sin despachar.")
            time.sleep(2)
            continue
        try:
            watcher_heartbeat(runtime().state, inicio_watcher)
            # Un bloque del journal ausente puede ser una reescritura en curso: se tolera rewrite_grace_seconds.
            ausentes, problemas = escritor.audit()
            faltantes_desde = (faltantes_desde or time.time()) if ausentes else None
            if problemas or (faltantes_desde is not None and time.time() - faltantes_desde
                             >= runtime().config.data['tracker']['rewrite_grace_seconds']):
                escritor.mark_lost(ausentes or problemas)
            # Outbox: archivo publicado -> validación -> TrackerWriter -> handoff confirmado (antes de leer el
            # tracker, para que el bloque incorporado se procese en este mismo ciclo).
            ingestor.tick(confirmar_handoff_outbox, incidencia_outbox)
            en_mantenimiento = maintenance_blocks(runtime().state)
            # Solo líneas completas y coherentes con el historial ya procesado; None = archivo en escritura.
            lineas = service.poll(num_lineas_leidas)
            if lineas is not None:
                if len(lineas) > num_lineas_leidas:
                    nuevas_lineas = lineas[num_lineas_leidas:]
                    for idx, linea in enumerate(nuevas_lineas):
                        actualizar_contexto_bloque(linea)
                        numero_linea_absoluta = num_lineas_leidas + idx
                        # GITOPS Live Interception
                        rama_crear = macro_gitops(linea, "BRANCH-CREATE")
                        rama_cerrar = macro_gitops(linea, "MERGE-CLOSE")
                        # E5.1: bloque headless o de "motor" sin journal: nada de él se ejecuta ni se despacha.
                        motivo_bloque, inicio_bloque = motivo_bloque_no_autorizado(lineas, numero_linea_absoluta)
                        compuerta = ('open' if rama_crear else 'close') if enforcer is not None and \
                            (rama_crear or rama_cerrar) and not motivo_bloque else None
                        event_key, claimed = service.begin_line(numero_linea_absoluta, linea,
                                                                {HU_GATE: compuerta} if compuerta else None)
                        if not claimed:
                            continue
                        if motivo_bloque:
                            auditar_bloque_no_autorizado(event_key, motivo_bloque, lineas, inicio_bloque,
                                                         numero_linea_absoluta)
                            continue
                        if enforcer is not None:
                            # Una macro anterior del mismo bloque sin operación confirmada (rechazada, fallida o
                            # reconocida sin confirmar) retiene todo lo que depende de ella: nada se despacha.
                            bloqueo = enforcer.suppressed_by(lineas, numero_linea_absoluta)
                            if bloqueo:
                                enforcer.suppress(event_key, bloqueo)
                                print(f"🛑 [HU] Línea {numero_linea_absoluta + 1} retenida: depende de {bloqueo}, "
                                      "que no está confirmada. No se despacha.")
                                continue
                        decision = None
                        try:
                            if enforcer is not None and rama_crear:
                                decision = enforcer.open(event_key, numero_linea_absoluta, rama_crear,
                                                         gitops_branch_create)
                            elif enforcer is not None and rama_cerrar:
                                decision = enforcer.close(event_key, numero_linea_absoluta, rama_cerrar,
                                                          lambda rama: fusionar_rama(rama, event_key),
                                                          confirm=confirmar_cierre_rama)
                            elif rama_crear:
                                gitops_branch_create(rama_crear)
                            elif rama_cerrar:
                                gitops_merge_close(rama_cerrar, event_key)
                        except (Exception, SystemExit):
                            # Fallo o conflicto GitOps: se observa el estado resultante y el error sigue su curso.
                            if rama_crear or rama_cerrar:
                                observar_ciclo_hu('gitops-error')
                            raise
                        if decision is not None and decision.rejected:
                            # Rechazo E4 (D5): ni Git ni despacho de este bloque; el evento ya terminó y el aviso
                            # WATCHER (@HUMANO:) pausa el flujo hasta que un humano responda.
                            cola_tareas = enforcer.cancel_block_tasks(cola_tareas, lineas, numero_linea_absoluta,
                                                                      decision.op)
                            print(f"🛑 [HU] {decision.code}: {decision.message}")
                            observar_ciclo_hu('hu-rejected')
                            enforcer.notify(decision.op)
                            continue

                        actualizar_contexto_bloque(linea)
                        nuevas_tareas = extraer_instrucciones(linea)
                        
                        for tarea in nuevas_tareas:
                            cola_tareas.append(service.enqueue(numero_linea_absoluta, linea, tarea))
                        service.complete_line(event_key)
                        if rama_crear or rama_cerrar:
                            observar_ciclo_hu('gitops')
                    num_lineas_leidas = len(lineas)
                    service.save_cursor(lineas, num_lineas_leidas)

            # H11: el tracker no es una cola; un bloque de agente sin despacho del watcher detiene nuevos despachos.
            for violacion in audit_blocks(runtime().state, autores_en_tracker(), agente_de_autor, seguimiento_agentes):
                aviso = (f"🛑 [Protocolo] '{violacion['agent_id']}' registró un bloque sin despacho del watcher "
                         f"(bloque {violacion['block_index']}). Despachos detenidos: revisa ese trabajo y reconcilia con "
                         f"python -m bmad_runtime.state --acknowledge protocol_violation:{violacion['block_index']} --confirm "
                         "(con el watcher detenido).")
                write_watcher_log(aviso)
                print(aviso)
            violaciones = protocol_violations(runtime().state)
            # Entregas outbox rechazadas o inciertas: nada se despacha hasta que un humano las reconozca o resuelva.
            incidencias_outbox = outbox.incidents(runtime().state)

            tareas_no_procesadas = []
            candado_disparo = False

            for tarea in cola_tareas:
                if is_tracker_paused_for_human() or violaciones or incidencias_outbox:
                    if violaciones and time.time() - avisos_espera.get('__protocolo__', 0) >= 60:
                        avisos_espera['__protocolo__'] = time.time()
                        print(f"🛑 [Watcher] {len(violaciones)} ejecución(es) fuera de protocolo sin reconciliar; tareas retenidas.")
                    if incidencias_outbox and time.time() - avisos_espera.get('__outbox__', 0) >= 60:
                        avisos_espera['__outbox__'] = time.time()
                        print(f"🛑 [Watcher] {len(incidencias_outbox)} entrega(s) outbox sin reconciliar; tareas retenidas.")
                    tareas_no_procesadas.append(tarea)
                    continue
                if candado_disparo:
                    tareas_no_procesadas.append(tarea)
                    continue

                agente = tarea['agente']
                mensaje = tarea['mensaje']

                if agente in en_mantenimiento:
                    # Mantenimiento incompleto o incierto: nada se envía hasta reconciliarlo (--reconcile).
                    ahora_espera = time.time()
                    if ahora_espera - avisos_espera.get(agente, 0) >= 60:
                        avisos_espera[agente] = ahora_espera
                        print(f"🔧 [Watcher] '{agente}' tiene el mantenimiento {en_mantenimiento[agente][:12]} sin reconciliar; "
                              "tarea retenida.")
                    tareas_no_procesadas.append(tarea)
                    continue

                estado_registro = (runtime().state.get('agent:' + agente) or {}).get('state')
                if estado_registro in HOLD_STATES:
                    # Arranque sin verificar, diálogo de confianza o mantenimiento: solo un humano lo libera.
                    ahora_espera = time.time()
                    if ahora_espera - avisos_espera.get(agente, 0) >= 60:
                        avisos_espera[agente] = ahora_espera
                        print(f"⏸️ [Watcher] '{agente}' está '{estado_registro}'; tarea retenida hasta "
                              f"'python -m bmad_runtime.maintenance --reconcile {agente} --confirm'.")
                    tareas_no_procesadas.append(tarea)
                    continue

                retencion = runtime().guard.hold(agente)
                if retencion:
                    # Solo en modo enforce: la tarea sigue en cola, sin reintentos ni cambios en el agente.
                    ahora_espera = time.time()
                    if ahora_espera - avisos_espera.get('guard:' + agente, 0) >= 60:
                        avisos_espera['guard:' + agente] = ahora_espera
                        print(f"⏸️ [Guard] '{agente}' retenido: {describir_alerta(retencion)}")
                    tareas_no_procesadas.append(tarea)
                    continue

                seguimiento = seguimiento_agentes.get(agente)
                if seguimiento and seguimiento.get("event_id") != tarea['event_id']:
                    # Idle en Herdr no confirma la tarea anterior: solo su bloque (o la escalada del vigilante)
                    # cierra el seguimiento. Despachar ahora lo sobrescribiría y ese handoff nunca se confirmaría.
                    ahora_espera = time.time()
                    if ahora_espera - avisos_espera.get('seguimiento:' + agente, 0) >= 60:
                        avisos_espera['seguimiento:' + agente] = ahora_espera
                        print(f"⏳ [Watcher] '{agente}' aún no registró el bloque de su tarea anterior; "
                              "la siguiente queda en cola sin despachar.")
                    tareas_no_procesadas.append(tarea)
                    continue

                pane_id, estado = obtener_info_agente(agente)

                if not pane_id:
                    service.mark(tarea, 'fallido', failure='agent_absent')
                    raise ReconciliationRequired(f"Agente {agente} ausente o sin propiedad registrada; lanzar o reconciliar antes de continuar.")
                    
                if estado not in ["idle", "done"]:
                    ahora_espera = time.time()
                    if ahora_espera - avisos_espera.get(agente, 0) >= 60:  # un aviso por minuto, no uno cada 2 s
                        avisos_espera[agente] = ahora_espera
                        print(f"⏳ [Watcher] '{agente}' está {estado}. Esperando turno ({len(cola_tareas)} tarea(s) en cola)...")
                    tareas_no_procesadas.append(tarea)
                    continue 

                print(f"\n🚀 [Watcher] Inyectando tarea a '{agente}'...")
                service.mark(tarea, 'reservado')
                try:
                    runtime().dispatcher.dispatch(agente, pane_id, mensaje, tarea['event_id'])
                except PaneNotReady as exc:
                    # Fase 4F-E5.2.1: pantalla ocupada o ambigua; nada se escribió y la tarea sigue en cola.
                    # Tras dispatcher.unready_limit comprobaciones seguidas el agente queda retenido (AgentBlocked).
                    service.mark(tarea, 'fallido', failure='pane_' + exc.observation.state.lower())
                    ahora_espera = time.time()
                    if ahora_espera - avisos_espera.get('pantalla:' + agente, 0) >= 60:
                        avisos_espera['pantalla:' + agente] = ahora_espera
                        print(f"⏳ [Watcher] {exc}")
                    tareas_no_procesadas.append(tarea)
                    continue
                except AgentBlocked as exc:
                    # H10: nada se envió (un Enter respondería el diálogo); la tarea queda en cola.
                    service.mark(tarea, 'fallido', failure='agent_blocked')
                    runtime().guard.event('permission_blocked', agente, event_id=tarea['event_id'],
                                          reason='dialog_before_dispatch')
                    print(f"⏸️ [Watcher] {exc}")
                    tareas_no_procesadas.append(tarea)
                    continue
                except BaseException as exc:
                    service.failed(tarea, type(exc).__name__)
                    # Entrega incierta o fallida: queda registrada como evidencia; nunca se reintenta sola.
                    runtime().guard.on_dispatch_failure(agente, tarea['event_id'], type(exc).__name__)
                    raise
                service.dispatched(tarea)
                print(f"✅ [Watcher] Tarea despachada a {agente}.")
                runtime().guard.on_dispatch(agente, mensaje, tarea['event_id'])
                registrar_seguimiento(agente, pane_id, event_id=tarea['event_id'])
                candado_disparo = True

            cola_tareas = tareas_no_procesadas
            # La confirmación técnica corre siempre; recordatorios y escaladas solo con el flujo libre.
            vigilar_agentes_inactivos(solo_confirmar=is_tracker_paused_for_human() or bool(violaciones)
                                      or bool(incidencias_outbox))
            runtime().state.put('followup', seguimiento_agentes)
            # Presupuesto y bucles: se recalculan desde SQLite; solo se anuncian las alertas que suben de nivel.
            # Quedan en SQLite y logs/guard.log, nunca en el tracker (no es un bus de alertas).
            for alerta in runtime().guard.tick():
                print(("🛑 " if alerta['level'] in ('PAUSE', 'REQUIRES_INTERVENTION') else "⚠️ ") + describir_alerta(alerta))
            # Mantenimiento recomendado: solo se anuncia (una vez por sesión, causa y evidencia); lo ejecuta un humano.
            for recomendacion in runtime().guard.announce_recommendations(runtime().sessions):
                print("💡 " + describir_recomendacion(recomendacion))
                                
        except KeyboardInterrupt:
            print("\n🛑 Watcher detenido por el usuario.")
            break
        except BMADRuntimeError:
            raise
        except Exception as e:
            raise ReconciliationRequired('Watcher detenido ante fallo inesperado; revisar estado antes de reanudar.') from e
        finally:
            lock_sesiones.release()

        time.sleep(2)

def main(argv=None):
    import argparse
    from bmad_runtime.cli import spec_plan
    parser = argparse.ArgumentParser(description='BMAD watcher with provider-neutral execution')
    parser.add_argument('--dry-run', action='store_true')
    parser.add_argument('--config', type=Path)
    add_project_arguments(parser)
    parser.add_argument('--compile-profiles', action='store_true',
                        help='Explicitly rebuild generated AGENTS.md profiles from modular sources, then exit.')
    args = parser.parse_args(argv)
    global _runtime
    try:
        if args.compile_profiles:
            if args.dry_run:
                parser.error('--compile-profiles cannot be combined with --dry-run')
            if args.workspace or args.project or os.environ.get('BMAD_WORKSPACE') or os.environ.get('BMAD_PROJECT'):
                parser.error('--compile-profiles is engine maintenance; omit project selection')
            with project_lock(ENGINE_ROOT, 'watcher'), project_lock(ENGINE_ROOT, 'fleet'):
                compilar_agentes_modulares()
            return 0
        context = resolve_context(ENGINE_ROOT, workspace=args.workspace, project=args.project, config_path=args.config)
        if args.dry_run:
            print(json.dumps(spec_plan(ENGINE_ROOT, args.config, context), ensure_ascii=False, indent=2))
            return 0
        with project_lock(context, 'watcher'):
            configure_project(Runtime(ENGINE_ROOT, config_path=args.config, context=context))
            iniciar_watcher()
        return 0
    except BMADRuntimeError as exc:
        print(f'ERROR: {exc}')
        return 1
    finally:
        if _runtime:
            _runtime.close()
            _runtime = None
