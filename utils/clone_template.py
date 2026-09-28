import os
import sys
import shutil
import argparse
from pathlib import Path

def copy_template(target_dir):
    # Ahora el script está dentro de /utils, por lo que el source_dir (la raíz del proyecto) es el padre del padre
    source_dir = Path(__file__).resolve().parent.parent
    target_path = Path(target_dir).resolve()

    # Prevenir accidentes de sobrescritura en carpetas ocupadas
    if target_path.exists() and os.listdir(target_path):
        print(f"⚠️  ATENCIÓN: La carpeta destino '{target_path}' ya existe y no está vacía.")
        confirm = input("¿Deseas continuar y sobrescribir/fusionar archivos? (s/n): ")
        if confirm.lower() != 's':
            print("Operación cancelada.")
            sys.exit(0)
    
    target_path.mkdir(parents=True, exist_ok=True)

    # ==========================================
    # LISTA BLANCA DE ARTEFACTOS DEL FRAMEWORK
    # ==========================================
    carpetas_permitidas = [
        "business-storyteller", "product-analyst", "product-manager", "business-analyst",
        "qa-documental", "designer-ux", "solutions-architect", "data-architect",
        "api-architect", "qa-tech", "dev-backend", "dev-frontend", "qa-auto",
        "code-review", "devops", "skills", "utils", ".specify", ".github"
    ]

    # Nota: Ya no copiamos "setup.py". Como este script ahora vive en "utils/", se copiará automáticamente con la carpeta "utils"
    archivos_permitidos = [
        "watcher_bmad.py", "init_bmad.py", "config_bmad.json", 
        "AGENTS.md", "README.md", "SETUP.md", "framework_bmad.md",
        "GUIDE.md", "PLUGGABLE_PHASE_D.md", "ARCHITECTURE.md"
    ]

    print(f"\n🚀 Clonando Motor BMAD v2.0 hacia: {target_path}")
    print("=" * 60)

    # 1. Copiar Carpetas
    for carpeta in carpetas_permitidas:
        src = source_dir / carpeta
        dst = target_path / carpeta
        if src.exists() and src.is_dir():
            if dst.exists():
                shutil.rmtree(dst)
            shutil.copytree(src, dst)
            print(f"📁 Copiado: {carpeta}/")

    # 2. Copiar Archivos
    for archivo in archivos_permitidos:
        src = source_dir / archivo
        dst = target_path / archivo
        if src.exists() and src.is_file():
            shutil.copy2(src, dst)
            print(f"📄 Copiado: {archivo}")

    # 3. Limpiar Constitución Técnica (Evita heredar reglas de la plantilla)
    constitution_path = target_path / ".specify" / "memory" / "constitution.md"
    if constitution_path.exists():
        with open(constitution_path, 'w', encoding='utf-8') as f:
            f.write("")
        print("🧹 Limpiado: .specify/memory/constitution.md (Iniciando en Greenfield puro)")

    print("=" * 60)
    print("✅ Plantilla clonada con éxito (Despliegue 100% limpio).")
    print("\n🏁 PRÓXIMOS PASOS RECOMENDADOS:")
    print(f"  1. cd {target_path}")
    print("  2. git init && git add . && git commit -m \"chore: inicialización BMAD v2.0\"")
    print("  3. python init_bmad.py \"Nombre de mi Proyecto\"")
    print("  4. python watcher_bmad.py --branch feat/mi-rama\n")

if __name__ == "__main__":
    parser = argparse.ArgumentParser(description="Clonador seguro de la plantilla BMAD.")
    parser.add_argument("destino", help="Ruta de la carpeta destino donde se creará el nuevo proyecto")
    args = parser.parse_args()
    
    copy_template(args.destino)
