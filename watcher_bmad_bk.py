# Orquestador Centralizado Monolítico o Patrón de Bus de Mensajes Central
import time
import os
import json
import random
import subprocess

TRACKER_PATH = r"D:\Paulo\Cursos\DMC\template-bmad\files\tracker_bmad.md"


def guardar_historial(agente_id, instruccion):
    max_reintentos = 5
    for intento in range(max_reintentos):
        try:
            # Intentamos hacer el commit
            subprocess.run("git add .", shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            mensaje_commit = f"BMAD Auto-Save: {agente_id} tarea despachada"
            comando_commit = f'git commit -m "{mensaje_commit}" -m "Instrucción: {instruccion[:50]}..."'
            subprocess.run(comando_commit, shell=True, check=True, stdout=subprocess.DEVNULL, stderr=subprocess.DEVNULL)
            print(f"📦 [Control de Cambios] Commit automático para {agente_id}.")
            break # Si tiene éxito, salimos del bucle
        except subprocess.CalledProcessError:
            # Si falla (probablemente porque otro watcher está haciendo commit), esperamos un momento aleatorio
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
    print(f"👁️ Watcher BMAD (State Machine) iniciado.")
    print(f"📂 Escuchando cambios en: {TRACKER_PATH}")
    
    num_lineas_leidas = 0
    cola_tareas = []
    hash_tareas_historicas = set()
    
    # NUEVO: Diccionario para obligar a Herdr a confirmar que recibió la orden
    esperando_confirmacion = {} 

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
            # 2. FASE DE INYECCIÓN (STATE MACHINE)
            # ==========================================
            tareas_no_procesadas = []
            
            for tarea in cola_tareas:
                agente = tarea['agente']
                mensaje = tarea['mensaje']
                
                pane_id, estado = obtener_info_agente(agente)
                
                if not pane_id:
                    print(f"❌ [Watcher] Agente '{agente}' no encontrado. Se mantendrá en cola.")
                    tareas_no_procesadas.append(tarea)
                    continue
                
                # REGLA DE ORO: Si le inyectamos una tarea, NO le damos otra hasta ver el estado "working"
                if agente in esperando_confirmacion and esperando_confirmacion[agente]:
                    if estado == "working":
                        print(f"🔄 [Watcher] API confirmó recepción. '{agente}' está oficialmente trabajando.")
                        esperando_confirmacion[agente] = False
                    else:
                        print(f"🔄 [Watcher] '{agente}' recibió tarea. Esperando actualización de API Herdr...")
                    
                    tareas_no_procesadas.append(tarea)
                    continue

                if estado not in ["idle", "done"]:
                    print(f"⏳ [Watcher] '{agente}' está {estado}. Esperando turno...")
                    tareas_no_procesadas.append(tarea)
                    continue 

                # Si está libre y NO estamos esperando confirmación, disparamos
                print(f"\n🚀 [Watcher] Inyectando tarea a '{agente}'...")
                linea_escapada = mensaje.replace('"', '\\"')
                comando = f'herdr pane run {pane_id} "{linea_escapada}"'

                try:
                    subprocess.run(comando, shell=True, check=True)
                    print(f"✅ [Watcher] Éxito. Tarea despachada a {agente}.")
                    guardar_historial(agente, mensaje)
                    
                    # ACTIVAMOS EL CANDADO DE CONFIRMACIÓN
                    esperando_confirmacion[agente] = True 
                    
                except subprocess.CalledProcessError as e:
                    print(f"❌ [Watcher] Error de inyección en '{agente}'. Código: {e.returncode}")
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
