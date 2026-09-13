from pathlib import Path
import shutil
import sys

AGENTES = {
    "bs:": "business-storyteller",
    "pa:": "product-analyst",
    "pm:": "product-manager",
    "ba:": "business-analyst",
    "qa:": "qa-documental",
    "ux:": "designer-ux",
}

def seleccionar_carpetas():
    opciones = list(AGENTES.items())
    
    print("\n=== LIMPIEZA DE CARPETAS DE AGENTES ===")
    for i, (prefijo, nombre) in enumerate(opciones, 1):
        print(f" [{i}] {nombre}")
    
    print(" [T] Todas las carpetas")
    print(" [0] Cancelar y salir")
    
    while True:
        seleccion = input("\nIngresa los números separados por coma (ej. 1,3,5), 'T' o '0': ").strip().upper()
        
        if seleccion == '0':
            print("Operación cancelada.")
            sys.exit(0)
            
        if seleccion == 'T':
            return AGENTES
            
        carpetas_seleccionadas = {}
        indices_ingresados = seleccion.split(',')
        
        errores = False
        for idx in indices_ingresados:
            idx = idx.strip()
            if idx.isdigit():
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
    # utils/clean_folders.py -> raíz del proyecto
    raiz_proyecto = Path(__file__).resolve().parent.parent
    files_dir = raiz_proyecto / "files"

    print(f"Directorio objetivo: {files_dir}")
    
    carpetas_a_limpiar = seleccionar_carpetas()
    
    print("\nIniciando vaciado de directorios...\n")

    for prefijo, nombre_carpeta in carpetas_a_limpiar.items():
        ruta_carpeta = files_dir / nombre_carpeta

        if not ruta_carpeta.exists():
            print(f"[OMITIDO] La carpeta no existe: {ruta_carpeta.name}")
            continue

        if not ruta_carpeta.is_dir():
            print(f"[ERROR] La ruta no es un directorio: {ruta_carpeta.name}")
            continue

        try:
            # Iterar y borrar únicamente el contenido interno de cada carpeta
            for elemento in ruta_carpeta.iterdir():
                if elemento.is_file() or elemento.is_symlink():
                    elemento.unlink()
                elif elemento.is_dir():
                    shutil.rmtree(elemento)
                    
            print(f"[OK] Contenido eliminado en: {nombre_carpeta}")
        except Exception as e:
            print(f"[ERROR] Fallo al limpiar {nombre_carpeta}: {e}")

    print("\nProceso finalizado. Los archivos en la raíz (ej. tracker_bmad.md) están intactos.")

if __name__ == "__main__":
    main()