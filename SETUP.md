# 🚀 Guía de Instanciación, Configuración y Despliegue (BMAD v2.0)

Este manual documenta el paso a paso detallado para clonar, parametrizar y encender una nueva instancia del framework **BMAD** (Business, Management, Architecture & Development). 

Sigue estos pasos en orden para garantizar que el orquestador, las rutas de los agentes y la integración con **Git** e **Integración SDD** funcionen correctamente en tu nueva carpeta.

---

## 🛑 PRERREQUISITOS DEL SISTEMA

Antes de iniciar un proyecto, asegúrate de tener instalado en tu máquina:
- **Python 3.10+** (Para ejecutar el orquestador y los scripts).
- **Git** (Obligatorio para que los agentes hagan *Commits Atómicos* y el orquestador gestione ramas).
- **GitHub Spec Kit CLI** (Obligatorio para la transición automática entre negocio y arquitectura).

---

## 🛠️ FASE 1: Preparación del Repositorio

### Paso 1: Clonar la plantilla con `clone_template.py`
Para instanciar un proyecto limpio sin arrastrar configuraciones legacy, basura, o archivos temporales de ejecuciones anteriores, utiliza el script automatizado de clonado.

En tu terminal (estando dentro de la carpeta `template-bmad`), ejecuta:
```bash
python utils/clone_template.py "D:\ruta\a\mi-nuevo-proyecto"
```
> **¿Qué hace este script?** Utiliza un enfoque de "Lista Blanca" para copiar exclusivamente las 15 carpetas de agentes, el motor orquestador (`watcher_bmad.py`), las herramientas (`utils/`, `skills/`), y la infraestructura de Spec Kit (`.specify/`). Ignorará automáticamente la carpeta `.git/`, la carpeta `files/` y cualquier archivo Markdown residual.

### Paso 2: Inicializar Git y hacer el commit base
Una vez que el script copie los archivos, ve a tu nueva carpeta y crea un repositorio limpio. El orquestador necesita una rama `main` de donde partir para crear ramas de funcionalidad.
```bash
cd /ruta/a/mi-nuevo-proyecto
git init
git add .
git commit -m "chore: inicialización del ecosistema BMAD v2.0"
```

---

## ⚙️ FASE 2: Scaffolding y Configuración (Automática)

En lugar de reconfigurar rutas absolutas manualmente, el framework incluye un script automatizado que crea la estructura de directorios, vacía el bus de mensajes y mapea las rutas absolutas para tu máquina actual.

### Paso 3: Ejecutar `init_bmad.py`
En la raíz de tu nuevo proyecto, ejecuta:
```bash
python init_bmad.py "Nombre de Mi Sistema"
```
**¿Qué hace este script?**
- Crea las carpetas de salida en `/files/` para los 15 agentes.
- Vacía el archivo `files/tracker_bmad.md` dejándolo en 0 bytes.
- Actualiza el archivo `config_bmad.json` con las rutas absolutas correctas de tu disco duro.
- Crea el directorio `.specify/memory/` para tu Constitución Técnica.

### Paso 4: Definir la Topología del Proyecto (`config_bmad.json`)
Abre el archivo `config_bmad.json` generado en la raíz de tu proyecto. Verás una clave llamada `"project_type"`.
Debes configurarla dependiendo de la naturaleza de tu software:
- `"project_type": "ui"` *(Por defecto)*: Transita por el diseñador UX (`@UX:`). Usado para Web, Apps Móviles, Dashboards.
- `"project_type": "headless"`: Salta el diseño visual y pasa directo al Arquitecto de Soluciones (`@SA:`). Usado para APIs puras, ETLs, CRONs y Workers.

### Paso 5: (Opcional) Proyectos Preexistentes (Brownfield)
Si tu proyecto no es nuevo y debe conectarse a bases de datos heredadas o sistemas legacy, debes documentar esas restricciones.
1. Crea o edita el archivo: `.specify/memory/constitution.md`
2. Escribe allí todas las reglas inmutables de tu infraestructura (ej. "Solo usar Oracle DB", "Prohibido C# 12, usar Java 17").
*(Si el proyecto es 100% nuevo, puedes dejar este archivo vacío).*

---

## ⚡ FASE 3: Despliegue de la Flota

Con el repositorio listo y las rutas configuradas, es hora de encender el motor de IA.

### Paso 6: Arrancar el Orquestador (Watcher)
El orquestador de BMAD ya no exige selección manual de ramas. Gracias al nuevo estándar **GitOps Feature Branching**, el orquestador gestiona la creación y fusión de ramas de manera 100% autónoma.

Abre una terminal en la raíz de tu proyecto y ejecuta:
```bash
python watcher_bmad.py
```
*(El Watcher compilará las skills en `AGENTS.md`, realizará State Hydration para recuperar operaciones inconclusas, y quedará escuchando indefinidamente. Las ramas aisladas `feat/HU_...` se crearán automáticamente durante el ciclo de vida del tracker).*

### Paso 7: Levantar la Interfaz de Agentes (Herdr)
Abre una **segunda terminal** en la raíz del proyecto. Aquí encenderemos a los 15 agentes divididos en 3 pestañas temáticas.
```bash
python utils/start_agents.py
```
*(Verás cómo los paneles se abren y los agentes quedan a la espera).*

---

## 🎯 FASE 4: Iniciar el Desarrollo

¡Tu ecosistema está vivo! 

Para empezar a crear software, dirígete al archivo `files/tracker_bmad.md` y escribe tu idea inicial etiquetando al analista de negocio:

```markdown
@BS: Necesitamos construir un panel administrativo para recursos humanos que permita gestionar vacaciones, subir nóminas en PDF y aprobar solicitudes con flujos de varios niveles.
```

El orquestador detectará tu mensaje, despertará al Business Storyteller y comenzará la cadena de valor secuencial de BMAD.

---

### 🧯 Comandos de Utilidad Diaria (`/utils`)

- `python utils/approve_step.py`: Úsalo cuando el framework te etiquete (`@HUMANO:`) pidiendo aprobación para transicionar de fase (HITL) o si ocurre una ambigüedad en el Spec-Driven Development.
- `python utils/stop_agents.py`: Ejecútalo cuando termines tu día de trabajo para cerrar limpiamente todos los agentes sin dejar procesos colgando en la terminal.
- `python utils/clean_files.py`: Herramienta de mantenimiento para vaciar los entregables de `/files/` interactivamente si deseas purgar pruebas y volver a empezar.


---

## 🛑 Regla de Oro: Principio de Vertical Slicing Estricto

El ecosistema BMAD v2.0 opera bajo un modelo de **Vertical Slicing Estricto** para garantizar la salud del State Ledger y evitar divergencias arquitectónicas.

*   **Prohibición de Desarrollo Horizontal:** Queda estrictamente prohibido abrir o diseñar múltiples Historias de Usuario (HUs) a la vez. No se puede avanzar al diseño de una nueva característica si la anterior no ha cerrado su ciclo.
*   **Ciclo de Vida de Rebanada Vertical:** Toda HU debe atravesar el ciclo completo antes de iniciar la siguiente: `PM -> BA -> QA -> UX -> SA -> (Fases Técnicas) -> QT -> Retorno a PM`.
*   **Regla de Ramas GitOps:** Queda terminantemente prohibido que el `@PM` inicie una nueva historia y emita un `GITOPS-BRANCH-CREATE` si la historia anterior no ha sido debidamente compilada y fusionada en el código base principal por el `@QT` mediante `GITOPS-MERGE-CLOSE`.
