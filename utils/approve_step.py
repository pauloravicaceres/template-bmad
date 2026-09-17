import sys
import re
import os
import platform
import subprocess
from pathlib import Path

# ==========================================
# RUTAS Y DIRECTORIOS DINÁMICOS
# ==========================================
# Asume que el script está en la carpeta /utils/
DIRECTORIO_RAIZ = Path(__file__).resolve().parent.parent
TRACKER_PATH = DIRECTORIO_RAIZ / "files" / "tracker_bmad.md"

# ==========================================
# MATRIZ DE APROBACIÓN Y HANDOFF
# ==========================================
# Se ha añadido la clave "folder" para ubicar físicamente el archivo
APPROVAL_CONFIG = {
    "1": {
        "name": "Business Storyteller (BS)",
        "folder": "business-storyteller",
        "file_regex": r"(idea_[\w_]+\.md)",
        "message": "@PA: La idea de usuario ha sido auditada y aprobada por negocio en el archivo {file}. Procede con la creación del PRODUCT BRIEF."
    },
    "2": {
        "name": "Product Analyst (PA)",
        "folder": "product-analyst",
        "file_regex": r"(pb_[\w_]+\.md)",
        "message": "@PM: El Product Brief ha sido auditado y aprobado por negocio en el archivo {file}. Procede con el análisis estratégico y la creación del Backlog."
    },
    "3": {
        "name": "Product Manager (PM)",
        "folder": "product-manager",
        "file_regex": r"(mvp_[\w_]+\.md)",
        "message": "@BA: El MVP y Backlog han sido aprobados en el archivo {file}. Procede con el análisis de negocio y redacción de Historias de Usuario para la siguiente Épica en prioridad."
    },
    "4": {
        "name": "Business Analyst (BA)",
        "folder": "business-analyst",
        "file_regex": r"(hu_[\w_]+\.md)",
        "message": "@QA: La Historia de Usuario ha sido revisada en el archivo {file}. Por favor, procede con la auditoría documental contra el Product Brief."
    },
    "5": {
        "name": "QA Documental (QA)",
        "folder": "qa-documental",
        "file_regex": r"(aprobado_qa_[\w_]+\.md)",
        "message": "@UX: La Historia de Usuario ha sido AUDITADA y APROBADA formalmente por QA Documental (ver certificado {file}). Procede con la fase de diseño UX, elaboración de flujos y wireframes correspondientes."
    },
    "6": {
        "name": "Designer UX (UX)",
        "folder": "designer-ux",
        "file_regex": r"(ux_[\w_]+\.md)",
        "message": "@PM: Los wireframes han sido revisados y aprobados en {file}. Por favor, identifica la siguiente Épica pendiente en el backlog y asígnala al BA."
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

def main():
    print("\n" + "="*55)
    print(" 🛡️  SISTEMA DE APROBACIÓN MANUAL (HITL) - BMAD ")
    print("="*55)
    print("¿De qué agente aprobará su trabajo?\n")
    
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
    
    # 1. Extraer el nombre del archivo inteligentemente
    archivo_detectado = extract_latest_file(config['file_regex'])
    
    if not archivo_detectado:
        print(f"\n⚠️ No se encontró ningún archivo asociado al {config['name']} en el tracker.")
        archivo_detectado = input("✍️ Ingrese el nombre del archivo manualmente (ej. pb_amely.md): ").strip()
        if not archivo_detectado:
            print("Operación cancelada.")
            sys.exit(1)
    else:
        print(f"\n📄 Archivo detectado en el tracker: {archivo_detectado}")
        
    # 2. APERTURA AUTOMÁTICA DEL ARCHIVO
    ruta_fisica = DIRECTORIO_RAIZ / "files" / config["folder"] / archivo_detectado
    
    if ruta_fisica.exists():
        print(f"🔍 Abriendo archivo para revisión...")
        abrir_archivo_en_so(ruta_fisica)
    else:
        print(f"⚠️ El archivo está referenciado en el tracker pero no existe físicamente en:\n{ruta_fisica}")
        
    # 3. Confirmación humana (ahora con el archivo abierto frente a ti)
    confirmacion = input(f"\n❓ ¿Desea aprobar el trabajo de {config['name']} y continuar con el siguiente paso? (s/n): ").strip().lower()
    
    if confirmacion == 's':
        # 4. Formatear y despachar el mensaje de delegación
        mensaje_final = config['message'].format(file=archivo_detectado)
        
        with open(TRACKER_PATH, 'a', encoding='utf-8') as f:
            f.write(f"\n{mensaje_final}")
            
        print("\n✅ Aprobación registrada con éxito.")
        print(f"📝 Se ha añadido al tracker:\n>> {mensaje_final}\n")
        print("🚀 El Watcher detectará este cambio y activará al siguiente agente automáticamente.")
    else:
        print("\n🛑 Aprobación cancelada. El flujo sigue en pausa. Modifique el archivo y vuelva a ejecutar este script cuando esté listo.")

if __name__ == "__main__":
    main()