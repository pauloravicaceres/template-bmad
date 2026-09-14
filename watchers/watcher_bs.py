import time
import os
import json
import subprocess
import random
from pathlib import Path

# ==========================================
# RUTAS Y DIRECTORIOS DINÁMICOS
# ==========================================
# Si el script está en template-bmad/watchers/watcher_base.py
# .resolve().parent (es watchers) -> .parent (es template-bmad)
DIRECTORIO_RAIZ = Path(__file__).resolve().parent.parent
TRACKER_PATH = str(DIRECTORIO_RAIZ / "files" / "tracker_bmad.md")

# ==========================================
# CONFIGURACIÓN DEL AGENTE
# ==========================================
ETIQUETA_AGENTE = "@BS:" 
NOMBRE_AGENTE = "business-storyteller"


def guardar_historial(instruccion):
    """Manejo de concurrencia y ejecución de Git en el root del proyecto"""
    max_reintentos = 5
    for intento in range(max_reintentos):
        try:
            # Inyectamos cwd=DIRECTORIO_RAIZ para que git add . abarque la carpeta /files
            subprocess.run("git add .", shell=True, check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            
            mensaje_commit = f"BMAD Auto-Save: {NOMBRE_AGENTE} tarea despachada"
            comando_commit = f'git commit -m "{mensaje_commit}" -m "Instrucción: {instruccion[:50]}..."'
            
            # También inyectamos cwd en el commit
            subprocess.run(comando_commit, shell=True, check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"📦 [{NOMBRE_AGENTE}] Commit automático exitoso.")
            break 
        except subprocess.CalledProcessError:
            espera = random.uniform(0.5, 2.0)
            time.sleep(espera)


def obtener_info_agente():
    try:
        resultado = subprocess.run("herdr agent list", shell=True, capture_output=True, text=True)
        if resultado.returncode != 0:
            return None, None

        datos = json.loads(resultado.stdout)
        agentes = datos.get("result", {}).get("agents", [])

        for agente in agentes:
            if agente.get("name") == NOMBRE_AGENTE:
                return agente.get("pane_id"), agente.get("agent_status")

        return None, None
    except Exception:
        return None, None


def extraer_instrucciones(linea):
    """Busca y extrae únicamente la instrucción que le corresponde a este script"""
    if ETIQUETA_AGENTE in linea:
        inicio = linea.find(ETIQUETA_AGENTE)
        fin = len(linea)
        
        # Lista de todas las etiquetas posibles en el proyecto
        etiquetas_conocidas = ["@BS:", "@PA:", "@PM:", "@BA:", "@QA:", "@UX:", "@HUMANO:"]
        
        for otra in etiquetas_conocidas:
            if otra != ETIQUETA_AGENTE:
                pos_otra = linea.find(otra, inicio + len(ETIQUETA_AGENTE))
                if pos_otra != -1 and pos_otra < fin:
                    fin = pos_otra
                    
        return linea[inicio:fin].strip()
    return None


def iniciar_watcher():
    print(f"👁️ Watcher Dedicado iniciado para: {NOMBRE_AGENTE}")
    
    num_lineas_leidas = 0
    cola_tareas = []
    hash_tareas_historicas = set()

    if os.path.exists(TRACKER_PATH):
        with open(TRACKER_PATH, 'r', encoding='utf-8', errors='replace') as f:
            lineas = [l for l in f.readlines() if l.strip()]
            num_lineas_leidas = len(lineas)
        print("🔒 Candado activado: Histórico ignorado. Esperando instrucciones...\n")

    while True:
        try:
            # ==========================================
            # 1. FASE DE LECTURA Y ENCOLADO INDIVIDUAL
            # ==========================================
            if os.path.exists(TRACKER_PATH):
                with open(TRACKER_PATH, 'r', encoding='utf-8', errors='replace') as f:
                    lineas = [l for l in f.readlines() if l.strip()]
                    
                    if len(lineas) > num_lineas_leidas:
                        nuevas_lineas = lineas[num_lineas_leidas:]
                        
                        for idx, linea in enumerate(nuevas_lineas):
                            mensaje = extraer_instrucciones(linea)
                            if mensaje:
                                numero_linea_absoluta = num_lineas_leidas + idx
                                id_tarea = hash(f"{numero_linea_absoluta}_{mensaje}")
                                
                                if id_tarea not in hash_tareas_historicas:
                                    cola_tareas.append(mensaje)
                                    hash_tareas_historicas.add(id_tarea)
                                    print(f"📥 [{NOMBRE_AGENTE}] Tarea encolada.")
                                    
                        num_lineas_leidas = len(lineas)
                        
                    elif len(lineas) < num_lineas_leidas:
                        num_lineas_leidas = len(lineas)

            # ==========================================
            # 2. FASE DE INYECCIÓN (COLA INDIVIDUAL)
            # ==========================================
            tareas_no_procesadas = []
            candado_disparo = False  # Evita inyectar múltiples tareas en el mismo ciclo de 2s
            
            for mensaje in cola_tareas:
                # Si ya disparamos en este milisegundo, retenemos el resto de la cola
                if candado_disparo:
                    tareas_no_procesadas.append(mensaje)
                    continue

                pane_id, estado = obtener_info_agente()
                
                if not pane_id:
                    print(f"❌ [{NOMBRE_AGENTE}] Agente no encontrado. Se mantendrá en cola.")
                    tareas_no_procesadas.append(mensaje)
                    continue
                    
                if estado not in ["idle", "done"]:
                    print(f"⏳ [{NOMBRE_AGENTE}] Está {estado}. Esperando turno...")
                    tareas_no_procesadas.append(mensaje)
                    continue 

                print(f"\n🚀 [{NOMBRE_AGENTE}] Inyectando tarea...")
                linea_escapada = mensaje.replace('"', '\\"')
                comando = f'herdr pane run {pane_id} "{linea_escapada}"'

                try:
                    subprocess.run(comando, shell=True, check=True)
                    print(f"✅ [{NOMBRE_AGENTE}] Éxito. Tarea despachada.")
                    guardar_historial(mensaje)
                    
                    # Activamos el candado para que las tareas restantes vayan directo a la espera
                    candado_disparo = True 
                    
                except subprocess.CalledProcessError as e:
                    print(f"❌ [{NOMBRE_AGENTE}] Error de inyección. Código: {e.returncode}")
                    tareas_no_procesadas.append(mensaje)

            cola_tareas = tareas_no_procesadas
                                
        except KeyboardInterrupt:
            print(f"\n🛑 Watcher de {NOMBRE_AGENTE} detenido.")
            break
        except Exception as e:
            print(f"⚠️ [{NOMBRE_AGENTE}] Error general: {e}")
            
        time.sleep(2)


if __name__ == "__main__":
    iniciar_watcher()