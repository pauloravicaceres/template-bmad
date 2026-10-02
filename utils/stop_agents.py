# -*- coding: utf-8 -*-
"""
stop_agents.py
Detiene y cierra automáticamente todas las pestañas y paneles de la flota BMAD en Herdr:
  1. Tab "Negocio y Producto"
  2. Tab "Arquitectura e Ingeniería"
  3. Tab "Desarrollo y Despliegue"
  4. Paneles individuales remanentes con agentes BMAD activos.

Protege de forma inteligente el panel/tab actual donde se ejecuta el script.
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
# 1. CONSTANTES DE LA FLOTA BMAD
# ==========================================
TARGET_TABS = [
    "Negocio y Producto",
    "Arquitectura e Ingeniería",
    "Desarrollo y Despliegue"
]

BMAD_AGENTS = [
    "business-storyteller",
    "product-analyst",
    "product-manager",
    "business-analyst",
    "qa-documental",
    "designer-ux",
    "solutions-architect",
    "data-architect",
    "api-architect",
    "qa-tech",
    "dev-backend",
    "dev-frontend",
    "qa-auto",
    "code-review",
    "devops"
]

# ==========================================
# 2. FUNCIONES DE APOYO Y HERDR CLI
# ==========================================
def obtener_contexto_actual():
    """Obtiene dinámicamente el pane_id y tab_id donde se está ejecutando este script."""
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

def cerrar_pestanas(current_tab_id=None):
    """Cierra las pestañas principales de la flota BMAD en Herdr."""
    tabs_cerradas = 0
    pestana_actual_afectada = False

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

            if label in TARGET_TABS:
                if tab_id == current_tab_id:
                    pestana_actual_afectada = True
                    print(f"   ⚠️ Pestaña activa actual detectada: '{label}' ({tab_id}). Se protegerá el panel de ejecución.")
                    continue

                print(f"   🛑 Cerrando pestaña: [{label}] (ID: {tab_id})...")
                res_close = subprocess.run(
                    ["herdr", "tab", "close", tab_id],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                if res_close.returncode == 0:
                    tabs_cerradas += 1
                    print(f"      ✅ Pestaña '{label}' cerrada exitosamente.")
                else:
                    err = res_close.stderr.strip() or res_close.stdout.strip()
                    print(f"      ⚠️ No se pudo cerrar '{label}': {err}")
                time.sleep(0.3)

    except Exception as e:
        print(f"   ❌ Error al consultar o cerrar pestañas: {e}")

    return tabs_cerradas, pestana_actual_afectada

def cerrar_paneles_remanentes(current_pane_id=None):
    """Cierra paneles individuales que ejecuten agentes BMAD fuera de las pestañas cerradas."""
    paneles_cerrados = 0
    try:
        res = subprocess.run(
            ["herdr", "agent", "list"],
            capture_output=True,
            text=True,
            encoding="utf-8",
            errors="replace",
            check=True
        )
        data = json.loads(res.stdout.strip())
        agentes = data.get("result", {}).get("agents", [])

        for agente in agentes:
            nombre = agente.get("name")
            pane_id = agente.get("pane_id")

            if nombre in BMAD_AGENTS:
                if pane_id == current_pane_id:
                    print(f"   ⚠️ Panel actual '{nombre}' ({pane_id}) omitido para proteger la consola activa.")
                    continue

                print(f"   🛑 Cerrando panel remanente del agente '{nombre}' ({pane_id})...")
                res_close = subprocess.run(
                    ["herdr", "pane", "close", pane_id],
                    capture_output=True,
                    text=True,
                    encoding="utf-8",
                    errors="replace"
                )
                if res_close.returncode == 0:
                    paneles_cerrados += 1
                    print(f"      ✅ Panel {pane_id} ({nombre}) cerrado.")
                time.sleep(0.2)

    except Exception as e:
        print(f"   ❌ Error al consultar agentes remanentes: {e}")

    return paneles_cerrados

def enfocar_tab_control():
    """Enfoca la primera pestaña disponible restante (ej. Tab 1 de control/terminal)."""
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
        if tabs:
            primera_tab_id = tabs[0].get("tab_id")
            primera_tab_label = tabs[0].get("label", "Control")
            print(f"\n🎯 Enfocando pestaña de control: '{primera_tab_label}' ({primera_tab_id})...")
            subprocess.run(
                ["herdr", "tab", "focus", primera_tab_id],
                capture_output=True,
                text=True,
                encoding="utf-8",
                errors="replace"
            )
    except Exception:
        pass

# ==========================================
# 3. ORQUESTACIÓN PRINCIPAL
# ==========================================
def detener_flota():
    print("=" * 65)
    print("🛑 APAGADO Y LIMPIEZA DE FLOTA BMAD EN HERDR")
    print("=" * 65 + "\n")

    current_pane, current_tab = obtener_contexto_actual()
    if current_pane:
        print(f"📍 Contexto de ejecución: Panel {current_pane} (Tab: {current_tab})\n")

    print("📂 Fase 1: Cerrando pestañas temáticas BMAD...")
    tabs_cerradas, tab_actual_afectada = cerrar_pestanas(current_tab)

    print("\n🪟 Fase 2: Verificando paneles/agentes individuales remanentes...")
    paneles_cerrados = cerrar_paneles_remanentes(current_pane)

    # Si se cerraron pestañas y no estamos en la pestaña objetivo, enfocar la pestaña disponible
    enfocar_tab_control()

    print("\n" + "=" * 65)
    print("🎉 APAGADO DE FLOTA COMPLETADO")
    print(f"   • Pestañas temáticas cerradas: {tabs_cerradas}")
    print(f"   • Paneles individuales cerrados: {paneles_cerrados}")
    if tab_actual_afectada:
        print("   ℹ️ Nota: La pestaña actual donde corrió el script fue preservada.")
    print("=" * 65 + "\n")

if __name__ == "__main__":
    detener_flota()
