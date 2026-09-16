# Guía de Instanciación y Configuración para Nuevos Proyectos (BMAD)

Este manual documenta los pasos necesarios para clonar, parametrizar y desplegar el framework `template-bmad` en una nueva ruta o entorno de trabajo, garantizando el aislamiento de datos, la correcta configuración de las herramientas MCP y el flujo orquestado entre los 6 agentes del ciclo de vida BMAD.

---

## 1. Puntos de Contacto (Parametrización Obligatoria)

Al clonar la plantilla a una nueva ubicación en disco (ejemplo: `C:\Proyectos\Nuevo-BMAD`), se deben actualizar los siguientes archivos críticos:

### 1.1. `config_bmad.json` (Diccionario Central de Rutas)
Contiene las rutas absolutas donde los agentes buscarán insumos y guardarán entregables vía MCP Filesystem.
- **Acción:** Reemplazar la ruta raíz base por la del nuevo proyecto en todas las claves.

```json
{
  "routes_bmad": {
    "business-storyteller": "<RUTA_NUEVO_PROYECTO>\\files\\business-storyteller\\",
    "product-analyst": "<RUTA_NUEVO_PROYECTO>\\files\\product-analyst\\",
    "product-manager": "<RUTA_NUEVO_PROYECTO>\\files\\product-manager\\",
    "business-analyst": "<RUTA_NUEVO_PROYECTO>\\files\\business-analyst\\",
    "qa-documental": "<RUTA_NUEVO_PROYECTO>\\files\\qa-documental\\",
    "designer-ux": "<RUTA_NUEVO_PROYECTO>\\files\\designer-ux\\",
    "tracker": "<RUTA_NUEVO_PROYECTO>\\files\\tracker_bmad.md"
  }
}
```

---

### 1.2. Archivo Bus de Mensajes (`files/tracker_bmad.md`)
Es el archivo central de orquestación y sincronización de estado.
- **Acción:** Limpiar el contenido del archivo si contiene eventos o historial del proyecto anterior. Debe quedar completamente vacío.

---

## 2. Estructura de Directorios y Aislamiento de Datos

La estructura del proyecto separa el código fuente/instrucciones del almacenamiento de artefactos generados por los agentes:

```text
<RUTA_NUEVO_PROYECTO>/
├── config_bmad.json                  # Diccionario de rutas del nuevo proyecto
├── watcher_bmad.py                   # Orquestador del ciclo de vida y compilador de agentes (Rutas Dinámicas)
├── README.md                         # Documentación general de arquitectura
├── SETUP.md                          # Guía de configuración para nuevas instancias
│
├── /utils                            # Herramientas de automatización
│   ├── start_agents.py               # Despliega la grilla de terminales herdr (Rutas Dinámicas)
│   ├── clean_files.py                # Limpia los entregables en files/
│   └── delete_agents.py              # Elimina los AGENTS.md auto-compilados
│
├── /business-storyteller             # Definiciones modulares del agente BS
│   ├── /agents                       # business-storyteller.agent.md
│   └── /instructions                 # Reglas satélite y templates
├── /product-analyst                  # Definiciones modulares del agente PA
├── /product-manager                  # Definiciones modulares del agente PM
├── /business-analyst                 # Definiciones modulares del agente BA
│   ├── /agents                       # business-analyst.agent.md (Variables de entorno)
│   └── /instructions                 # Reglas satélite y templates
├── /qa-documental                    # Definiciones modulares del agente QA
├── /designer-ux                      # Definiciones modulares del agente UX
│
└── /files                            # Directorio de entregables (Aislamiento de Datos)
    ├── tracker_bmad.md               # Bus de eventos y cola de orquestación
    ├── /business-storyteller         # Salidas BS: ideas estructuradas (idea_*.md)
    ├── /product-analyst              # Salidas PA: product briefs (pb_*.md)
    ├── /product-manager              # Salidas PM: planes de gestión / MVP (mvp_*.md)
    ├── /business-analyst             # Salidas BA: historias de usuario (hu_*.md)
    ├── /qa-documental                # Salidas QA: reportes de auditoría (qa_*.md)
    └── /designer-ux                  # Salidas UX: especificaciones UI/UX (ux_*.md)
```

> **Nota de Aislamiento:** Al iniciar un nuevo proyecto, todas las subcarpetas dentro de `files/` deben estar completamente vacías para evitar cruce de contexto entre proyectos.

---

## 3. Utilidades de Mantenimiento (`/utils`)

El framework cuenta con scripts auxiliares en `utils/` para agilizar el ciclo de vida:

1. **`python utils/clean_files.py`:**
   - Permite vaciar de forma interactiva las subcarpetas de `files/` (individualmente o todas con `T`), preservando `tracker_bmad.md`.
2. **`python utils/delete_agents.py`:**
   - Elimina los archivos `AGENTS.md` generados por el compilador para forzar una reconstrucción limpia desde las carpetas `agents/` e `instructions/`.
3. **`python utils/start_agents.py`:**
   - Abre y nombra automáticamente los 6 paneles en `herdr`, configura la asignación de modelos y los permisos `--add-dir`. Resuelve dinámicamente el `WORKSPACE_DIR` mediante `Path(__file__)`, por lo que **no requiere edición manual de rutas**.
   - **Asignación de Modelo y Esfuerzo (FinOps / LLMOps):**
     - El modelo asignado a los agentes se puede personalizar editando la variable `modelo_base` (por defecto `"Gemini 3.7 Flash"`).
     - El nivel de esfuerzo de razonamiento se configura en la variable `esfuerzo` (opciones: `"low"`, `"medium"`, `"high"`).
     - *Opcional:* También se pueden sobreescribir estos valores de manera individual por agente dentro del diccionario `AGENTS_CONFIG` agregando las claves `"model"` y `"effort"`.

---

## 4. Checklist de Puesta en Marcha (Paso a Paso)

Sigue esta lista de verificación secuencial para inicializar y levantar el proyecto en una nueva ruta:

- [ ] **1. Clonar/Copiar:** Copiar el directorio `template-bmad` a la nueva ruta deseada.
- [ ] **2. Limpieza de Entregables:** Ejecutar `python utils/clean_files.py` y seleccionar opción `T` para vaciar entregables previos.
- [ ] **3. Limpieza de Compilación previa:** Ejecutar `python utils/delete_agents.py` si existen archivos `AGENTS.md` residuales.
- [ ] **4. Actualizar `config_bmad.json`:** Modificar todas las rutas absolutas para que apunten al nuevo directorio.
- [ ] **5. Limpiar `files/tracker_bmad.md`:** Asegurar que el archivo de tracker esté completamente vacío.
- [ ] **6. Iniciar el Watcher (Compilación y Escucha):**
  - En una terminal, ejecutar el orquestador:
    ```bash
    python watcher_bmad.py
    ```
  - *Nota:* El watcher compilará automáticamente los agentes modulares (`compilar_agentes_modulares()`), generando los archivos `AGENTS.md` unificados para cada agente y quedará escuchando `tracker_bmad.md`.
- [ ] **7. Desplegar los Agentes en `herdr`:**
  - En la terminal principal de `herdr`, ejecutar el script de arranque:
    ```bash
    python utils/start_agents.py
    ```
  - Esto dividirá la pantalla en los paneles correspondientes, asignará los modelos (FinOps) e inicializará cada agente con acceso dinámico a la ruta (`--add-dir`), cargando sus `AGENTS.md` compilados.
- [ ] **8. Verificación:** Confirmar que todos los agentes queden en estado activo/idle en `herdr` y que el watcher reporte que está a la escucha de nuevas instrucciones.
