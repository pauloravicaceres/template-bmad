# Orquestador Centralizado Monolítico (Modelo Secuencial Estricto)
import time
import os
import json
import subprocess
import random
from pathlib import Path

# ==========================================
# RUTAS Y DIRECTORIOS DINÁMICOS
# ==========================================
DIRECTORIO_RAIZ = Path(__file__).resolve().parent
TRACKER_PATH = str(DIRECTORIO_RAIZ / "files" / "tracker_bmad.md")

def guardar_historial(agente_id, instruccion):
    max_reintentos = 5
    for intento in range(max_reintentos):
        try:
            subprocess.run("git add .", shell=True, check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            mensaje_commit = f"BMAD Auto-Save: {agente_id} tarea despachada"
            comando_commit = f'git commit -m "{mensaje_commit}" -m "Instrucción: {instruccion[:50]}..."'
            subprocess.run(comando_commit, shell=True, check=True, cwd=DIRECTORIO_RAIZ, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"📦 [Control de Cambios] Commit automático para {agente_id}.")
            break 
        except subprocess.CalledProcessError:
            espera = random.uniform(0.5, 2.0)
            time.sleep(espera)

def obtener_info_agente(nombre_agente):
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

def extraer_instrucciones(linea):
    agentes = {
        "@BS:": "business-storyteller",
        "@PA:": "product-analyst",
        "@PM:": "product-manager",
        "@BA:": "business-analyst",
        "@QA:": "qa-documental",
        "@UX:": "designer-ux"
    }
    
    tareas = []
    todas_las_etiquetas = list(agentes.keys())
    
    for etiqueta, agente_nombre in agentes.items():
        if etiqueta in linea:
            inicio = linea.find(etiqueta)
            fin = len(linea)
            
            for otra_etiqueta in todas_las_etiquetas:
                if otra_etiqueta != etiqueta:
                    pos_otra = linea.find(otra_etiqueta, inicio + len(etiqueta))
                    if pos_otra != -1 and pos_otra < fin:
                        fin = pos_otra
                        
            mensaje = linea[inicio:fin].strip()
            tareas.append({'agente': agente_nombre, 'mensaje': mensaje})
            
    return tareas

def iniciar_watcher():
    print(f"👁️ Watcher BMAD (Sequential Token-Passing) iniciado.")
    print(f"📂 Escuchando cambios en: {TRACKER_PATH}")
    
    num_lineas_leidas = 0
    cola_tareas = []
    hash_tareas_historicas = set()
    
    if os.path.exists(TRACKER_PATH):
        with open(TRACKER_PATH, 'r', encoding='utf-8', errors='replace') as f:
            lineas = [l for l in f.readlines() if l.strip()]
            num_lineas_leidas = len(lineas)
        print("🔒 Candado activado: Histórico ignorado. Esperando nuevas instrucciones...\n")

    while True:
        try:
            # ==========================================
            # 1. FASE DE LECTURA Y ENCOLADO
            # ==========================================
            if os.path.exists(TRACKER_PATH):
                with open(TRACKER_PATH, 'r', encoding='utf-8', errors='replace') as f:
                    lineas = [l for l in f.readlines() if l.strip()]
                    
                    if len(lineas) > num_lineas_leidas:
                        nuevas_lineas = lineas[num_lineas_leidas:]
                        for idx, linea in enumerate(nuevas_lineas):
                            nuevas_tareas = extraer_instrucciones(linea)
                            numero_linea_absoluta = num_lineas_leidas + idx
                            
                            for tarea in nuevas_tareas:
                                id_tarea = hash(f"{numero_linea_absoluta}_{tarea['agente']}_{tarea['mensaje']}")
                                if id_tarea not in hash_tareas_historicas:
                                    cola_tareas.append(tarea)
                                    hash_tareas_historicas.add(id_tarea)
                                    print(f"📥 [Cola] Tarea encolada para '{tarea['agente']}'.")
                                    
                        num_lineas_leidas = len(lineas)
                    elif len(lineas) < num_lineas_leidas:
                        num_lineas_leidas = len(lineas)
                        
            # ==========================================
            # 2. FASE DE INYECCIÓN (SECUENCIAL PURA)
            # ==========================================
            tareas_no_procesadas = []
            candado_disparo = False  # Garantiza una sola inyección por ciclo
            
            for tarea in cola_tareas:
                if candado_disparo:
                    tareas_no_procesadas.append(tarea)
                    continue

                agente = tarea['agente']
                mensaje = tarea['mensaje']
                
                pane_id, estado = obtener_info_agente(agente)
                
                if not pane_id:
                    print(f"❌ [Watcher] Agente '{agente}' no encontrado.")
                    tareas_no_procesadas.append(tarea)
                    continue
                    
                if estado not in ["idle", "done"]:
                    print(f"⏳ [Watcher] '{agente}' está {estado}. Esperando turno...")
                    tareas_no_procesadas.append(tarea)
                    continue 

                print(f"\n🚀 [Watcher] Inyectando tarea a '{agente}'...")
                linea_escapada = mensaje.replace('"', '\\"')
                comando = f'herdr pane run {pane_id} "{linea_escapada}"'

                try:
                    subprocess.run(comando, shell=True, check=True)
                    print(f"✅ [Watcher] Éxito. Tarea despachada a {agente}.")
                    # guardar_historial(agente, mensaje)
                    
                    # Bloqueamos el resto de la cola hasta el siguiente ciclo de 2s
                    candado_disparo = True
                except subprocess.CalledProcessError as e:
                    print(f"❌ [Watcher] Error de inyección. Código: {e.returncode}")
                    tareas_no_procesadas.append(tarea)

            cola_tareas = tareas_no_procesadas
                                
        except KeyboardInterrupt:
            print("\n🛑 Watcher detenido por el usuario.")
            break
        except Exception as e:
            print(f"⚠️ [Watcher] Error general: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    iniciar_watcher()
