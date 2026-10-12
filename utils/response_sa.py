import datetime
import os
from pathlib import Path

DIRECTORIO_RAIZ = Path(__file__).resolve().parent.parent
TRACKER_PATH = DIRECTORIO_RAIZ / "docs" / "tracker_bmad.md"

def registrar_respuesta(argv=None):
    import argparse
    import sys
    sys.path.insert(0, str(Path(__file__).resolve().parents[1]))
    from bmad_runtime.context import add_project_arguments, resolve_context
    parser = argparse.ArgumentParser(description='Record a human response in the selected project tracker.')
    add_project_arguments(parser)
    args = parser.parse_args(argv)
    context = resolve_context(Path(__file__).resolve().parents[1], workspace=args.workspace, project=args.project)
    global TRACKER_PATH
    TRACKER_PATH = context.tracker_path
    revisado_hasta = TRACKER_PATH.stat().st_size if TRACKER_PATH.exists() else 0

    print("===================================================")
    print("🤖 BMAD CLI - Entrada del Humano (@HUMANO)")
    print("===================================================")
    print("Pega aquí todo el bloque de tus respuestas estratégicas.")
    print("Cuando termines, presiona Enter, escribe la palabra FIN y vuelve a presionar Enter.\n")

    lineas_entrada = []
    while True:
        try:
            linea = input()
            # Si el usuario escribe 'FIN' (sin importar mayúsculas/minúsculas), termina la captura
            if linea.strip().upper() == "FIN":
                break
            lineas_entrada.append(linea)
        except EOFError:
            # Respaldo de seguridad por si el usuario presiona Ctrl+D / Ctrl+Z por costumbre
            break
    
    texto_completo = "\n".join(lineas_entrada).strip()

    if not texto_completo:
        print("❌ No se ingresó ningún texto. Operación cancelada.")
        return

    # Formatear el texto con indentación para respetar el formato Markdown del tracker
    estado_formateado = "\n".join([f"  {linea}" for linea in lineas_entrada])

    # Obtener fecha y hora actual
    ahora = datetime.datetime.now()
    fecha_str = ahora.strftime("%d-%m-%Y")
    hora_str = ahora.strftime("%H:%M:%S")

    # Construir el bloque exacto del tracker
    bloque_tracker = f"""
### [{fecha_str}] Humano
- **Hora:** {hora_str}
- **Artefacto generado:** `N/A (Definiciones Estratégicas)`
- **Estado:** Respuestas al cuestionario estratégico:
{estado_formateado}
- **⚠️ Puntos Abiertos:** Ninguno.
- **Handoff:** @SA: Las definiciones estratégicas han sido resueltas. Procede a compilar el documento tech_guidelines.md utilizando estas reglas y avanza el flujo arquitectónico.
"""

    from bmad_runtime.errors import BMADRuntimeError
    try:
        registrar_bloque(bloque_tracker, revisado_hasta)
    except BMADRuntimeError as exc:
        print(f"\n❌ No se registró la respuesta: {exc}")
        sys.exit(1)

    print("\n✅ ¡Registro guardado exitosamente!")
    print(f"📄 El archivo {TRACKER_PATH} ha sido actualizado con los saltos de línea intactos.")
    print("⚡ El Watcher debería detectar el @SA: y despertar al Solutions Architect de inmediato.")

def registrar_bloque(bloque_tracker, revisado_hasta=None):
    """Anexa el bloque del humano con lock y journal; otra decisión humana posterior a la lectura lo aborta."""
    from bmad_runtime.tracker_io import TrackerWriter, no_human_block_since
    separador = "\n\n" if os.path.exists(TRACKER_PATH) else ""
    TrackerWriter(TRACKER_PATH).append(
        separador + bloque_tracker.strip() + "\n", source='response_sa',
        precondition=no_human_block_since(revisado_hasta) if revisado_hasta is not None else None)

if __name__ == "__main__":
    registrar_respuesta()
