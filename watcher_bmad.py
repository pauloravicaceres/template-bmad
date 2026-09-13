import time
import os
import json
import subprocess

TRACKER_PATH = r"D:\Paulo\Cursos\DMC\template-bmad\files\tracker_bmad.md"

# Memoria en RAM para recordar qué se le envió a cada agente exitosamente
memoria_envios = {}

def guardar_historial(agente_id, instruccion):
    """Ejecuta un commit automático en Git para el control de cambios"""
    try:
        subprocess.run("git add .", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        mensaje_commit = f"BMAD Auto-Save: {agente_id} finalizó su tarea"
        comando_commit = f'git commit -m "{mensaje_commit}" -m "Instrucción procesada: {instruccion}"'
        subprocess.run(comando_commit, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"📦 [Control de Cambios] Historial guardado por {agente_id}.")
    except subprocess.CalledProcessError:
        pass


def obtener_info_agente(nombre_agente):
    """Consulta Herdr dinámicamente y retorna el (pane_id, estado) del agente."""
    try:
        resultado = subprocess.run("herdr agent list", shell=True, capture_output=True, text=True)
        if resultado.returncode != 0:
            return None, None

        datos = json.loads(resultado.stdout)
        agentes = datos.get("result", {}).get("agents", [])

        for agente in agentes:
            if agente.get("name") == nombre_agente:
                return agente.get("pane_id"), agente.get("agent_status")

        return None, None
    except Exception as e:
        print(f"⚠️ [Watcher] Error al consultar agentes: {e}")
        return None, None


def extraer_instruccion(linea, etiqueta_objetivo, todas_las_etiquetas):
    """Extrae solo el fragmento del mensaje destinado al agente objetivo."""
    inicio = linea.find(etiqueta_objetivo)
    if inicio == -1:
        return None
    
    # Buscar cuál es la etiqueta más cercana que aparece después de la nuestra
    fin = len(linea)
    for otra_etiqueta in todas_las_etiquetas:
        if otra_etiqueta != etiqueta_objetivo:
            pos_otra = linea.find(otra_etiqueta, inicio + len(etiqueta_objetivo))
            if pos_otra != -1 and pos_otra < fin:
                fin = pos_otra
                
    # Retorna el texto limpio, ej: "@UX: Procede con los wireframes."
    return linea[inicio:fin].strip()


def procesar_tracker(linea_actual):
    """
    Retorna True SI Y SOLO SI todos los agentes requeridos en esta línea
    recibieron su instrucción con éxito. Retorna False si alguno estaba ocupado.
    """
    linea = linea_actual.strip()
    
    agentes = {
        "@BS:": "business-storyteller",
        "@PA:": "product-analyst",
        "@PM:": "product-manager",
        "@BA:": "business-analyst",
        "@QA:": "qa-documental",
        "@UX:": "designer-ux"
    }

    todas_entregadas = True
    al_menos_un_target = False

    todas_las_etiquetas = list(agentes.keys())

    for etiqueta, agente_nombre in agentes.items():
        if etiqueta in linea:
            al_menos_un_target = True
            
            # Extraer solo la parte del mensaje que le corresponde a este agente
            mensaje_especifico = extraer_instruccion(linea, etiqueta, todas_las_etiquetas)
            
            # Usamos el mensaje específico para la memoria RAM
            if memoria_envios.get(agente_nombre) == mensaje_especifico:
                continue

            pane_id, estado = obtener_info_agente(agente_nombre)

            if not pane_id:
                print(f"❌ [Watcher] Agente '{agente_nombre}' no encontrado.")
                continue

            if estado != "idle":
                print(f"⏳ [Watcher] '{agente_nombre}' está {estado}. Esperando...")
                todas_entregadas = False
                continue 

            print(f"\n🚀 [Watcher] Evento detectado para '{agente_nombre}'.")
            
            # INYECTAR SOLO EL MENSAJE ESPECÍFICO, NO LA LÍNEA COMPLETA
            linea_escapada = mensaje_especifico.replace('"', '\\"')
            comando = f'herdr pane run {pane_id} "{linea_escapada}"'

            try:
                subprocess.run(comando, shell=True, check=True)
                print(f"✅ [Watcher] Instrucción entregada a '{agente_nombre}'.")
                
                memoria_envios[agente_nombre] = mensaje_especifico
                guardar_historial(agente_nombre, mensaje_especifico)

            except subprocess.CalledProcessError as e:
                print(f"❌ [Watcher] Error de ejecución en '{agente_nombre}'. Código: {e.returncode}")
                todas_entregadas = False

    # Si la línea no tenía etiquetas de agentes, se considera "procesada" para descartarla
    if not al_menos_un_target:
        return True
        
    return todas_entregadas


def iniciar_watcher():
    print(f"👁️ Watcher BMAD asíncrono iniciado.")
    print(f"📂 Escuchando cambios en: {TRACKER_PATH}")
    
    ultima_fecha_mod = 0
    ultima_linea_procesada = ""
    linea_pendiente = None

    if os.path.exists(TRACKER_PATH):
        ultima_fecha_mod = os.path.getmtime(TRACKER_PATH)
        with open(TRACKER_PATH, 'r', encoding='utf-8', errors='replace') as f:
            lineas = [l for l in f.readlines() if l.strip()]
            if lineas:
                ultima_linea_procesada = lineas[-1]
                
        print("🔒 Candado activado: Ignorando el histórico. Esperando nuevas instrucciones...\n")

    while True:
        try:
            # 1. Fase de Lectura: Detectar nuevas instrucciones
            if os.path.exists(TRACKER_PATH):
                fecha_mod_actual = os.path.getmtime(TRACKER_PATH)
                
                if fecha_mod_actual != ultima_fecha_mod:
                    ultima_fecha_mod = fecha_mod_actual
                    with open(TRACKER_PATH, 'r', encoding='utf-8', errors='replace') as f:
                        lineas = [l for l in f.readlines() if l.strip()]
                        if lineas:
                            ultima_linea = lineas[-1]
                            # Si es una línea completamente nueva, entra a la cola
                            if ultima_linea != ultima_linea_procesada:
                                linea_pendiente = ultima_linea

            # 2. Fase de Ejecución: Bombardear hasta tener éxito
            if linea_pendiente:
                completado_para_todos = procesar_tracker(linea_pendiente)
                
                if completado_para_todos:
                    # Solo cuando TODOS los agentes de esa línea recibieron su orden, la damos por muerta
                    ultima_linea_procesada = linea_pendiente
                    linea_pendiente = None
                                
        except KeyboardInterrupt:
            print("\n🛑 Watcher detenido por el usuario.")
            break
        except Exception as e:
            print(f"⚠️ [Watcher] Error general: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    iniciar_watcher()