import time
import os
import json
import subprocess

# Reemplaza con la ruta absoluta real de tu tracker
TRACKER_PATH = r"D:\Paulo\Cursos\DMC\template-bmad\files\tracker_bmad.md"

def guardar_historial(agente_id, instruccion):
    """Ejecuta un commit automático en Git para el control de cambios"""
    try:
        # Añade todos los archivos modificados
        subprocess.run("git add .", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        
        # Crea un commit usando el nombre del agente como autor del cambio
        mensaje_commit = f"BMAD Auto-Save: {agente_id} finalizó su tarea"
        comando_commit = f'git commit -m "{mensaje_commit}" -m "Instrucción procesada: {instruccion}"'
        
        subprocess.run(comando_commit, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"📦 [Control de Cambios] Historial guardado por {agente_id}.")
    except subprocess.CalledProcessError:
        # Falla silenciosamente si no hubo cambios reales en los archivos
        pass

def obtener_pane_id(nombre_agente):
    """Consulta Herdr dinámicamente y retorna el pane_id donde corre el agente."""
    try:
        resultado = subprocess.run(
            "herdr agent list", shell=True, capture_output=True, text=True
        )
        if resultado.returncode != 0:
            return None

        datos = json.loads(resultado.stdout)
        agentes = datos.get("result", {}).get("agents", [])

        for agente in agentes:
            if agente.get("name") == nombre_agente:
                return agente.get("pane_id")

        return None
    except Exception as e:
        print(f"⚠️ [Watcher] Error al consultar la lista de agentes: {e}")
        return None

def procesar_tracker(ultima_linea):
    linea = ultima_linea.strip()

    # Mapeo limpio usando nombres semánticos
    agentes = {
        "@BS:": "business-storyteller",
        "@PA:": "product-analyst",
        "@PM:": "product-manager",
        "@BA:": "business-analyst",
        "@QA:": "qa-documental",
        "@UX:": "designer-ux"
    }

    for etiqueta, agente_nombre in agentes.items():
        if linea.startswith(etiqueta):
            print(f"\n🚀 [Watcher] Evento detectado para '{agente_nombre}'.")

            # 1. Resolución automática de nombre -> pane_id
            pane_id = obtener_pane_id(agente_nombre)

            if not pane_id:
                print(f"❌ [Watcher] El agente '{agente_nombre}' no está registrado o activo en Herdr.")
                return False

            print(f"🎯 [Watcher] Agente '{agente_nombre}' localizado en panel '{pane_id}'.")
            print(f"   Enviando instrucción: {linea}")

            # 2. Inyección y ejecución atómica
            linea_escapada = linea.replace('"', '\\"')
            comando = f'herdr pane run {pane_id} "{linea_escapada}"'

            try:
                subprocess.run(comando, shell=True, check=True)
                print(f"✅ [Watcher] Instrucción entregada exitosamente a '{agente_nombre}' ({pane_id}).")

                # 3. Registro histórico en Git
                guardar_historial(agente_nombre, linea)

            except subprocess.CalledProcessError as e:
                print(f"❌ [Watcher] Error al ejecutar comando en '{agente_nombre}'. Código: {e.returncode}")

            return True

    return False

def iniciar_watcher():
    print(f"👁️ Watcher BMAD iniciado.")
    print(f"📂 Escuchando cambios en: {TRACKER_PATH}")
    
    ultima_fecha_mod = 0
    ultima_linea_procesada = ""

    # ==========================================
    # CANDADO DE INICIALIZACIÓN (ESTADO BASE)
    # ==========================================
    if os.path.exists(TRACKER_PATH):
        # 1. Memoriza la fecha de modificación actual antes de vigilar
        ultima_fecha_mod = os.path.getmtime(TRACKER_PATH)
        
        # 2. Memoriza la última línea actual para no reprocesarla
        with open(TRACKER_PATH, 'r', encoding='utf-8', errors='replace') as f:
            lineas = [l for l in f.readlines() if l.strip()]
            if lineas:
                ultima_linea_procesada = lineas[-1]
                
        print("🔒 Candado activado: Ignorando el histórico del tracker. Esperando nuevas instrucciones...")
    
    print("⏳ Presiona Ctrl+C para detener el monitoreo.\n")

    # ==========================================
    # BUCLE DE MONITOREO (WATCHER)
    # ==========================================
    while True:
        try:
            if os.path.exists(TRACKER_PATH):
                fecha_mod_actual = os.path.getmtime(TRACKER_PATH)
                
                # Solo entra si la fecha de modificación cambió DESPUÉS de encender el candado
                if fecha_mod_actual != ultima_fecha_mod:
                    ultima_fecha_mod = fecha_mod_actual
                    
                    with open(TRACKER_PATH, 'r', encoding='utf-8', errors='replace') as f:
                        lineas = [l for l in f.readlines() if l.strip()]
                        
                        if lineas:
                            ultima_linea = lineas[-1]
                            
                            # Segunda validación: asegura que el texto sea realmente distinto
                            if ultima_linea != ultima_linea_procesada:
                                ultima_linea_procesada = ultima_linea
                                procesar_tracker(ultima_linea)
                                
        except KeyboardInterrupt:
            print("\n🛑 Watcher detenido por el usuario.")
            break
        except Exception as e:
            print(f"⚠️ [Watcher] Error de lectura: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    iniciar_watcher()