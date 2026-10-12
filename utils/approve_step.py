import sys
import re
import os
import platform
import subprocess
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
# Asume que el script está en la carpeta /utils/
DIRECTORIO_RAIZ = Path(__file__).resolve().parent.parent
TRACKER_PATH = DIRECTORIO_RAIZ / "docs" / "tracker_bmad.md"
if str(DIRECTORIO_RAIZ) not in sys.path:
    sys.path.insert(0, str(DIRECTORIO_RAIZ))
from bmad_runtime.hu_naming import HU_FILE_IN_TEXT, hu_id_from_delegation, hu_name_error, last_hu_candidate

# ==========================================
# MATRIZ DE APROBACIÓN Y HANDOFF (HITL & SDD BRIDGE)
# ==========================================
APPROVAL_CONFIG = {
    "1": {
        "name": "Business Storyteller (BS) -> PA",
        "folder": "business-storyteller",
        "file_regex": r"(?<![\w-])(idea-[a-z0-9]+(?:-[a-z0-9]+)*\.md)",
        "message": "@PA: La idea de usuario ha sido auditada y aprobada por negocio en el archivo {file}. Procede con la creación del PRODUCT BRIEF."
    },
    "2": {
        "name": "Product Analyst (PA) -> PM [Pausa HITL Canónica]",
        "folder": "product-analyst",
        "file_regex": r"(?<![\w-])(pb-[a-z0-9]+(?:-[a-z0-9]+)*\.md)",
        "message": "@PM: El Product Brief ha sido auditado y aprobado formalmente en el archivo {file}. Procede con el análisis estratégico y la creación del Backlog del MVP."
    },
    "3": {
        "name": "Product Manager (PM) -> BA [Pausa HITL de Estrategia]",
        "folder": "product-manager",
        "file_regex": r"(?<![\w-])(mvp-[a-z0-9]+(?:-[a-z0-9]+)*\.md)",
        "message": "@WATCHER: GITOPS-BRANCH-CREATE feat/{branch_name}\n@BA: El MVP y Backlog han sido aprobados en el archivo {file}. La rama feat/{branch_name} ha sido creada. Procede con el análisis de negocio y redacción de Historias de Usuario para la épica {branch_name}. Usa el identificador universal estricto para crear el archivo físico en docs/business-analyst."
    },
    "4": {
        "name": "Business Analyst (BA) -> QA",
        "folder": "business-analyst",
        "file_regex": HU_FILE_IN_TEXT,
        "message": "@QA: La Historia de Usuario ha sido revisada en el archivo {file}. Por favor, procede con la auditoría documental contra el Product Brief."
    },
    "5": {
        "name": "Spec Kit (SDD Bridge / clarify) -> UX [Diseño de Interfaces]",
        "folder": "qa-documental",
        "file_regex": r"(requirements\.md|spec\.md|aprobado_qa_[\w_]+\.md)",
        "message": "@UX: El ciclo SDD (/specify -> /clarify) ha concluido con éxito. Procede con el diseño visual y wireframes tomando como Fuente de la Verdad los artefactos spec.md y requirements.md."
    },
    "6": {
        "name": "Spec Kit (SDD Bridge / clarify) -> SA [Bypass Headless]",
        "folder": "qa-documental",
        "file_regex": r"(requirements\.md|spec\.md|aprobado_qa_[\w_]+\.md)",
        "message": "@SA: El ciclo SDD (/specify -> /clarify) ha concluido con éxito. Al ser un proyecto Headless, el diseño UX se omite. Procede con las directrices de arquitectura técnica basadas en spec.md y requirements.md."
    },
    "7": {
        "name": "Designer UX (UX) -> Siguiente Épica hacia PM",
        "folder": "designer-ux",
        "file_regex": r"(ux_[\w_]+\.md)",
        "message": "@PM: Los wireframes para la HU han sido revisados y aprobados en {file}. Por favor, identifica la siguiente Épica pendiente en el backlog y asígnala al BA."
    },
    "8": {
        "name": "Designer UX (UX) -> Conclusión de MVP hacia Solutions Architect",
        "folder": "designer-ux",
        "file_regex": r"(ux_[\w_]+\.md)",
        "message": "@SA: El diseño visual del MVP ha concluido exitosamente y ha sido aprobado en {file}. Por favor, lee el Product Brief y el MVP, y define el stack tecnológico y las reglas arquitectónicas del proyecto."
    },
    "9": {
        "name": "Solutions Architect (SA) -> DA [Gobernanza Aprobada]",
        "folder": "solutions-architect",
        "file_regex": r"(tech_guidelines\.md)",
        "message": "@DA: Las directrices de arquitectura técnica han sido aprobadas en {file}. Procede con el diseño del Modelo Entidad-Relación (MER)."
    },
    "10": {
        "name": "QA Técnico (QT) -> Gatillo Spec Kit Implement (/speckit.implement)",
        "folder": "qa-tech",
        "file_regex": r"(tech-design_[\w_]+\.md)",
        "message": "@SPEC-KIT: La arquitectura técnica ha sido compilada y aprobada en {file}. Gatillar /speckit.implement para despacho de tareas a la Fase D (@DEV-BACK, @DEV-FRONT, @DEVOPS)."
    },
    "11": {
        "name": "QA Técnico (QT) -> Despacho Directo Backend (@DEV-BACK:) [Enjambre Clásico BMAD]",
        "folder": "qa-tech",
        "file_regex": r"(tech-design_[\w_]+\.md)",
        "message": "@DEV-BACK: La arquitectura técnica consolidada ha sido verificada y aprobada formalmente en el archivo {file}. Procede con la implementación del Backend según los contratos y directrices arquitectónicas vigentes."
    },
    "11b": {
        "name": "QA Técnico (QT) -> Despacho Paralelo Full-Stack (@DEV-BACK y @DEV-FRONT) [Fork-Join BMAD]",
        "folder": "qa-tech",
        "file_regex": r"(tech-design_[\w_]+\.md)",
        "message": "@DEV-BACK: La arquitectura técnica ha sido validada. Inicia la implementación del Backend.\n@DEV-FRONT: La arquitectura técnica ha sido validada. Inicia la implementación del Frontend."
    },
    "12": {
        "name": "QA Técnico (QT) -> Despacho Directo Frontend (@DEV-FRONT:) [Enjambre Clásico BMAD]",
        "folder": "qa-tech",
        "file_regex": r"(tech-design_[\w_]+\.md)",
        "message": "@DEV-FRONT: La arquitectura técnica consolidada ha sido verificada y aprobada formalmente en el archivo {file}. Procede con la implementación del Frontend según el diseño UX y los contratos de integración vigentes."
    },
    "13": {
        "name": "Devs (Backend/Frontend) -> Handoff a QA Automation (@QA-AUTO:)",
        "folder": "dev-backend",
        "file_regex": r"([\w_\-\.]+\.(?:cs|ts|js|py|java|go|rs|kt|php|rb|md))",
        "message": "@QA-AUTO: El código fuente de la Feature ha sido implementado y auto-auditado. Procede con el diseño y ejecución de la suite de pruebas automatizadas cubriendo los Criterios de Aceptación (Zero-Tautology)."
    },
    "14": {
        "name": "QA Automation (QA-Auto) -> Handoff a Code Review (@CODE-REVIEW:)",
        "folder": "qa-auto",
        "file_regex": r"([\w_\-\.]*(?:test|spec)[\w_\-\.]*\.(?:cs|ts|js|py|java|go|rs|md)|[\w_\-\.]+\.md)",
        "message": "@CODE-REVIEW: La suite de pruebas automatizadas y la verificación de Criterios de Aceptación han sido completadas. Procede con la auditoría SecOps, OWASP y calidad técnica integral."
    },
    "15": {
        "name": "Code Review -> Aprobación Final y Handoff a DevOps (@DEVOPS:)",
        "folder": "code-review",
        "file_regex": r"(tracker_bmad\.md)",
        "message": "@DEVOPS: El código y las pruebas han sido aprobados con éxito en la compuerta de Code Review. Procede con el aprovisionamiento de infraestructura, contenedores y pipelines CI/CD."
    }
}

def extract_latest_file(regex_pattern):
    """Lee el tracker y extrae la última ocurrencia del archivo buscado."""
    if not TRACKER_PATH.exists():
        return None
        
    with open(TRACKER_PATH, 'r', encoding='utf-8', errors='replace') as f:
        content = f.read()
        
    matches = re.findall(regex_pattern, content)
    if matches:
        return matches[-1] 
    return None

def abrir_archivo_en_so(ruta):
    """Abre un archivo con el programa predeterminado del sistema operativo."""
    try:
        if platform.system() == 'Windows':
            os.startfile(ruta)
        elif platform.system() == 'Darwin':  # macOS
            subprocess.call(('open', str(ruta)))
        else:  # Linux / Unix
            subprocess.call(('xdg-open', str(ruta)))
    except Exception as e:
        print(f"⚠️ No se pudo abrir el archivo automáticamente. Puede revisarlo manualmente en:\n{ruta}\nError: {e}")

def main(argv=None):
    import argparse
    sys.path.insert(0, str(Path(__file__).resolve().parent.parent))
    from bmad_runtime.context import add_project_arguments, resolve_context
    parser = argparse.ArgumentParser(description='Approve a gate in the selected workspace.')
    add_project_arguments(parser)
    args = parser.parse_args(argv)
    context = resolve_context(Path(__file__).resolve().parent.parent, workspace=args.workspace, project=args.project)
    global DIRECTORIO_RAIZ, TRACKER_PATH
    DIRECTORIO_RAIZ, TRACKER_PATH = context.workspace_root, context.tracker_path
    # Lo que el humano revisa es el tracker hasta aquí: si otra decisión humana llega antes de registrar la suya,
    # la aprobación se rechaza en lugar de duplicar el handoff (sin retener el lock durante la revisión).
    revisado_hasta = TRACKER_PATH.stat().st_size if TRACKER_PATH.exists() else 0
    print("\n" + "="*60)
    print(" 🛡️  SISTEMA DE APROBACIÓN MANUAL (HITL) - FRAMEWORK BMAD ")
    print("="*60)
    print("¿Qué entregable / transición deseas aprobar?\n")
    
    for key, data in APPROVAL_CONFIG.items():
        print(f" [{key}] {data['name']}")
        
    print(" [0] Salir")
    
    opcion = input("\nSeleccione una opción: ").strip()
    
    if opcion == "0":
        print("Saliendo del aprobador...")
        sys.exit(0)
        
    if opcion not in APPROVAL_CONFIG:
        print("❌ Opción inválida.")
        sys.exit(1)
        
    config = APPROVAL_CONFIG[opcion]
    
    if opcion == "3":
        content = TRACKER_PATH.read_text(encoding='utf-8', errors='replace') if TRACKER_PATH.exists() else ""
        branch_name = hu_id_from_delegation(content)
        if branch_name:
            print(f"\n⚡ Identificador extraído automáticamente del Tracker: {branch_name}")
        else:
            # Sin identificador válido no se crea ninguna rama: nada de ramas genéricas ni nombres inventados.
            print("\n⚠️ El tracker no contiene 'delegar es NNN-nombre-en-kebab-case' con un identificador válido.")
            branch_name = input("✍️ Ingrese el identificador de la HU delegada (NNN-nombre-en-kebab-case): ").strip()
            error = hu_name_error(f"{branch_name}.md") if branch_name else "identificador vacío"
            if error:
                print(f"❌ Identificador rechazado: {error}. No se registra la aprobación.")
                sys.exit(1)
        config['message'] = config['message'].replace("{branch_name}", branch_name)

    # 1. Extraer el nombre del archivo inteligentemente
    archivo_detectado = extract_latest_file(config['file_regex'])
    if opcion == "4" and TRACKER_PATH.exists():
        # La HU más reciente manda: si su nombre incumple el contrato no se aprueba otra anterior en su lugar.
        ultima = last_hu_candidate(TRACKER_PATH.read_text(encoding='utf-8', errors='replace'))
        if ultima and hu_name_error(ultima):
            print(f"❌ Historia de usuario rechazada: {hu_name_error(ultima)}. Renómbrala manualmente y vuelve a aprobar.")
            sys.exit(1)

    if not archivo_detectado:
        print(f"\n⚠️ No se encontró ningún archivo asociado al {config['name']} en el tracker.")
        archivo_detectado = input("✍️ Ingrese el nombre del archivo manualmente (ej. tasks.md, spec.md o pb-proyecto.md): ").strip()
        if not archivo_detectado:
            print("Operación cancelada.")
            sys.exit(1)
        if opcion == "4" and hu_name_error(archivo_detectado):
            print(f"❌ Historia de usuario rechazada: {hu_name_error(archivo_detectado)}.")
            sys.exit(1)
    else:
        print(f"\n📄 Archivo detectado en el tracker: {archivo_detectado}")
        
    # 2. Ubicación del entregable con el clasificador compartido (bmad_runtime.artifacts): solo el workspace
    # seleccionado y los directorios de la compuerta; nunca la primera coincidencia ni otro proyecto.
    clasificacion = clasificar_artefacto(context, config["folder"], archivo_detectado)
    if clasificacion is None:
        sys.exit(1)
    if clasificacion.path and clasificacion.status == "PRESENT":
        print(f"🔍 Abriendo archivo para revisión humana ({clasificacion.path})...")
        abrir_archivo_en_so(DIRECTORIO_RAIZ / clasificacion.path)
    elif clasificacion.status == "EXTERNAL_ALLOWED":
        print(f"🔗 Referencia externa autorizada (no se abre automáticamente): {clasificacion.url}")
    for aviso in clasificacion.warnings():
        print(f"⚠️ [{aviso['code']}] {aviso['detail']}")
    artefacto_registrado = clasificacion.path or clasificacion.url or archivo_detectado

    # 3. Confirmación humana
    confirmacion = input(f"\n❓ ¿Deseas autorizar formalmente el avance hacia la siguiente fase? (s/n): ").strip().lower()
    
    if confirmacion == 's':
        # 4. Formatear y despachar el mensaje de delegación
        mensaje_final = config['message'].format(file=archivo_detectado)
        
        from bmad_runtime.errors import BMADRuntimeError
        try:
            registrar_aprobacion(mensaje_final, artefacto_registrado, revisado_hasta)
        except BMADRuntimeError as exc:
            print(f"\n❌ No se registró la aprobación: {exc}")
            sys.exit(1)

        print("\n✅ Aprobación registrada con éxito en el tracker.")
        print(f"📝 Se ha añadido al bus de eventos:\n>> {mensaje_final}\n")
        
        # Intercepción para auto-gatillar Spec Kit Implement
        print("🚀 El Watcher detectará este evento y resolverá el proveedor configurado para la operación.")
    else:
        print("\n🛑 Aprobación cancelada. El flujo permanece en pausa HITL segura.")

def clasificar_artefacto(context, folder, referencia, preguntar=None):
    """Clasificación aceptable del entregable de la opción `folder`, o None si se rechaza (nada se escribe).

    OUTSIDE y OTHER_PROJECT se rechazan; AMBIGUOUS lista los candidatos y pide al humano la ruta exacta (nunca se
    elige uno); MISSING/FUTURE continúan con advertencia (modo warn), como antes la apertura fallida."""
    from bmad_runtime.artifacts import AMBIGUOUS, ArtifactClassifier, load_policy, rule_for_folder
    policy = load_policy(context.engine_root)
    rule = rule_for_folder(folder, policy)
    clasificador = ArtifactClassifier.for_context(context)
    clasificacion = clasificador.classify(referencia, rule)
    if clasificacion.status == AMBIGUOUS:
        print(f"\n⚠️ {clasificacion.detail}")
        exacta = (preguntar or input)("✍️ Ingrese la ruta relativa exacta del entregable (vacío para cancelar): ").strip()
        if not exacta:
            print("Operación cancelada.")
            return None
        clasificacion = clasificador.classify(exacta, rule)
    if clasificacion.rejected:
        print(f"❌ Artefacto rechazado ({clasificacion.status}): {clasificacion.detail} No se registra la aprobación.")
        return None
    return clasificacion


def registrar_aprobacion(mensaje, artefacto, revisado_hasta=None):
    """A human approval starts its own block and releases the preceding HITL gate.

    `revisado_hasta`: tracker size when the human started reviewing; a human decision recorded after it
    (e.g. from the Control Center) aborts this one without writing (tracker_io.TrackerConflict)."""
    from datetime import datetime
    from bmad_runtime.tracker_io import TrackerWriter, no_human_block_since
    now = datetime.now()
    lines = mensaje.splitlines()
    macros = [line for line in lines if line.startswith('@WATCHER: GITOPS-')]
    handoff = ' '.join(line for line in lines if line not in macros)
    bloque = (f"\n### [{now:%d-%m-%Y}] HUMANO\n- **Hora:** {now:%H:%M:%S}\n"
              f"- **Artefacto generado:** `{artefacto}`\n- **Estado:** APPROVE\n"
              "- **⚠️ Puntos Abiertos:** Ninguno.\n"
              + ''.join(macro + '\n' for macro in macros)
              + f'- **Handoff:** {handoff}\n')
    TrackerWriter(TRACKER_PATH).append(
        bloque, source='approve_step',
        precondition=no_human_block_since(revisado_hasta) if revisado_hasta is not None else None)


if __name__ == "__main__":
    main()
