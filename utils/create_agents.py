from pathlib import Path
import shutil

AGENTES = {
    "bs:": "business-storyteller",
    "pa:": "product-analyst",
    "pm:": "product-manager",
    "ba:": "business-analyst",
    "qa:": "qa-documental",
    "ux:": "designer-ux",
}

def main():
    # utils/crear_agentes.py -> raíz del proyecto
    raiz_proyecto = Path(__file__).resolve().parent.parent

    agents_dir = raiz_proyecto / "agents"
    prompts_dir = raiz_proyecto / "prompts"

    print(f"Raíz del proyecto: {raiz_proyecto}")
    print()

    for prefijo, nombre_agente in AGENTES.items():
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
        print(f"     {archivo_prompt} -> {archivo_destino}")

    print()
    print("Proceso finalizado.")

if __name__ == "__main__":
    main()
