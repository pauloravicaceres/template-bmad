"""
Decisión de ruta del diseño UX, independiente del orquestador.

Solo usa la biblioteca estándar: no importa el Watcher, herdr ni ningún framework de agentes. Cualquier
orquestador (el Watcher actual, un grafo de LangChain/LangGraph, un script) puede importarlo y llamar a
`decidir_ruta_ux()` para saber si una HU pasa por el Diseñador UX o va directo al Arquitecto de Soluciones.

Contrato de datos (lo único que el módulo lee):
  - `config_bmad.json` en la raíz del proyecto: claves `project_type` ("ui" | "headless") y `ux_phase` ("auto" | "on" | "off").
  - La HU técnica del BA: línea `- **Requiere interfaz:** Sí | No`.
  - (Opcional) `.specify/feature.json`: para localizar la HU en curso cuando el llamador no la indica.

Prioridad: project_type headless  >  ux_phase  >  campo de la HU  >  diseñar (por defecto).
"""
import json
import re
from pathlib import Path
from typing import NamedTuple, Optional, Union

RutaLike = Union[str, Path]

_PATRON_REQUIERE_INTERFAZ = re.compile(r"Requiere interfaz[^\w\n]*(S[ií]|No)\b", re.IGNORECASE)


class RutaUX(NamedTuple):
    destino: str   # "UX" (se diseña) o "SA" (se omite el diseño y se pasa al arquitecto)
    motivo: str    # explicación legible, apta para el tracker
    omitida: bool  # True si el diseño UX se omite


def hu_desde_feature_json(raiz: RutaLike) -> Optional[Path]:
    """Ruta de la HU del BA que corresponde a la carpeta fijada en .specify/feature.json (o None)."""
    raiz = Path(raiz)
    try:
        feature = json.loads((raiz / ".specify" / "feature.json").read_text(encoding="utf-8"))
    except (OSError, ValueError):
        return None
    nombre = Path(str(feature.get("feature_directory", "")).replace("\\", "/")).name
    ruta = raiz / "documents" / "business-analyst" / f"{nombre}.md"
    return ruta if nombre and ruta.exists() else None


def hu_requiere_interfaz(ruta_hu: RutaLike, raiz: Optional[RutaLike] = None) -> Optional[bool]:
    """True/False según el campo 'Requiere interfaz' (Sí/No) de la HU; None si no está declarado o no se puede leer."""
    try:
        ruta = Path(ruta_hu)
        if not ruta.is_absolute() and raiz is not None:
            ruta = Path(raiz) / ruta
        texto = ruta.read_text(encoding="utf-8", errors="replace")
    except (OSError, TypeError, ValueError):
        return None
    m = _PATRON_REQUIERE_INTERFAZ.search(texto)
    if not m:
        return None
    return m.group(1).lower().startswith("s")


def _leer_config(raiz: Path, config_path: str) -> dict:
    try:
        ruta = raiz / config_path
        if ruta.exists():
            return json.loads(ruta.read_text(encoding="utf-8"))
    except (OSError, ValueError):
        pass
    return {}


def decidir_ruta_ux(raiz: RutaLike, ruta_hu: Optional[RutaLike] = None,
                    config_path: str = "config_bmad.json") -> RutaUX:
    """
    Decide si la HU pasa por el diseño UX.
      ux_phase = "off"  -> nunca diseña (interruptor global)
      ux_phase = "on"   -> siempre diseña
      ux_phase = "auto" -> (por defecto) decide cada HU según su campo 'Requiere interfaz'
    Lee el config en cada llamada: se puede cambiar en caliente, sin reiniciar el orquestador.
    """
    raiz = Path(raiz)
    config = _leer_config(raiz, config_path)
    if str(config.get("project_type", "")).lower() == "headless":
        return RutaUX("SA", "el proyecto es headless", True)
    modo = str(config.get("ux_phase", "auto")).lower()
    if modo == "off":
        return RutaUX("SA", "ux_phase=off en config_bmad.json", True)
    if modo == "on":
        return RutaUX("UX", "ux_phase=on en config_bmad.json", False)
    ruta = ruta_hu or hu_desde_feature_json(raiz)
    requiere = hu_requiere_interfaz(ruta, raiz) if ruta else None
    if requiere is False:
        return RutaUX("SA", "la HU declara 'Requiere interfaz: No'", True)
    if requiere is True:
        return RutaUX("UX", "la HU declara 'Requiere interfaz: Sí'", False)
    return RutaUX("UX", "la HU no declara 'Requiere interfaz'; por defecto se diseña", False)


def agentes_omitidos(raiz: RutaLike, config_path: str = "config_bmad.json") -> set:
    """Agentes cuyo panel/nodo no hace falta levantar según la configuración global (no mira HU concretas)."""
    config = _leer_config(Path(raiz), config_path)
    if str(config.get("ux_phase", "auto")).lower() == "off" or str(config.get("project_type", "")).lower() == "headless":
        return {"designer-ux"}
    return set()
