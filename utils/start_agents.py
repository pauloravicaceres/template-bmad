import subprocess
import time
import json
from pathlib import Path

# ==========================================
# 1. CONFIGURACIÓN ESTRATÉGICA (FinOps / LLMOps)
# ==========================================
WORKSPACE_DIR = Path(__file__).resolve().parent


# Motor de Grilla (2 Columnas). 
# El panel actual (donde corre este script) será la esquina superior izquierda.
# AGENTS_CONFIG = {
#     # Fila 1 (La izquierda es el script actual, cortamos a la derecha para iniciar la columna 2)
#     "business-storyteller": {"target": "CURRENT_PANE",         "direction": "right"},
    
#     # Fila 2
#     "product-analyst":      {"target": "CURRENT_PANE",         "direction": "down"},
#     "product-manager":      {"target": "business-storyteller", "direction": "down"},
    
#     # Fila 3
#     "business-analyst":     {"target": "product-analyst",      "direction": "down"},
#     "qa-documental":        {"target": "product-manager",      "direction": "down"},
    
#     # Fila 4 (Columna Izquierda extra para equilibrar a los 6 agentes)
#     "designer-ux":          {"target": "business-analyst",     "direction": "down"}
# }

AGENTS_CONFIG = {
    # Fila 1 (La izquierda es el script actual, cortamos a la derecha para iniciar la columna 2)
    "business-analyst": {"target": "CURRENT_PANE", "direction": "right"},
    
    # Fila 2
    "business-storyteller": {"target": "CURRENT_PANE", "direction": "down"},
    "qa-documental": {"target": "business-analyst", "direction": "down"},
    
    # Fila 3
    "product-analyst": {"target": "business-storyteller", "direction": "down"},
    "designer-ux": {"target": "qa-documental", "direction": "down"},
    
    # Fila 4 (Columna Izquierda extra para equilibrar a los 6 agentes)
    "product-manager": {"target": "product-analyst", "direction": "down"}
}

def obtener_panel_actual():
    """Obtiene dinámicamente el ID del panel donde se está ejecutando este script."""
    res = subprocess.run(["herdr", "pane", "current"], capture_output=True, text=True, check=True)
    try:
        datos_json = json.loads(res.stdout.strip())
        return datos_json.get("result", {}).get("pane", {}).get("pane_id")
    except json.JSONDecodeError:
        return res.stdout.strip()

def inicializar_flota():
    print("🚀 Iniciando motor de grilla multi-agente...\n")
    
    current_pane = obtener_panel_actual()
    if not current_pane:
        print("❌ No se pudo determinar el panel actual. Abortando.")
        return
        
    print(f"📍 Panel Base (Script Python): {current_pane}\n")
    runtime_agents = {}

    for nombre_agente, config in AGENTS_CONFIG.items():
        target_alias = config["target"]
        direccion = config["direction"]
        
        # ---------------------------------------------------------
        # LÓGICA DE CONCATENACIÓN DE MODELO + ESFUERZO
        # ---------------------------------------------------------
        # Extraemos valores o usamos los defaults
        modelo_base = config.get("model", "Gemini 3.7 Flash")
        esfuerzo = config.get("effort", "low")
        
        # Capitalizamos el esfuerzo (low -> Low) para que coincida con la sintaxis de la CLI
        esfuerzo_cap = esfuerzo.capitalize()
        
        # Armamos el string final (ej: "Gemini 3.7 Flash (Low)")
        if f"({esfuerzo_cap})" not in modelo_base:
            modelo_final = f"{modelo_base} ({esfuerzo_cap})"
        else:
            modelo_final = modelo_base
        # ---------------------------------------------------------
        
        target_pane_id = current_pane if target_alias == "CURRENT_PANE" else runtime_agents[target_alias]
        
        dir_agente = WORKSPACE_DIR / nombre_agente
        dir_agente.mkdir(parents=True, exist_ok=True)
        
        print(f"🪟 Configurando: {nombre_agente}...")

        try:
            # 1. Crear el panel
            cmd_split = [
                "herdr", "pane", "split", 
                "--pane", target_pane_id, 
                "--direction", direccion, 
                "--cwd", str(dir_agente)
            ]
            res_split = subprocess.run(cmd_split, capture_output=True, text=True, check=True)
            time.sleep(2) 

            # 2. Extraer el ID
            salida_cruda = res_split.stdout.strip()
            pane_id = None
            try:
                datos_json = json.loads(salida_cruda)
                pane_id = datos_json.get("result", {}).get("pane", {}).get("pane_id")
            except json.JSONDecodeError:
                pane_id = salida_cruda
            
            if not pane_id:
                raise ValueError(f"No se pudo extraer el ID del split: {salida_cruda}")

            runtime_agents[nombre_agente] = pane_id

            # 3. Renombrar el panel en la UI
            try:
                subprocess.run(["herdr", "pane", "rename", pane_id, nombre_agente], check=True, capture_output=True, text=True)
            except subprocess.CalledProcessError:
                try:
                    subprocess.run(["herdr", "pane", "rename", pane_id, "--name", nombre_agente], check=True, capture_output=True, text=True)
                except Exception:
                    pass 
            except Exception:
                pass

            # 4. Iniciar el agente
            cmd_start = [
                "herdr", "agent", "start", nombre_agente, 
                "--kind", "agy", 
                "--pane", pane_id, 
                "--", "--add-dir", str(WORKSPACE_DIR)
            ]
            subprocess.run(cmd_start, check=True, capture_output=True, text=True)
            print(f"   🤖 Agente inicializado en panel {pane_id}.")

            # 5. Inyectar UN SOLO comando con el Modelo y Esfuerzo combinados
            cmd_model = ["herdr", "pane", "run", pane_id, f"/model {modelo_final}"]
            subprocess.run(cmd_model, check=True, capture_output=True, text=True)
            print(f"   🧠 FinOps: Asignado {modelo_final}")

            print(f"   ✅ Listo.\n")

        except subprocess.CalledProcessError as e:
            err_msg = e.stderr.strip() if e.stderr else e.stdout.strip()
            print(f"   ❌ Error CLI al procesar {nombre_agente}. Detalle: {err_msg}\n")
        except Exception as e:
            print(f"   ❌ Error inesperado con {nombre_agente}: {str(e)}\n")
            
        time.sleep(1)

    print("🎉 Despliegue de la flota completado.")

if __name__ == "__main__":
    inicializar_flota()