import datetime
import os
from pathlib import Path

DIRECTORIO_RAIZ = Path(__file__).resolve().parent.parent
TRACKER_PATH = DIRECTORIO_RAIZ / "files" / "tracker_bmad.md"

def registrar_respuesta():
    
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

    # Validar si el tracker existe para anexarlo de forma segura
    modo_apertura = "a" if os.path.exists(TRACKER_PATH) else "w"
    
    with open(TRACKER_PATH, modo_apertura, encoding="utf-8") as f:
        # Añadir un salto de línea inicial si estamos anexando a un archivo existente
        if modo_apertura == "a":
            f.write("\n\n")
        f.write(bloque_tracker.strip() + "\n")

    print("\n✅ ¡Registro guardado exitosamente!")
    print(f"📄 El archivo {TRACKER_PATH} ha sido actualizado con los saltos de línea intactos.")
    print("⚡ El Watcher debería detectar el @SA: y despertar al Solutions Architect de inmediato.")

if __name__ == "__main__":
    registrar_respuesta()