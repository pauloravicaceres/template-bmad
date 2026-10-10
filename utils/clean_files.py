from pathlib import Path
import shutil
import sys

AGENTS = {
    "bs:": "business-storyteller",
    "pa:": "product-analyst",
    "pm:": "product-manager",
    "ba:": "business-analyst",
    "qa:": "qa-documental",
    "ux:": "designer-ux",
    "sa:": "solutions-architect",
    "da:": "data-architect",
    "api:": "api-architect",
    "qt:": "qa-tech",
    "dev-back:": "dev-backend",
    "dev-front:": "dev-frontend",
    "qa-auto:": "qa-auto",
    "code-rev:": "code-review",
    "devops:": "devops"
}

def seleccionar_carpetas():
    opciones = list(AGENTS.items())
    
    print("\n=== LIMPIEZA DE CARPETAS DE TRABAJO DE LOS AGENTES ===")
    for i, (prefijo, nombre) in enumerate(opciones, 1):
        print(f" [{i}] {nombre}")
    
    print(" [S] Carpeta specs (y regenerar README.md)")
    print(" [T] Todas las carpetas (incluyendo specs)")
    print(" [0] Cancelar y salir")
    
    while True:
        seleccion = input("\nIngresa los números separados por coma (ej. 1,3,S), 'T' o '0': ").strip().upper()
        
        if seleccion == '0':
            print("Operación cancelada.")
            sys.exit(0)
            
        if seleccion == 'T':
            todas = AGENTS.copy()
            todas['specs'] = 'specs'
            return todas
            
        carpetas_seleccionadas = {}
        indices_ingresados = seleccion.split(',')
        
        errores = False
        for idx in indices_ingresados:
            idx = idx.strip()
            if idx == 'S':
                carpetas_seleccionadas['specs'] = 'specs'
            elif idx.isdigit():
                i = int(idx)
                if 1 <= i <= len(opciones):
                    prefijo, nombre = opciones[i-1]
                    carpetas_seleccionadas[prefijo] = nombre
                else:
                    print(f"[!] El número {i} está fuera de rango.")
                    errores = True
            else:
                if idx:
                    print(f"[!] Entrada inválida: '{idx}'")
                    errores = True
                    
        if errores or not carpetas_seleccionadas:
            print("Por favor, intenta nuevamente.")
            continue
            
        return carpetas_seleccionadas

def main():
    import os
    if os.environ.get('BMAD_WORKSPACE') or os.environ.get('WORKSPACE_ROOT') or any(arg.startswith(('--workspace', '--project')) for arg in sys.argv):
        raise SystemExit('Legacy engine maintenance is disabled in a project context.')
    raiz_proyecto = Path(__file__).resolve().parent.parent
    docs_dir = raiz_proyecto / "docs"
    specs_dir = raiz_proyecto / "specs"
    
    carpetas_a_limpiar = seleccionar_carpetas()
    
    print("\nIniciando vaciado de directorios...\n")

    for prefijo, nombre_carpeta in carpetas_a_limpiar.items():
        if nombre_carpeta == "specs":
            ruta_carpeta = specs_dir
        else:
            ruta_carpeta = docs_dir / nombre_carpeta

        if not ruta_carpeta.exists():
            print(f"[OMITIDO] La carpeta no existe: {ruta_carpeta.name}")
            continue

        if not ruta_carpeta.is_dir():
            print(f"[ERROR] La ruta no es un directorio: {ruta_carpeta.name}")
            continue

        try:
            for elemento in ruta_carpeta.iterdir():
                if elemento.is_file() or elemento.is_symlink():
                    elemento.unlink()
                elif elemento.is_dir():
                    shutil.rmtree(elemento)
            
            print(f"[OK] Contenido eliminado en: {nombre_carpeta}")
            
            if nombre_carpeta == "specs":
                template_path = raiz_proyecto / "utils" / "readme-specs.template.md"
                if template_path.exists():
                    shutil.copy2(template_path, specs_dir / "README.md")
                    print("[OK] README.md regenerado en specs/")
                else:
                    print(f"[WARN] No se encontró el template {template_path}")
                    
        except Exception as e:
            print(f"[ERROR] Fallo al limpiar {nombre_carpeta}: {e}")

    print("\nProceso finalizado. Los archivos en la raíz (ej. tracker_bmad.md) están intactos.")

if __name__ == "__main__":
    main()