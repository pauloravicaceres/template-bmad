import sys
import json
from pathlib import Path
from datetime import datetime

def init_project(nombre_proyecto):
    # Definición de rutas relativas al script
    DIRECTORIO_RAIZ = Path(__file__).resolve().parent
    DIR_FILES = DIRECTORIO_RAIZ / "files"
    CONFIG_PATH = DIRECTORIO_RAIZ / "config_bmad.json"
    TRACKER_PATH = DIR_FILES / "tracker_bmad.md"
    
    # Ecosistema de carpetas (Microservicios de Agentes)
    carpetas_agentes = [
        "business-storyteller",
        "product-analyst",
        "product-manager",
        "business-analyst",
        "qa-documental",
        "designer-ux",
        "solutions-architect",
        "data-architect",
        "api-architect",
        "qa-tech"
    ]
    
    print(f"\n🚀 Inicializando proyecto BMAD: {nombre_proyecto}")
    print("=" * 55)
    
    # 1. Scaffolding: Crear estructura física inmutable
    rutas_absolutas = {}
    for carpeta in carpetas_agentes:
        ruta = DIR_FILES / carpeta
        ruta.mkdir(parents=True, exist_ok=True)
        # Se guardan las rutas como strings absolutos para evitar fallos de lectura en los LLMs
        rutas_absolutas[carpeta] = str(ruta.resolve())
        print(f"📁 Estructura verificada: files/{carpeta}/")
        
    # 2. Generar Archivo de Configuración (Single Source of Truth de Rutas)
    config_data = {
        "project_name": nombre_proyecto,
        "created_at": datetime.now().strftime("%Y-%m-%d %H:%M:%S"),
        "tracker": str(TRACKER_PATH.resolve()),
        "routes_bmad": rutas_absolutas
    }
    
    with open(CONFIG_PATH, 'w', encoding='utf-8') as f:
        json.dump(config_data, f, indent=4, ensure_ascii=False)
    print(f"\n⚙️ Archivo de configuración enlazado: config_bmad.json")
    
    # 3. Formateo y Reseteo del Tracker (Creación de archivo en blanco)
    # Se genera un archivo vacío para evitar errores de lectura (FileNotFoundError) en los agentes.
    TRACKER_PATH.write_text("", encoding="utf-8")
    print(f"📝 Archivo tracker_bmad.md inicializado (vacío).")
    
    print("=" * 55)
    print("✅ ¡Ecosistema BMAD preparado! El framework está listo para recibir el input del usuario.")

if __name__ == "__main__":
    if len(sys.argv) > 1:
        nombre = " ".join(sys.argv[1:])
    else:
        nombre = input("✍️ Ingrese el nombre del nuevo proyecto (ej. Sistema de Inventario): ").strip()
        if not nombre:
            print("❌ Error: El nombre del proyecto es obligatorio para inicializar el entorno.")
            sys.exit(1)
            
    init_project(nombre)