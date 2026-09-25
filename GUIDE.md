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
| **Specification & BDD** | `business-analyst` | Redacta Historias de Usuario atómicas con criterios de aceptación en sintaxis Gherkin (`hu_*.md`). |
| **Quality Assurance (Doc)** | `qa-documental` | Audita trazabilidad, *sad paths* y coherencia lógica (`qa_*.md`). Gestiona bypass Headless vs UI. |
| **UX & Visual Design** | `designer-ux` | Traduce escenarios Gherkin a wireframes ASCII (`ux_*.md`), audita avance y delega a `@SA:`. |
| **Solutions Architecture** | `solutions-architect` | Formula cuestionario técnico al humano y consolida stack y reglas de gobernanza (`tech_guidelines.md`). |
| **Data Architecture** | `data-architect` | Modela la persistencia: Modelo Entidad-Relación (MER), diccionario y ADRs (`db_*.md`). |
| **API Architecture** | `api-architect` | Diseña contratos de integración REST/GraphQL, payloads y códigos de respuesta (`api_*.md`). |
| **Quality Assurance (Tech)** | `qa-tech` | Audita coherencia cruzada (MER vs API) y compila el documento maestro (`tech-design_*.md`). |

### Términos Fundamentales

| Término | Significado |
|---|---|
| `Token-Passing` | Modelo de orquestación lineal donde los agentes se transfieren el turno de ejecución secuencialmente mediante etiquetas (`@AGENTE:`). |
| `tracker_bmad.md` | Bus de eventos y archivo central de estado donde se registran cronológicamente todas las órdenes y handoffs. |
| `Handoff` | Transición entre dos agentes donde el emisor documenta la ruta del archivo generado para que el receptor lo consuma vía MCP. |
| `Backpressure` | Mecanismo del Watcher para retener tareas encoladas hasta que el agente destinatario se encuentre en estado `idle`. |
| `HITL (Human-in-the-Loop)` | Pausa controlada del flujo donde la continuación hacia el siguiente rol depende de una acción humana (ej. `utils/approve_step.py`). |
| `Bypass Headless` | Enrutamiento condicional donde proyectos sin interfaz gráfica omiten la fase de UX y avanzan directamente de QA a Arquitectura. |
| `Modo Dual (Greenfield / Brownfield)` | Capacidad nativa donde la presencia del archivo `files/context/legacy_ecosystem.md` actúa como interruptor: si existe, todos los agentes subordinan sus entregables al sistema legado; si no, operan como proyecto nuevo sin restricciones. |

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
- **Fase Ágil de Especificación:** El PM asignará épicas al BA (`@BA:`), quien redactará las HUs y delegará a QA (`@QA:`). Tras la aprobación, el flujo continúa a UX (`@UX:`) o salta a Arquitectura (`@SA:`) si es Headless.

---

### Paso 5: Transición a Fase de Arquitectura
Cuando el Designer UX concluye el diseño visual de todas las épicas del MVP (o QA en modo Headless):
1. **Delegación a SA:** Designer UX anexa formalmente la orden `@SA:` en el tracker.
2. **Evaluación de Entorno y Descubrimiento Técnico:**
   - **En Modo Greenfield (sin archivo legacy):** Solutions Architect formula 5 preguntas de gobernanza (Cloud, stack, presupuesto, Greenfield/Brownfield) al `@HUMANO:` en el tracker. Tras tu respuesta, genera `tech_guidelines.md`.
   - **En Modo Brownfield (con `files/context/legacy_ecosystem.md`):** Solutions Architect detecta e ingiere el archivo automáticamente (Cero Fricción), adopta el stack, servidores y restricciones preexistentes sin formular preguntas genéricas al humano, y compila inmediatamente `tech_guidelines.md` subordinado al ecosistema legacy.
3. **Delegación a Persistencia:** SA delega formalmente a `@DA:`.
4. **Persistencia e Integración:** Data Architect genera el MER (`db_*.md`) y delega a `@API:` (o a `@QT:` si es ETL). API Architect define los contratos (`api_*.md`) y delega a `@QT:`.
5. **Auditoría Cruzada Final:** QA Técnico audita la coherencia entre el MER y la API (y contra el archivo legacy si aplica), compila el documento maestro `tech-design_*.md` y solicita la aprobación final (`@HUMANO:`).
6. **Aprobación de Arquitectura:** Ejecuta nuevamente `python utils/approve_step.py` (Opción 7: QA Técnico) para transferir el proyecto al equipo de desarrollo (`@DEV:`).

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
| **SA** | `pb_*.md` + `mvp_*.md` + (Q&A Humano o `legacy_ecosystem.md`) | `tech_guidelines.md` (Gobernanza) | `files/solutions-architect/` |
| **DA** | `hu_*.md` + `pb_*.md` + Guidelines | `db_[nombre].md` (MER + ADRs) | `files/data-architect/` |
| **API** | `db_*.md` + `hu_*.md` | `api_[nombre].md` (Contratos + ADRs) | `files/api-architect/` |
| **QT** | `db_*.md` + `api_*.md` | `tech-design_[nombre].md` (TDD Maestro) | `files/qa-tech/` |

> *Nota sobre Modo Brownfield: Si existe el archivo `files/context/legacy_ecosystem.md`, todos los agentes de negocio, producto, requerimientos y arquitectura lo consumen de forma complementaria para subordinar sus entregables a dicho entorno.*

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
| El enjambre ignora restricciones del sistema existente | `files/context/legacy_ecosystem.md` no existe o está vacío | Crear `files/context/legacy_ecosystem.md` detallando el stack, datos y reglas preexistentes antes de iniciar el flujo. |
| Se desea alternar entre Greenfield y Brownfield | Gestión del archivo interruptor físico | Para Greenfield: renombrar o borrar `legacy_ecosystem.md`. Para Brownfield: crear o poblar dicho archivo. |
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
