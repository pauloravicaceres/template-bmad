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


def seleccionar_agentes():
    opciones = list(AGENTES.items())
    
    print("\n=== SELECCIÓN DE AGENTES ===")
    for i, (prefijo, nombre) in enumerate(opciones, 1):
        print(f" [{i}] {nombre} ({prefijo.rstrip(':')})")
    
    print(" [T] Todos los agentes")
    print(" [0] Cancelar y salir")
    
    while True:
        seleccion = input("\nIngresa los números separados por coma (ej. 1,3,5), 'T' o '0': ").strip().upper()
        
        if seleccion == '0':
            print("Operación cancelada.")
            sys.exit(0)
            
        if seleccion == 'T':
            return AGENTES
            
        agentes_seleccionados = {}
        indices_ingresados = seleccion.split(',')
        
        errores = False
        for idx in indices_ingresados:
            idx = idx.strip()
            if idx.isdigit():
                i = int(idx)
                if 1 <= i <= len(opciones):
                    prefijo, nombre = opciones[i-1]
                    agentes_seleccionados[prefijo] = nombre
                else:
                    print(f"[!] El número {i} está fuera de rango.")
                    errores = True
            else:
                if idx:
                    print(f"[!] Entrada inválida: '{idx}'")
                    errores = True
                    
        if errores or not agentes_seleccionados:
            print("Por favor, intenta nuevamente.")
            continue
            
        return agentes_seleccionados


def main():
    # utils/crear_agentes.py -> raíz del proyecto
    raiz_proyecto = Path(__file__).resolve().parent.parent
    agents_dir = raiz_proyecto / "agents"
    prompts_dir = raiz_proyecto / "prompts"

    print(f"Directorio raíz: {raiz_proyecto}")
    
    # 1. Llamar al menú de selección interactiva
    agentes_a_procesar = seleccionar_agentes()
    
    print("\nIniciando creación de entornos...\n")

    # 2. Iterar únicamente sobre la selección del usuario
    for prefijo, nombre_agente in agentes_a_procesar.items():
        codigo = prefijo.rstrip(":")
        archivo_prompt = prompts_dir / f"{codigo}.md"
        carpeta_agente = agents_dir / nombre_agente
        archivo_destino = carpeta_agente / "AGENTS.md"

        # Crear carpeta del agente
        carpeta_agente.mkdir(parents=True, exist_ok=True)

        # Validar que exista el prompt
        if not archivo_prompt.exists():
            print(f"[ERROR] No existe: {archivo_prompt}")
            continue

        # Copiar prompt como AGENTS.md
        shutil.copy2(archivo_prompt, archivo_destino)

        print(f"[OK] {nombre_agente}")
        print(f"     {archivo_prompt.name} -> AGENTS.md")

    print("\nProceso finalizado.")


if __name__ == "__main__":
    main()