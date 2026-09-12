import time
import os
import subprocess

# ==========================================
# CONFIGURACIÓN DEL ENTORNO
# ==========================================
# Reemplaza con la ruta absoluta real de tu tracker
TRACKER_PATH = r"D:\Paulo\Cursos\DMC\Amely Spa\files\tracker_bmad.md"

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

def procesar_tracker(ultima_linea):
    linea = ultima_linea.strip()
    
    # Mapeo de las etiquetas con el ID exacto del agente en Herdr
    agentes = {
        "@BS:": "business-storyteller",     # Almacena la idea de usuario estructurada para la generación del product brief
        "@PA:": "product-analyst",  # Almacena el product brief y las instrucciones de producto
        "@PM:": "product-manager",  # Almacena el product backlog y las instrucciones de gestión de producto
        "@BA:": "business-analyst",  # Almancena las historias de usuario y las instrucciones de negocio
        "@QA:": "qa-documental",    # Almacenas las historias de usuario aprobadas y los feedbacks de QA
        "@UX:": "designer-ux"   # Almacena las propuestas de diseño (wireframes) y las instrucciones de experiencia de usuario
    }

    for etiqueta, agente_id in agentes.items():
        if linea.startswith(etiqueta):
            print(f"\n🚀 [Watcher] Evento detectado para '{agente_id}'.")
            print(f"   Enviando instrucción: {linea}")
            
            # Cambio clave: Usamos 'prompt' en lugar de 'start'
            # Inyectamos la línea del tracker directamente como el mensaje
            comando = f'herdr agent prompt {agente_id} "{linea}"'
            
            try:
                # 1. El agente ejecuta su trabajo y sobrescribe los archivos
                subprocess.run(comando, shell=True, check=True)
                print(f"✅ [Watcher] Instrucción entregada exitosamente al agente '{agente_id}'.")
                
                # 2. El Watcher congela el historial
                guardar_historial(agente_id, linea)
                
            except subprocess.CalledProcessError as e:
                print(f"❌ [Watcher] Error al contactar al agente '{agente_id}'. Código: {e.returncode}")
            
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
        with open(TRACKER_PATH, 'r', encoding='utf-8') as f:
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
                    
                    with open(TRACKER_PATH, 'r', encoding='utf-8') as f:
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