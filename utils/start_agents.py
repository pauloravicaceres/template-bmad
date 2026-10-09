"""Original public entry point for the provider-neutral BMAD fleet."""
from pathlib import Path
import sys

WORKSPACE_DIR = Path(__file__).resolve().parent.parent
if str(WORKSPACE_DIR) not in sys.path:
    sys.path.insert(0, str(WORKSPACE_DIR))

from bmad_runtime.cli import launcher_main
from bmad_runtime.fleet import TABS_CONFIG
import ux_routing


def agentes_omitidos():
    return ux_routing.agentes_omitidos(WORKSPACE_DIR)


def inicializar_flota():
    return launcher_main(WORKSPACE_DIR)


if __name__ == '__main__':
    raise SystemExit(inicializar_flota())
