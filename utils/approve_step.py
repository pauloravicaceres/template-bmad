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
TRACKER_PATH = DIRECTORIO_RAIZ / "documents" / "tracker_bmad.md"

# ==========================================
# MATRIZ DE APROBACIÓN Y HANDOFF (HITL & SDD BRIDGE)
# ==========================================
APPROVAL_CONFIG = {
    "1": {
        "name": "Business Storyteller (BS) -> PA",
        "folder": "business-storyteller",
        "file_regex": r"(idea_[\w_]+\.md)",
        "message": "@PA: La idea de usuario ha sido auditada y aprobada por negocio en el archivo {file}. Procede con la creación del PRODUCT BRIEF."
    },
    "2": {
        "name": "Product Analyst (PA) -> PM [Pausa HITL Canónica]",
        "folder": "product-analyst",
        "file_regex": r"(pb_[\w_]+\.md)",
        "message": "@PM: El Product Brief ha sido auditado y aprobado formalmente en el archivo {file}. Procede con el análisis estratégico y la creación del Backlog del MVP."
    },
    "3": {
        "name": "Product Manager (PM) -> BA [Pausa HITL de Estrategia]",
        "folder": "product-manager",
        "file_regex": r"(mvp_[\w_]+\.md)",
        "message": "@WATCHER: GITOPS-BRANCH-CREATE feat/{branch_name}\n@BA: El MVP y Backlog han sido aprobados en el archivo {file}. La rama feat/{branch_name} ha sido creada. Procede con el análisis de negocio y redacción de Historias de Usuario para la épica {branch_name}. Usa el identificador universal estricto para crear el archivo físico en documents/business-analyst."
    },
    "4": {
        "name": "Business Analyst (BA) -> QA",
        "folder": "business-analyst",
        "file_regex": r"(hu_[\w_]+\.md)",
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
        import re
        branch_name = "001-HU_epic_generica"
        if TRACKER_PATH.exists():
            with open(TRACKER_PATH, 'r', encoding='utf-8', errors='replace') as f:
                content = f.read()
            match = re.search(r"delegar es\s+(\d{3}-HU_[\w_]+)", content)
            if match:
                branch_name = match.group(1)
                print(f"\n⚡ Identificador extraído automáticamente del Tracker: {branch_name}")
            else:
                print(f"\n⚠️ No se pudo extraer el identificador automáticamente. Usando fallback: {branch_name}")
        config['message'] = config['message'].replace("{branch_name}", branch_name)
    
    # 1. Extraer el nombre del archivo inteligentemente
    archivo_detectado = extract_latest_file(config['file_regex'])
    
    if not archivo_detectado:
        print(f"\n⚠️ No se encontró ningún archivo asociado al {config['name']} en el tracker.")
        archivo_detectado = input("✍️ Ingrese el nombre del archivo manualmente (ej. tasks.md, spec.md o pb_proyecto.md): ").strip()
        if not archivo_detectado:
            print("Operación cancelada.")
            sys.exit(1)
    else:
        print(f"\n📄 Archivo detectado en el tracker: {archivo_detectado}")
        
    # 2. APERTURA AUTOMÁTICA DEL ARCHIVO (Búsqueda multi-ruta resiliente)
    candidatos_ruta = [
        DIRECTORIO_RAIZ / "documents" / config["folder"] / archivo_detectado,
        DIRECTORIO_RAIZ / ".specify" / archivo_detectado,
        DIRECTORIO_RAIZ / "specs" / archivo_detectado,
        DIRECTORIO_RAIZ / "documents" / "business-analyst" / archivo_detectado,
        DIRECTORIO_RAIZ / archivo_detectado
    ]
    ruta_fisica = None
    for cand in candidatos_ruta:
        if cand.exists():
            ruta_fisica = cand
            break
            
    if ruta_fisica:
        print(f"🔍 Abriendo archivo para revisión humana ({ruta_fisica.name})...")
        abrir_archivo_en_so(ruta_fisica)
    else:
        ruta_defecto = DIRECTORIO_RAIZ / "documents" / config["folder"] / archivo_detectado
        print(f"⚠️ El archivo está referenciado en el tracker pero no existe físicamente en:\n{ruta_defecto}")
        
    # 3. Confirmación humana
    confirmacion = input(f"\n❓ ¿Deseas autorizar formalmente el avance hacia la siguiente fase? (s/n): ").strip().lower()
    
    if confirmacion == 's':
        # 4. Formatear y despachar el mensaje de delegación
        mensaje_final = config['message'].format(file=archivo_detectado)
        
        registrar_aprobacion(mensaje_final, archivo_detectado)
            
        print("\n✅ Aprobación registrada con éxito en el tracker.")
        print(f"📝 Se ha añadido al bus de eventos:\n>> {mensaje_final}\n")
        
        # Intercepción para auto-gatillar Spec Kit Implement
        print("🚀 El Watcher detectará este evento y resolverá el proveedor configurado para la operación.")
    else:
        print("\n🛑 Aprobación cancelada. El flujo permanece en pausa HITL segura.")

def registrar_aprobacion(mensaje, artefacto):
    """A human approval starts its own block and releases the preceding HITL gate."""
    from datetime import datetime
    now = datetime.now()
    lines = mensaje.splitlines()
    macros = [line for line in lines if line.startswith('@WATCHER: GITOPS-')]
    handoff = ' '.join(line for line in lines if line not in macros)
    with open(TRACKER_PATH, 'a', encoding='utf-8') as handle:
        handle.write(f"\n### [{now:%d-%m-%Y}] HUMANO\n- **Hora:** {now:%H:%M:%S}\n"
                     f"- **Artefacto generado:** `{artefacto}`\n- **Estado:** APPROVE\n"
                     "- **⚠️ Puntos Abiertos:** Ninguno.\n")
        for macro in macros:
            handle.write(macro + '\n')
        handle.write(f'- **Handoff:** {handoff}\n')


if __name__ == "__main__":
    main()
