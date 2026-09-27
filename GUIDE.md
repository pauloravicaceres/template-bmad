# BMAD Multi-Agent Ecosystem — Guía de Uso

> Esta guía orienta a analistas de negocio, gerentes de producto, arquitectos y desarrolladores para operar el ecosistema multi-agente BMAD y ejecutar flujos completos de definición de software de forma autónoma.

---

## 1. Requisitos Previos

- **Python 3.10+** instalado y disponible en el `PATH`.
- **Herdr CLI** instalado y configurado para la orquestación de terminales virtuales.
- **Entorno de Agentes (Agy CLI)** instalado para la ejecución de los modelos.
- **Git** inicializado en el repositorio para el registro de auto-commits de trazabilidad.
- **Servidores MCP configurados:**
  - `MCP Filesystem` con permisos de lectura/escritura en el proyecto.
  - `MCP Stitch` (opcional para generación de assets visuales).
- **Rutas parametrizadas:** Archivo `config_bmad.json` actualizado según las instrucciones de [`SETUP.md`](./SETUP.md).

---

## 2. Conceptos Clave

### Etapas y Agentes del Ciclo BMAD

| Etapa | Agente Responsable | Acción / Qué Produce |
|---|---|---|
| **Discovery & Storytelling** | `business-storyteller` | Evalúa la idea cruda, ejecuta preguntas de refinamiento si es ambigua y produce `idea_*.md`. |
| **Product Definition** | `product-analyst` | Transforma la narrativa en un Product Brief formal estructurado (`pb_*.md`). Activa pausa HITL. |
| **Management & Planning** | `product-manager` | Tras aprobación HITL, prioriza el alcance del MVP, define la arquitectura modular y el Backlog (`mvp_*.md`). |
| **Specification & BDD** | `business-analyst` | Estrategia Dual-Output: Redacta HU Técnica (Gherkin puro / Spec Kit en `hu_*.md`) y HU para Stakeholders (`HUs-stakeholders/`). |
| **Quality Assurance (Doc)** | `qa-documental` | Audita trazabilidad BDD y coherencia lógica (`qa_*.md`). Al certificar, activa la pausa **SDD Gatekeeper**. |
| **UX & Visual Design** | `designer-ux` | Traduce escenarios Gherkin a wireframes ASCII (`ux_*.md`), audita avance y delega a `@SA:`. |
| **Solutions Architecture** | `solutions-architect` | Formula cuestionario técnico al humano y consolida stack y reglas de gobernanza (`tech_guidelines.md`). |
| **Data Architecture** | `data-architect` | Modela la persistencia: Modelo Entidad-Relación (MER), diccionario y ADRs (`db_*.md`). |
| **API Architecture** | `api-architect` | Diseña contratos de integración REST/GraphQL, payloads y códigos de respuesta (`api_*.md`). |
| **Quality Assurance (Tech)** | `qa-tech` | Audita coherencia cruzada (MER vs API) y compila el documento maestro (`tech-design_*.md`). |
| **Backend Development** | `dev-backend` | Desarrolla la lógica de negocio, endpoints y persistencia del backend según las directrices y contratos del TDD. |
| **Frontend Development** | `dev-frontend` | Construye interfaces de usuario y componentes visuales reactivos según los wireframes y contratos del TDD. |
| **QA Automation** | `qa-auto` | Diseña y ejecuta suites automáticas (unitarias e integración) con cobertura de Criterios de Aceptación (Zero-Tautology). |
| **Code Review & SecOps** | `code-review` | Gatekeeper final: lectura física, verificación de concurrencia, N+1, IDOR, XSS, OWASP y emisión de veredicto formal. |
| **DevOps & SRE** | `devops` | Aprovisiona contenedores multi-stage, compose resiliente con healthchecks y pipelines CI/CD. |

### Términos Fundamentales

| Término | Significado |
|---|---|
| `Token-Passing` | Modelo de orquestación lineal donde los agentes se transfieren el turno de ejecución secuencialmente mediante etiquetas (`@AGENTE:`). |
| `tracker_bmad.md` | Bus de eventos y archivo central de estado donde se registran cronológicamente todas las órdenes y handoffs. |
| `Handoff` | Transición entre dos agentes donde el emisor documenta la ruta del archivo generado para que el receptor lo consuma vía MCP. |
| `Backpressure` | Mecanismo del Watcher para retener tareas encoladas hasta que el agente destinatario se encuentre en estado `idle`. |
| `HITL (Human-in-the-Loop)` | Pausa controlada del flujo donde la continuación hacia el siguiente rol depende de una acción humana (ej. `utils/approve_step.py`). |
| `Bypass Headless` | Enrutamiento condicional donde proyectos sin interfaz gráfica omiten la fase de UX y avanzan directamente de QA a Arquitectura. |
| `Modo Dual (Greenfield / Brownfield)` | Capacidad nativa donde la presencia del archivo `.specify/memory/constitution.md` actúa como interruptor: si existe, todos los agentes subordinan sus entregables al sistema legado; si no, operan como proyecto nuevo sin restricciones. |
| `Cartucho Intercambiable (Pluggable Phase D)` | Principio arquitectónico donde los agentes de construcción y testing operan como interfaces abstractas. El stack (.NET, Java, Python, Go) se cambia modificando únicamente `constitution.md` y las instrucciones locales, manteniendo intacto el orquestador Python. |

---

## 3. Uso Paso a Paso

### Paso 1: Iniciar el Watcher (Orquestador Central)
Abre una terminal y ejecuta el script del orquestador:
```bash
python watcher_bmad.py
```
> *El Watcher compilará automáticamente las definiciones modulares en `AGENTS.md` de cada agente y quedará escuchando el archivo `files/tracker_bmad.md`.*

---

### Paso 2: Desplegar la Grilla de Agentes en Herdr
En tu terminal principal de **Herdr**, ejecuta el inicializador de flota:
```bash
python utils/start_agents.py
```
> *Este script creará la grilla de terminales para los 10 agentes, asignando modelos y permisos de sandbox con `--add-dir`.*

---

### Paso 3: Disparar el Flujo con una Idea de Negocio
Dirígete a la terminal del agente **Business Storyteller** (o envía un prompt directo) con la visión informal del producto:

```text
@BS: Necesitamos desarrollar una plataforma web para que clínicas veterinarias gestionen citas médicas, historial clínico de mascotas y recordatorios automáticos por WhatsApp.
```

---

### Paso 4: Monitoreo Autónomo y Aprobación Obligatoria (HITL)
- **Si la idea es ambigua:** El Business Storyteller formulará 3 a 4 preguntas en su panel. Responde en el mismo chat para que proceda a generar `idea_*.md`.
- **A partir de la delegación:** El Watcher detectará la orden `@PA:` y el flujo avanzará hacia el PA.
- **Pausa Obligatoria HITL (Product Brief):** Al concluir el Product Brief, el PA detiene deliberadamente el flujo emitiendo `@HUMANO:`. La activación de `@PM:` depende de la validación humana:
  1. Revisa el archivo generado en `files/product-analyst/`.
  2. Abre una terminal y ejecuta:
     ```bash
     python utils/approve_step.py
     ```
  3. Selecciona la opción `[2] Product Analyst` y confirma con `s`.
  4. El script inyectará la orden `@PM:` en el tracker y el Watcher despertará automáticamente.
- **Fase Ágil de Especificación (Estrategia Dual-Output):** El PM asignará épicas al BA (`@BA:`), quien redactará simultáneamente:
  - La **HU Técnica (Spec Kit Ready)** en `files/business-analyst/hu_[ID]_[nombre].md`.
  - La **HU para Stakeholders** en `files/business-analyst/HUs-stakeholders/hu_[ID]_[nombre].md`.
  - El BA delega la revisión al QA Documental (`@QA:`).

- **🛑 Intercepción SDD Gatekeeper (Pausa Lógica de Spec Kit):**
  Cuando `@QA:` emite su certificado de aprobación (`aprobado_qa_*.md`), el orquestador **`watcher_bmad.py` intercepta el avance automático hacia UX o Arquitectura y detiene el flujo**. La consola del Watcher mostrará un banner indicando que es el momento del ciclo interactivo de Spec Kit:
  1. Ejecutar en terminal:
     ```bash
     /speckit.specify files/business-analyst/hu_[ID]_[nombre].md
     /speckit.clarify
     /speckit.plan
     /speckit.tasks
     /speckit.analyze
     ```
  2. Una vez validada la especificación contra la constitución técnica con `/speckit.analyze`, abre otra terminal y ejecuta el liberador:
     ```bash
     python utils/approve_step.py
     ```
  3. Selecciona la opción **`[5] Spec Kit (SDD Bridge) -> UX`** (o **`[6] Spec Kit -> SA`** si es un proyecto Headless).
  4. El script despachará el evento al tracker y el Watcher reanudará el enrutamiento hacia la Fase de Arquitectura.

---

### Paso 5: Transición a Fase de Arquitectura y Despacho SDD
1. **Consumo de Artefactos Spec Kit:** `designer-ux`, `solutions-architect`, `data-architect`, `api-architect` y `qa-tech` toman como fuente de la verdad `spec.md`, `plan.md` y `tasks.md`:
   - `designer-ux`: Diseña wireframes ASCII mapeando cada tarea de UI de `tasks.md`.
   - `solutions-architect`: Consolida directrices (`tech_guidelines.md`) enriqueciendo los ADRs de `plan.md`.
   - `data-architect`: Modela la persistencia física (`db_*.md`) alineada a las entidades de `spec.md` y `tasks.md`.
   - `api-architect`: Diseña los contratos REST/GraphQL (`api_*.md`) mapeando los endpoints planificados.
2. **Compilación y Certificación TDD:** `qa-tech` audita de forma cruzada el MER y las APIs contra `tasks.md`, compila el documento maestro `tech-design_*.md` y emite en el tracker la orden `@SPEC-KIT:`.
3. **Gatillo de Implementación Fase D (`/speckit.implement`):**
   - Ejecuta en terminal `/speckit.implement` (o `python utils/approve_step.py` opción `[10]`).
   - Spec Kit despacha en paralelo las tareas a los agentes de la Fase D (`dev-backend`, `dev-frontend`, `devops`), quienes ejecutan comandos de compilación, construcción y pruebas directamente mediante su herramienta de terminal canónica **`execute_command`**.
   - `qa-auto` valida los tests no-tautológicos y `code-review` audita el código fuente antes del despliegue final.

---

## 4. Matriz de Entradas y Salidas

| Agente | Entrada Requerida | Salida Generada | Ubicación de Salida |
|---|---|---|---|
| **BS** | Idea o requerimiento crudo del usuario | `idea_[nombre].md` | `files/business-storyteller/` |
| **PA** | `idea_[nombre].md` | `pb_[nombre].md` (Product Brief) | `files/product-analyst/` |
| **PM** | `pb_[nombre].md` (Post-HITL) | `mvp_[nombre].md` (Plan MVP + Épicas) | `files/product-manager/` |
| **BA** | `mvp_[nombre].md` + `pb_[nombre].md` | `hu_[nombre].md` (Historias BDD) | `files/business-analyst/` |
| **QA** | `hu_[nombre].md` + `pb_[nombre].md` | `aprobado_qa_*.md` / `feedback_qa_*.md` | `files/qa-documental/` |
| **UX** | `hu_[nombre].md` (Aprobada) | `ux_[nombre].md` (Wireframes ASCII) | `files/designer-ux/` |
| **SA** | `pb_*.md` + `mvp_*.md` + (Q&A Humano o `constitution.md`) | `tech_guidelines.md` (Gobernanza) | `files/solutions-architect/` |
| **DA** | `hu_*.md` + `pb_*.md` + Guidelines | `db_[nombre].md` (MER + ADRs) | `files/data-architect/` |
| **API** | `db_*.md` + `hu_*.md` | `api_[nombre].md` (Contratos + ADRs) | `files/api-architect/` |
| **QT** | `db_*.md` + `api_*.md` | `tech-design_[nombre].md` (TDD Maestro) | `files/qa-tech/` |

> *Nota sobre Modo Brownfield: Si existe el archivo `.specify/memory/constitution.md`, todos los agentes de negocio, producto, requerimientos y arquitectura lo consumen de forma complementaria para subordinar sus entregables a dicho entorno.*

---

## 5. Extensibilidad (Inyección Dinámica de Skills)

El ecosistema permite agregar nuevas habilidades (*skills*) a los agentes de forma modular, sin duplicar código en múltiples archivos.

### Cómo crear e inyectar un Skill
1. **Define la ubicación:**
   - **Skill Global:** Si la habilidad será usada por múltiples agentes (ej. `tracker-logger`, `export-pdf`), créala en la raíz: `skills/nombre-skill/SKILL.md`.
   - **Skill Local:** Si es específica de un dominio (ej. `pb-validator`, `hu-validator`), créala dentro del agente: `product-analyst/skills/nombre-skill/SKILL.md`.
2. **Importa el Skill:** En el archivo de instrucciones (`.instructions.md`) del agente, añade la siguiente etiqueta en la línea donde deseas inyectar el contenido:
   ```markdown
   [IMPORT_SKILL: skills/nombre-skill/SKILL.md]
   ```
3. **Recompila:** Reinicia `watcher_bmad.py`. El orquestador leerá la etiqueta, buscará el archivo local o globalmente, e inyectará su contenido en el `AGENTS.md` final del agente.

---

## 6. Solución de Problemas

| Síntoma | Causa Probable | Solución Recomendada |
|---|---|---|
| El Watcher entra en pausa tras el Product Brief | Pausa obligatoria HITL activa | Revisar `files/product-analyst/pb_*.md` y ejecutar `python utils/approve_step.py`. |
| El Watcher indica `Agente no encontrado` | El panel de Herdr no coincide con el nombre esperado | Verificar que `start_agents.py` haya nombrado los paneles correctamente o ejecutar `herdr agent list`. |
| El agente reporta `Access Denied` al leer un archivo | El agente no tiene permisos sobre la ruta raíz del proyecto | Asegurarse de haber arrancado el agente con el flag `--add-dir` en la raíz (manejado automáticamente por `start_agents.py`). |
| Bucle infinito entre BA y QA (Rechazo repetido) | El LLM del BA no logra interpretar el feedback de QA | Intervenir manualmente en la terminal del BA inyectando la corrección puntual y reactivar el Watcher. |
| El Watcher no reacciona a nuevas líneas en el tracker | El archivo `tracker_bmad.md` tiene problemas de codificación o permisos | Guardar el archivo en formato UTF-8 sin BOM o reiniciar el proceso `python watcher_bmad.py`. |
| Faltan archivos `AGENTS.md` en los directorios de los agentes | No se ejecutó el paso de compilación previa | El Watcher los compila automáticamente al iniciar, o se pueden forzar corriendo `python watcher_bmad.py`. |
| El enjambre ignora restricciones del sistema existente | `.specify/memory/constitution.md` no existe o está vacío | Crear `.specify/memory/constitution.md` detallando el stack, datos y reglas preexistentes antes de iniciar el flujo. |
| Se desea alternar entre Greenfield y Brownfield | Gestión del archivo interruptor físico | Para Greenfield: renombrar o borrar `constitution.md`. Para Brownfield: crear o poblar dicho archivo. |
| Se requiere reiniciar el proyecto desde cero | Existen archivos residuales de ejecuciones previas | Ejecutar `python utils/clean_files.py` (opción `T`) y vaciar `files/tracker_bmad.md`. |

---

## 7. Referencias

- **Manual General:** [`README.md`](./README.md)
- **Arquitectura del Sistema:** [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- **Reporte de Auditoría:** [`BMAD_AUDIT_REPORT.md`](./BMAD_AUDIT_REPORT.md)
- **Instanciación en Nueva Ruta:** [`SETUP.md`](./SETUP.md)
- **Preguntas Técnicas y Arquitectónicas:** [`QUESTIONS.md`](./QUESTIONS.md)
- **Manifiesto:** [`manifest.yaml`](./manifest.yaml)
- **Catálogo Backstage:** [`catalog-info.yaml`](./catalog-info.yaml)
