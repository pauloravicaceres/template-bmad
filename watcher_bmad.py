import time
import os
import json
import subprocess

TRACKER_PATH = r"D:\Paulo\Cursos\DMC\template-bmad\files\tracker_bmad.md"

def guardar_historial(agente_id, instruccion):
    try:
        subprocess.run("git add .", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        mensaje_commit = f"BMAD Auto-Save: {agente_id} tarea despachada"
        comando_commit = f'git commit -m "{mensaje_commit}" -m "Instrucción: {instruccion}"'
        subprocess.run(comando_commit, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
        print(f"📦 [Control de Cambios] Commit automático para {agente_id}.")
    except subprocess.CalledProcessError:
        pass


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
    """Parsea una línea y devuelve una lista de diccionarios con las tareas separadas"""
    agentes = {
        "@BS:": "business-storyteller",
        "@PA:": "product-analyst",
        "@PM:": "product-manager",
        "@BA:": "business-analyst",
        "@QA:": "qa-documental",
        "@UX:": "designer-ux"
        # "@ARQ:": "arquitecto"
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
    print(f"👁️ Watcher BMAD (Queue System) iniciado.")
    print(f"📂 Escuchando cambios en: {TRACKER_PATH}")
    
    num_lineas_leidas = 0
    cola_tareas = []
    hash_tareas_historicas = set()
    tiempo_idle_agentes = {}  # <--- NUEVO: Registro de estabilización

    # Candado de Inicialización: Cuenta las líneas existentes para ignorar el pasado
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
                    
                    # Si el archivo creció, procesamos SOLO las líneas nuevas
                    if len(lineas) > num_lineas_leidas:
                        nuevas_lineas = lineas[num_lineas_leidas:]
                        
                        # Usamos enumerate para saber en qué línea exacta estamos
                        for idx, linea in enumerate(nuevas_lineas):
                            nuevas_tareas = extraer_instrucciones(linea)
                            numero_linea_absoluta = num_lineas_leidas + idx
                            
                            for tarea in nuevas_tareas:
                                # Inyectamos el número de línea en el hash para evitar falsos duplicados
                                id_tarea = hash(f"{numero_linea_absoluta}_{tarea['agente']}_{tarea['mensaje']}")
                                
                                if id_tarea not in hash_tareas_historicas:
                                    cola_tareas.append(tarea)
                                    hash_tareas_historicas.add(id_tarea)
                                    print(f"📥 [Cola] Tarea encolada para '{tarea['agente']}'.")
                                    
                        num_lineas_leidas = len(lineas)
                        
                    # Protección por si se borran líneas manualmente del archivo
                    elif len(lineas) < num_lineas_leidas:
                        num_lineas_leidas = len(lineas)

            # ==========================================
            # 2. FASE DE INYECCIÓN (BACKPRESSURE + DEBOUNCER)
            # ==========================================
            tareas_no_procesadas = []
            agentes_despachados_hoy = set()
            
            for tarea in cola_tareas:
                agente = tarea['agente']
                mensaje = tarea['mensaje']
                
                # Candado de doble despacho simultáneo
                if agente in agentes_despachados_hoy:
                    tareas_no_procesadas.append(tarea)
                    continue
                
                pane_id, estado = obtener_info_agente(agente)
                
                if not pane_id:
                    print(f"❌ [Watcher] Agente '{agente}' no encontrado. Se mantendrá en cola.")
                    tareas_no_procesadas.append(tarea)
                    continue
                    
                if estado != "idle":
                    print(f"⏳ [Watcher] '{agente}' está {estado}. Esperando turno...")
                    # Si el agente parpadeó a working, fue un falso positivo. Reseteamos su reloj.
                    if agente in tiempo_idle_agentes:
                        del tiempo_idle_agentes[agente]
                    tareas_no_procesadas.append(tarea)
                    continue 

                # --- INICIO DEL DEBOUNCER (Filtro Anti-Parpadeo) ---
                if agente not in tiempo_idle_agentes:
                    # Inicia el cronómetro de 15 segundos
                    tiempo_idle_agentes[agente] = time.time()
                    print(f"⏱️ [Watcher] '{agente}' parece idle. Verificando estabilización (15s)...")
                    tareas_no_procesadas.append(tarea)
                    continue
                else:
                    tiempo_transcurrido = time.time() - tiempo_idle_agentes[agente]
                    if tiempo_transcurrido < 15:
                        # Sigue esperando en silencio hasta cumplir el tiempo
                        tareas_no_procesadas.append(tarea)
                        continue
                # --- FIN DEL DEBOUNCER ---

                # Si el código llega aquí, el agente superó la prueba de 15s ininterrumpidos en idle.
                print(f"\n🚀 [Watcher] Inyectando tarea a '{agente}'...")
                linea_escapada = mensaje.replace('"', '\\"')
                comando = f'herdr pane run {pane_id} "{linea_escapada}"'

                try:
                    subprocess.run(comando, shell=True, check=True)
                    print(f"✅ [Watcher] Éxito. Tarea despachada a {agente}.")
                    guardar_historial(agente, mensaje)
                    
                    agentes_despachados_hoy.add(agente)
                    del tiempo_idle_agentes[agente]  # Limpiamos el contador tras éxito
                    
                except subprocess.CalledProcessError as e:
                    print(f"❌ [Watcher] Error de inyección en '{agente}'. Código: {e.returncode}")
                    tareas_no_procesadas.append(tarea)

            # Sobrescribimos la cola
            cola_tareas = tareas_no_procesadas
                                
        except KeyboardInterrupt:
            print("\n🛑 Watcher detenido por el usuario.")
            break
        except Exception as e:
            print(f"⚠️ [Watcher] Error general: {e}")
            
        time.sleep(2)

if __name__ == "__main__":
    iniciar_watcher()