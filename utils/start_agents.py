# -*- coding: utf-8 -*-
"""
start_agents.py
Despliega la flota completa de 15 agentes de BMAD organizada en 3 pestañas temáticas en Herdr:
  1. Negocio y Producto (6 agentes en grilla 2x3)
  2. Arquitectura e Ingeniería (4 agentes)
  3. Desarrollo y Despliegue (3 agentes)

Aplica estrategia FinOps (modelo y esfuerzo de razonamiento) y sandbox con --add-dir.
"""

import subprocess
import time
import json
import sys
from pathlib import Path

# Prevenir errores de codificación en consolas de Windows (cp1252)
if sys.platform == "win32":
    try:
        sys.stdout.reconfigure(encoding="utf-8", errors="replace")
        sys.stderr.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# ==========================================
# 1. CONFIGURACIÓN ESTRATÉGICA (FinOps / LLMOps)
# ==========================================
WORKSPACE_DIR = Path(__file__).resolve().parent.parent

TABS_CONFIG = {
    "Negocio y Producto": [
        # Fila 1
        {"name": "business-storyteller", "model": "Gemini 3.6 Flash", "effort": "low"},
        {"name": "product-analyst",     "model": "Gemini 3.6 Flash", "effort": "low", "target": "business-storyteller", "direction": "right"},
        {"name": "product-manager",     "model": "Gemini 3.6 Flash", "effort": "low", "target": "product-analyst", "direction": "right"},

        # Fila 2
        {"name": "business-analyst",    "model": "Gemini 3.6 Flash", "effort": "low", "target": "business-storyteller", "direction": "down"},
        {"name": "qa-documental",       "model": "Gemini 3.6 Flash", "effort": "low", "target": "product-analyst", "direction": "down"},
        {"name": "designer-ux",         "model": "Gemini 3.6 Flash", "effort": "low", "target": "product-manager", "direction": "down"},
    ],
    "Arquitectura e Ingeniería": [
        {"name": "solutions-architect", "model": "Gemini 3.6 Flash", "effort": "low"},
        {"name": "data-architect",      "model": "Gemini 3.6 Flash", "effort": "low", "target": "solutions-architect", "direction": "right"},
        {"name": "api-architect",       "model": "Gemini 3.6 Flash", "effort": "low", "target": "solutions-architect", "direction": "down"},
        {"name": "qa-tech",             "model": "Gemini 3.6 Flash", "effort": "low", "target": "data-architect", "direction": "down"},
    ],
    "Desarrollo y Despliegue": [
        # Fase D automatizada: @DEV-BACK y @DEV-FRONT son asimilados por SpecKit.
        # Solo mantenemos a los auditores e infraestructura.
        {"name": "qa-auto",      "model": "Gemini 3.6 Flash", "effort": "low"},
        {"name": "code-review",  "model": "Gemini 3.6 Flash", "effort": "low", "target": "qa-auto", "direction": "right"},
        {"name": "devops",       "model": "Gemini 3.6 Flash", "effort": "low", "target": "code-review", "direction": "right"},
    ]
}

# ==========================================
# 2. FUNCIONES DE APOYO Y HERDR CLI
# ==========================================
def obtener_contexto_actual():
    """Obtiene dinámicamente el ID del panel y tab donde se ejecuta este script."""
    try:
        res = subprocess.run(
            ["herdr", "pane", "current"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        data = json.loads(res.stdout.strip())
        pane = data.get("result", {}).get("pane", {})
        return pane.get("pane_id"), pane.get("tab_id")
    except Exception:
        return None, None

def limpiar_pestanas_previas(tab_actual_id=None):
    """Cierra pestañas con nombres idénticos generadas en ejecuciones previas (salvo la actual)."""
    try:
        res = subprocess.run(
            ["herdr", "tab", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        data = json.loads(res.stdout.strip())
        tabs = data.get("result", {}).get("tabs", [])
        for tab in tabs:
            label = tab.get("label")
            tab_id = tab.get("tab_id")
            if label in TABS_CONFIG and tab_id != tab_actual_id:
                print(f"🧹 Cerrando pestaña previa: '{label}' ({tab_id})...")
                subprocess.run(
                    ["herdr", "tab", "close", tab_id],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                time.sleep(0.5)
    except Exception as e:
        print(f"⚠️ Nota: No se pudo verificar pestañas previas ({e}). Continuando...")

def extraer_ids_tab(salida_cruda):
    """Extrae tab_id y root_pane_id desde la salida JSON de 'herdr tab create'."""
    try:
        data = json.loads(salida_cruda.strip())
        res = data.get("result", {})
        tab_id = res.get("tab", {}).get("tab_id")
        root_pane_id = res.get("root_pane", {}).get("pane_id")
        return tab_id, root_pane_id
    except Exception:
        return None, None

def extraer_id_pane(salida_cruda):
    """Extrae pane_id desde la salida JSON de 'herdr pane split'."""
    try:
        data = json.loads(salida_cruda.strip())
        res = data.get("result", {})
        if "pane" in res and isinstance(res["pane"], dict):
            return res["pane"].get("pane_id")
        if "root_pane" in res and isinstance(res["root_pane"], dict):
            return res["root_pane"].get("pane_id")
    except Exception:
        pass
    return salida_cruda.strip()

def configurar_agente_en_panel(pane_id, nombre_agente, config_agente):
    """Renombra el panel, inicia el agente AGY con sandboxing y asigna modelo/esfuerzo FinOps."""
    modelo_base = config_agente.get("model", "Gemini 3.6 Flash")
    esfuerzo = config_agente.get("effort", "low")
    esfuerzo_cap = esfuerzo.capitalize()

    if f"({esfuerzo_cap})" not in modelo_base:
        modelo_final = f"{modelo_base} ({esfuerzo_cap})"
    else:
        modelo_final = modelo_base

    # 1. Renombrar panel en Herdr
    try:
        subprocess.run(
            ["herdr", "pane", "rename", pane_id, nombre_agente],
            check=True,
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace"
        )
    except Exception:
        pass

    time.sleep(1)

    # 2. Iniciar el agente con agy, inyectando perfil y modelo directamente al arranque
    cmd_start = [
        "herdr", "agent", "start", nombre_agente,
        "--kind", "agy",
        "--pane", pane_id,
        "--", 
        "--dangerously-skip-permissions",
        "--add-dir", str(WORKSPACE_DIR),
        "--model", modelo_final,
        "--agent", f"{nombre_agente}/AGENTS.md" 
    ]
    
    res_start = subprocess.run(
        cmd_start,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if res_start.returncode == 0:
        print(f"      🤖 Agente inicializado con perfil y modelo {modelo_final}.")
    else:
        err = res_start.stderr.strip() or res_start.stdout.strip()
        print(f"      ⚠️ Advertencia al arrancar agente {nombre_agente}: {err}")

    time.sleep(1)

    # 3. Asignar modelo y esfuerzo FinOps
    cmd_model = ["herdr", "pane", "run", pane_id, f"/model {modelo_final}"]
    res_model = subprocess.run(
        cmd_model,
        capture_output=True,
        text=True,
        encoding="utf-8",
        errors="replace"
    )
    if res_model.returncode == 0:
        print(f"      🧠 FinOps: Asignado {modelo_final}")
    else:
        print(f"      ⚠️ No se pudo asignar modelo para {nombre_agente}")

# ==========================================
# 3. ORQUESTACIÓN PRINCIPAL
# ==========================================
def inicializar_flota():
    print("=" * 65)
    print("🚀 DESPLIEGUE MULTI-TAB DE LA FLOTA BMAD EN HERDR")
    print("=" * 65 + "\n")

    current_pane, current_tab = obtener_contexto_actual()
    if current_pane:
        print(f"📍 Contexto de ejecución: Panel {current_pane} (Tab: {current_tab})\n")

    # Limpiar pestañas anteriores idénticas para evitar duplicados
    limpiar_pestanas_previas(current_tab)

    primer_tab_id = None

    for tab_label, agentes in TABS_CONFIG.items():
        total_agentes = len(agentes)
        print(f"\n📂 Creando Pestaña: [{tab_label}] ({total_agentes} agentes)...")

        primer_agente = agentes[0]
        dir_primer_agente = WORKSPACE_DIR / primer_agente["name"]
        dir_primer_agente.mkdir(parents=True, exist_ok=True)

        # 1. Crear la pestaña temática en Herdr
        cmd_tab = [
            "herdr", "tab", "create",
            "--label", tab_label,
            "--cwd", str(dir_primer_agente)
        ]
        try:
            res_tab = subprocess.run(
                cmd_tab,
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True
            )
            tab_id, root_pane_id = extraer_ids_tab(res_tab.stdout)
        except subprocess.CalledProcessError as e:
            err = e.stderr.strip() if e.stderr else e.stdout.strip()
            print(f"   ❌ Error CLI al crear pestaña '{tab_label}': {err}")
            continue

        if not tab_id or not root_pane_id:
            print(f"   ❌ No se pudo extraer tab_id o root_pane_id: {res_tab.stdout.strip()}")
            continue

        if primer_tab_id is None:
            primer_tab_id = tab_id

        print(f"   📑 Pestaña creada: {tab_id} (Panel Raíz: {root_pane_id})")

        # Diccionario para mapear los nombres de agentes a sus respectivos pane_id en la pestaña actual
        tab_panes = {primer_agente["name"]: root_pane_id}

        # 2. Configurar el primer agente en el panel raíz de la pestaña
        print(f"   🪟 [1/{total_agentes}] Configurando {primer_agente['name']}...")
        configurar_agente_en_panel(root_pane_id, primer_agente["name"], primer_agente)
        print(f"      ✅ {primer_agente['name']} listo.")

        prev_pane_id = root_pane_id

        # 3. Configurar los agentes subsiguientes según target y direction
        for idx, agente in enumerate(agentes[1:], start=2):
            nombre = agente["name"]
            target_name = agente.get("target")
            target_pane_id = tab_panes.get(target_name, prev_pane_id)
            direction = agente.get("direction", "right")

            dir_agente = WORKSPACE_DIR / nombre
            dir_agente.mkdir(parents=True, exist_ok=True)

            target_desc = f"'{target_name}'" if target_name else "panel anterior"
            print(f"   🪟 [{idx}/{total_agentes}] Creando panel ({direction} desde {target_desc}) para {nombre}...")

            cmd_split = [
                "herdr", "pane", "split",
                "--pane", target_pane_id,
                "--direction", direction,
                "--cwd", str(dir_agente)
            ]
            try:
                res_split = subprocess.run(
                    cmd_split,
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace",
                    check=True
                )
                time.sleep(1.5)

                pane_id = extraer_id_pane(res_split.stdout)
                if not pane_id:
                    raise ValueError(f"No se pudo extraer pane_id: {res_split.stdout.strip()}")

                tab_panes[nombre] = pane_id
                prev_pane_id = pane_id

                configurar_agente_en_panel(pane_id, nombre, agente)
                print(f"      ✅ {nombre} listo.")

            except subprocess.CalledProcessError as e:
                err_msg = e.stderr.strip() if e.stderr else e.stdout.strip()
                print(f"      ❌ Error CLI al procesar {nombre}: {err_msg}")
            except Exception as e:
                print(f"      ❌ Error inesperado con {nombre}: {str(e)}")

            time.sleep(0.5)

        time.sleep(1)

    # Al finalizar, enfocar la primera pestaña (Negocio y Producto)
    if primer_tab_id:
        print(f"\n🎯 Enfocando pestaña inicial: 'Negocio y Producto' ({primer_tab_id})...")
        try:
            subprocess.run(
                ["herdr", "tab", "focus", primer_tab_id],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace",
                check=True
            )
        except Exception as e:
            print(f"   ⚠️ No se pudo enfocar la pestaña: {e}")

    print("\n" + "=" * 65)
    print("🎉 DESPLIEGUE MULTI-TAB COMPLETADO CON ÉXITO")
    print("   • Tab 1: Negocio y Producto (6 agentes - Grilla 2x3)")
    print("   • Tab 2: Arquitectura e Ingeniería (4 agentes)")
    print("   • Tab 3: Desarrollo y Despliegue (3 agentes de Auditoría e Infraestructura)")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    inicializar_flota()
