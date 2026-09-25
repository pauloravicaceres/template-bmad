# Guía de Instanciación, Parametrización y Despliegue (BMAD)

Este manual documenta el procedimiento oficial para inicializar, parametrizar y desplegar una nueva instancia del framework **BMAD** (Business, Management, Architecture & Development). Garantiza el aislamiento físico de datos, la configuración determinista de rutas para herramientas MCP y el flujo orquestado a través del roster oficial de agentes.

---

## 1. Principios Fundamentales del Framework

Antes de inicializar un entorno, ten presentes las reglas de arquitectura:

1. **El Tracker como Único Bus de Comunicación:** Los agentes nunca se comunican directamente. Todo intercambio de instrucciones y artefactos ocurre registrando eventos en `files/tracker_bmad.md`.
2. **Plantillas Deterministas:** Ningún agente inventa la estructura de sus salidas; todos los artefactos se generan respetando sus plantillas `.instructions.md`.
3. **Lógica de Bypass Headless vs UI:**
   - **Proyectos con UI:** Transitan el pipeline completo: `PA -> PM -> BA -> QA -> UX -> SA -> DA -> API -> QT`.
   - **Proyectos Headless (ETL, SSIS, APIs puras):** Saltan dinámicamente la etapa de diseño UX: `PA -> PM -> BA -> QA -> SA -> DA -> QT`.
4. **Pausa Obligatoria Human-in-the-Loop (HITL):** Al finalizar el Product Brief, el flujo entra en pausa obligatoria (`@HUMANO:`). El inicio del PM depende formalmente de la ejecución de `python utils/approve_step.py`.
5. **Estrategia Dual Greenfield / Brownfield:** El framework es completamente agnóstico y soporta tanto proyectos nuevos desde cero como la subordinación a sistemas preexistentes mediante el interruptor físico opcional `files/context/legacy_ecosystem.md`.

---

## 2. Inicialización Automatizada con `init_bmad.py`

El framework cuenta con el script oficial [`init_bmad.py`](./init_bmad.py) en la raíz del proyecto para automatizar el aprovisionamiento de un nuevo proyecto en un solo paso:

```bash
python init_bmad.py "Nombre de Mi Nuevo Proyecto"
```

### Qué realiza automáticamente este script:
1. **Scaffolding de Almacenamiento:** Crea todas las carpetas dentro de `files/` para el roster completo de agentes:
   - `files/context/` *(Opcional: aloja `legacy_ecosystem.md` para proyectos Brownfield)*
   - `files/business-storyteller/`
   - `files/product-analyst/`
   - `files/product-manager/`
   - `files/business-analyst/`
   - `files/qa-documental/`
   - `files/designer-ux/`
   - `files/solutions-architect/`
   - `files/data-architect/`
   - `files/api-architect/`
   - `files/qa-tech/`
2. **Generación del Diccionario de Rutas (`config_bmad.json`):** Construye el archivo de configuración con rutas absolutas canónicas adaptadas al directorio actual.
3. **Reseteo Limpio del Tracker:** Inicializa `files/tracker_bmad.md` como un archivo totalmente vacío y limpio, asegurando que no existan instrucciones residuales que confundan al orquestador.

---

## 3. Puntos de Contacto Manuales (Si se parametriza sin `init_bmad.py`)

Si optas por clonar y configurar manualmente sin ejecutar `init_bmad.py`, debes actualizar:

### 3.1. `config_bmad.json` (Diccionario Central de Rutas)
Reemplaza las rutas base por las correspondientes a tu nueva ubicación:

```json
{
  "project_name": "Nuevo-Proyecto",
  "created_at": "2026-09-23 12:00:00",
  "tracker": "D:\\Ruta\\Al\\Proyecto\\files\\tracker_bmad.md",
  "context": "D:\\Ruta\\Al\\Proyecto\\files\\context\\legacy_ecosystem.md",
  "routes_bmad": {
    "business-storyteller": "D:\\Ruta\\Al\\Proyecto\\files\\business-storyteller\\",
    "product-analyst": "D:\\Ruta\\Al\\Proyecto\\files\\product-analyst\\",
    "product-manager": "D:\\Ruta\\Al\\Proyecto\\files\\product-manager\\",
    "business-analyst": "D:\\Ruta\\Al\\Proyecto\\files\\business-analyst\\",
    "qa-documental": "D:\\Ruta\\Al\\Proyecto\\files\\qa-documental\\",
    "designer-ux": "D:\\Ruta\\Al\\Proyecto\\files\\designer-ux\\",
    "solutions-architect": "D:\\Ruta\\Al\\Proyecto\\files\\solutions-architect\\",
    "data-architect": "D:\\Ruta\\Al\\Proyecto\\files\\data-architect\\",
    "api-architect": "D:\\Ruta\\Al\\Proyecto\\files\\api-architect\\",
    "qa-tech": "D:\\Ruta\\Al\\Proyecto\\files\\qa-tech\\"
  }
}
```

> **Parámetro `"context"` (Opcional para Brownfield):**
> Apunta al archivo `files/context/legacy_ecosystem.md`. Si el archivo existe físicamente y contiene directrices de sistemas preexistentes, los agentes operarán en modo subordinado (Brownfield). Si el archivo no existe o se elimina, el ecosistema corre en modo Greenfield estándar sin restricciones ni fallos.

### 3.2. Vaciado del Bus de Mensajes (`files/tracker_bmad.md`)
Asegura que el archivo exista físicamente pero su contenido sea una cadena vacía (0 bytes) antes de encender el Watcher.

---

## 4. Estructura Completa del Directorio

```text
/template-bmad
├── config_bmad.json                  # Diccionario de rutas absolutas para MCP
├── watcher_bmad.py                   # Orquestador del ciclo de vida y compilador modular
├── init_bmad.py                      # Scaffolding automatizado para nuevas instancias
├── README.md                         # Portada principal y arquitectura del framework
├── ARCHITECTURE.md                   # Diagramas técnicos detallados y topología
├── GUIDE.md                          # Guía operativa de usuario y solución de incidentes
├── SETUP.md                          # Manual de instanciación y puesta en marcha
├── BMAD_AUDIT_REPORT.md              # Reporte de certificación de salud arquitectónica
│
├── /skills                           # Repositorio global de habilidades inyectables
│   ├── /tracker-logger               # Habilidad canónica de anexión segura al tracker
│   ├── /export-pdf                   # Exportador determinista a PDF
│   └── /git-commit                   # Autoguardado y control de versiones
│
├── /utils                            # Scripts de mantenimiento y control
│   ├── start_agents.py               # Despliega la flota completa en paneles Herdr
│   ├── approve_step.py               # Gateway de aprobación humana (HITL)
│   ├── clean_files.py                # Limpiador interactivo de entregables en files/
│   └── delete_agents.py              # Limpiador de archivos AGENTS.md auto-ensamblados
│
├── /business-storyteller             # Agente BS: Discovery y narrativa de negocio
├── /product-analyst                  # Agente PA: Product Brief (PRD de 8 secciones)
│   └── /skills                       # Skills locales (pb-validator)
├── /product-manager                  # Agente PM: Backlog y priorización de Ruta Crítica
├── /business-analyst                 # Agente BA: Historias de Usuario con BDD Gherkin
│   └── /skills                       # Skills locales (hu-validator)
├── /qa-documental                    # Agente QA: Control de calidad documental y Bypass
├── /designer-ux                      # Agente UX: Wireframes ASCII y auditoría de MVP
├── /solutions-architect              # Agente SA: Stack tecnológico y gobernanza técnica
├── /data-architect                   # Agente DA: Modelo Entidad-Relación y ADRs de datos
├── /api-architect                    # Agente API: Contratos de integración REST/GraphQL
├── /qa-tech                          # Agente QT: Auditoría cruzada y compilación del TDD
│
└── /files                            # Aislamiento físico de entregables generados
    ├── tracker_bmad.md               # Único bus de datos y cola de tareas
    ├── /context                      # Ingestión de ecosistema preexistente (Brownfield)
    │   └── legacy_ecosystem.md       # Interruptor físico opcional con directrices legadas
    └── */                            # Carpetas individuales por rol
```

---

## 5. Scripts de Utilidad y Mantenimiento (`/utils`)

- **`python utils/clean_files.py`:** Permite vaciar interactivamente los entregables de una o todas las subcarpetas de `files/` (opción `T`), manteniendo intacta la estructura y el `tracker_bmad.md`.
- **`python utils/delete_agents.py`:** Elimina los archivos `AGENTS.md` compilados para forzar una regeneración limpia desde las carpetas `agents/` e `instructions/`.
- **`python utils/start_agents.py`:** Abre la grilla completa en **Herdr**, divide los paneles, configura permisos de sandbox (`--add-dir`) y aplica la estrategia FinOps de modelos y esfuerzos de razonamiento.
- **`python utils/approve_step.py`:** Administra las pausas de aprobación obligatoria (HITL). Permite abrir el artefacto producido, revisarlo en el sistema operativo y emitir la orden formal correspondiente (`@PM:`, `@DEV:`, etc.) en el tracker.

---

## 6. Checklist de Puesta en Marcha (Paso a Paso)

Para poner en marcha un nuevo proyecto desde cero:

- [ ] **Paso 1: Clonar plantilla:** Copiar el repositorio a la carpeta de destino.
- [ ] **Paso 2: Inicializar entorno:** Ejecutar `python init_bmad.py "Nombre del Proyecto"` para crear las carpetas de `files/`, generar `config_bmad.json` y vaciar `tracker_bmad.md`.
- [ ] **Paso 2.1 (Opcional - Proyectos Brownfield):** Si la solución debe coexistir con un sistema o base de datos preexistente, crear `files/context/legacy_ecosystem.md` y documentar la arquitectura, motores relacionales, protocolos y restricciones heredadas. Para proyectos 100% nuevos (Greenfield), omitir este paso asegurando que dicho archivo no exista.
- [ ] **Paso 3: Arrancar el Orquestador:**
  ```bash
  python watcher_bmad.py
  ```
  *(El Watcher auto-ensamblará los archivos `AGENTS.md` inyectando las skills y quedará escuchando el tracker).*
- [ ] **Paso 4: Levantar la flota de agentes en Herdr:**
  En tu terminal principal de Herdr, ejecutar:
  ```bash
  python utils/start_agents.py
  ```
- [ ] **Paso 5: Disparar el requerimiento:** Inyectar la primera orden en la terminal de `@BS:` o directamente en el tracker.
