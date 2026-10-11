from pathlib import Path
import sys

# Excelente cambio: Lista simple, más limpia y directa
AGENTS = [
    "business-storyteller", 
    "product-analyst", 
    "product-manager",
    "business-analyst", 
    "qa-documental", 
    "designer-ux",
    "solutions-architect",
    "data-architect",
    "api-architect",
    "qa-tech",
    "dev-backend",
    "dev-frontend",
    "qa-auto",
    "code-review",
    "devops"
]

def seleccionar_carpetas():
    print("\n=== ELIMINACIÓN DE ARCHIVOS AGENTS.md ===")
    for i, nombre in enumerate(AGENTS, 1):
        print(f" [{i}] {nombre}")
     
    return AGENTS
        
def main(argv=None, root=None):
    import argparse
    import os
    argv = sys.argv[1:] if argv is None else argv
    if os.environ.get('BMAD_WORKSPACE') or os.environ.get('WORKSPACE_ROOT') or any(arg.startswith(('--workspace', '--project')) for arg in argv):
        raise SystemExit('Legacy engine maintenance is disabled in a project context.')
    parser = argparse.ArgumentParser(description='Elimina los AGENTS.md generados del motor (regenerables con '
                                                 'watcher_bmad.py --compile-profiles).')
    parser.add_argument('--confirm', action='store_true',
                        help='Autoriza explícitamente la eliminación; sin él solo se listan los archivos.')
    args = parser.parse_args(argv)
    # utils/delete_agents.py -> raíz del motor
    raiz_proyecto = Path(root) if root else Path(__file__).resolve().parent.parent

    print(f"Directorio objetivo: {raiz_proyecto}")

    agentes_a_eliminar = seleccionar_carpetas()

    if not args.confirm:
        # Seguro por defecto: los AGENTS.md pueden tener cambios sin confirmar en Git.
        existentes = [n for n in agentes_a_eliminar if (raiz_proyecto / n / "AGENTS.md").is_file()]
        print(f"\nNo se eliminó nada. {len(existentes)} AGENTS.md se eliminarían; revisa git status y "
              "vuelve a ejecutar con --confirm para autorizarlo.")
        return 0

    print("\nIniciando eliminación de archivos AGENTS.md...\n")

    # Corrección: Iteramos directamente sobre los elementos de la lista
    for nombre_carpeta in agentes_a_eliminar:
        ruta_carpeta = raiz_proyecto / nombre_carpeta

        if not ruta_carpeta.exists():
            print(f"[OMITIDO] La carpeta no existe: {ruta_carpeta.name}")
            continue

        if not ruta_carpeta.is_dir():
            print(f"[ERROR] La ruta no es un directorio: {ruta_carpeta.name}")
            continue

        try:
            # 1. Apuntar específicamente al archivo AGENTS.md en la raíz de cada agente
            archivo_agents = ruta_carpeta / "AGENTS.md"
            
            # 2. Verificar si existe y si es un archivo antes de borrarlo
            if archivo_agents.exists() and archivo_agents.is_file():
                archivo_agents.unlink()
                print(f"[OK] AGENTS.md eliminado en: {nombre_carpeta}")
            else:
                print(f"[OMITIDO] No se encontró AGENTS.md en: {nombre_carpeta}")
                
        except Exception as e:
            print(f"[ERROR] Fallo al limpiar {nombre_carpeta}: {e}")

    print("\nProceso finalizado. Las carpetas internas (agents/, instructions/) están intactas.")
    return 0

if __name__ == "__main__":
    raise SystemExit(main())