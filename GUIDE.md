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
  - `MCP Stitch` (opcional/requerido para generación de wireframes en UX).
- **Rutas parametrizadas:** Archivo `config_bmad.json` actualizado según las instrucciones de [`SETUP.md`](./SETUP.md).

---

## 2. Conceptos Clave

### Etapas y Agentes del Ciclo BMAD

| Etapa | Agente Responsable | Acción / Qué Produce |
|---|---|---|
| **Discovery & Storytelling** | `business-storyteller` | Evalúa la idea cruda, ejecuta preguntas de refinamiento si es ambigua y produce `idea_*.md`. |
| **Product Definition** | `product-analyst` | Transforma la narrativa en un Product Brief formal estructurado (`pb_*.md`). |
| **Management & Planning** | `product-manager` | Prioriza el alcance del MVP, define la arquitectura modular y el Backlog de Épicas (`mvp_*.md`). |
| **Specification & BDD** | `business-analyst` | Redacta Historias de Usuario atómicas con criterios de aceptación en sintaxis Gherkin (`hu_*.md`). |
| **Quality Assurance** | `qa-documental` | Audita trazabilidad, *sad paths* y coherencia lógica (`qa_*.md`), aprobando o rechazando la HU. |
| **UX & Visual Design** | `designer-ux` | Traduce escenarios Gherkin a wireframes UI con MCP Stitch (`ux_*.md`) y audita el cierre de épicas. |

### Términos Fundamentales

| Término | Significado |
|---|---|
| `Token-Passing` | Modelo de orquestación lineal donde los agentes se transfieren el turno de ejecución secuencialmente mediante etiquetas (`@AGENTE:`). |
| `tracker_bmad.md` | Bus de eventos y archivo central de estado donde se registran cronológicamente todas las órdenes y handoffs. |
| `Handoff` | Transición entre dos agentes donde el emisor documenta la ruta del archivo generado para que el receptor lo consuma vía MCP. |
| `Backpressure` | Mecanismo del Watcher para retener tareas encoladas hasta que el agente destinatario se encuentre en estado `idle`. |
| `HITL (Human-in-the-Loop)` | Capacidad del Business Storyteller de pausar el flujo automático para consultar directamente al usuario en caso de ideas ambiguas. |

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
> *Este script creará la grilla de terminales, asignará los modelos y niveles de esfuerzo de razonamiento correspondientes (FinOps) y aplicará los permisos de sandbox con `--add-dir`.*

---

### Paso 3: Disparar el Flujo con una Idea de Negocio
Dirígete a la terminal del agente **Business Storyteller** (o envía un prompt directo) con la visión informal del producto:

```text
@BS: Necesitamos desarrollar una plataforma web para que clínicas veterinarias gestionen citas médicas, historial clínico de mascotas y recordatorios automáticos por WhatsApp.
```

---

### Paso 4: Monitoreo Autónomo y Aprobación (HITL)
- **Si la idea es ambigua:** El Business Storyteller formulará 3 a 4 preguntas en su panel. Responde en el mismo chat para que proceda a generar `idea_*.md`.
- **A partir de la delegación:** El Watcher detectará la orden `@PA:` y el flujo avanzará hacia el PA.
- **Aprobación Manual:** Cuando el PA termina el Product Brief, detiene el flujo solicitando aprobación (`@HUMANO:`). Para continuar:
  1. Revisa el archivo generado en `files/product-analyst/`.
  2. Abre una nueva terminal y ejecuta `python utils/approve_step.py`.
  3. Selecciona la opción del agente (ej. `[2] Product Analyst`) y confirma con `s`.
  4. El script despachará la orden `@PM:` y el Watcher despertará automáticamente.
- El resto del flujo procederá de forma desatendida a través de PM -> BA -> QA -> UX.
- Cada tarea completada generará un entregable en su respectiva carpeta dentro de `files/` y disparará un commit automático en Git.

---

### Paso 5: Cierre del Proyecto
Cuando el Designer UX procese la última épica del Backlog del MVP, emitirá la notificación final:
```markdown
@HUMANO: El flujo de especificación y diseño para el MVP ha concluido exitosamente. Todos los entregables están listos en files/.
```

---

## 4. Matriz de Entradas y Salidas

| Agente | Entrada Requerida | Salida Generada | Ubicación de Salida |
|---|---|---|---|
| **BS** | Idea o requerimiento crudo del usuario | `idea_[nombre].md` | `files/business-storyteller/` |
| **PA** | `idea_[nombre].md` | `pb_[nombre].md` (Product Brief) | `files/product-analyst/` |
| **PM** | `pb_[nombre].md` | `mvp_[nombre].md` (Plan MVP + Épicas) | `files/product-manager/` |
| **BA** | `mvp_[nombre].md` + `pb_[nombre].md` | `hu_[nombre].md` (Historias BDD) | `files/business-analyst/` |
| **QA** | `hu_[nombre].md` + `pb_[nombre].md` | `qa_[nombre].md` (Auditoría / Feedback) | `files/qa-documental/` |
| **UX** | `hu_[nombre].md` (Aprobada) | `ux_[nombre].md` (Wireframes Stitch) | `files/designer-ux/` |

---

## 5. Solución de Problemas

| Síntoma | Causa Probable | Solución Recomendada |
|---|---|---|
| El Watcher indica `Agente no encontrado` | El panel de Herdr no coincide con el nombre esperado | Verificar que `start_agents.py` haya nombrado los paneles correctamente o ejecutar `herdr agent list`. |
| El agente reporta `Access Denied` al leer un archivo | El agente no tiene permisos sobre la ruta raíz del proyecto | Asegurarse de haber arrancado el agente con el flag `--add-dir` en la raíz (manejado automáticamente por `start_agents.py`). |
| Bucle infinito entre BA y QA (Rechazo repetido) | El LLM del BA no logra interpretar el feedback de QA | Intervenir manualmente en la terminal del BA inyectando la corrección puntual y reactivar el Watcher. |
| El Watcher no reacciona a nuevas líneas en el tracker | El archivo `tracker_bmad.md` tiene problemas de codificación o permisos | Guardar el archivo en formato UTF-8 sin BOM o reiniciar el proceso `python watcher_bmad.py`. |
| Faltan archivos `AGENTS.md` en los directorios de los agentes | No se ejecutó el paso de compilación previa | El Watcher los compila automáticamente al iniciar, o se pueden forzar corriendo `python watcher_bmad.py`. |
| Se requiere reiniciar el proyecto desde cero | Existen archivos residuales de ejecuciones previas | Ejecutar `python utils/clean_files.py` (opción `T`) y vaciar `files/tracker_bmad.md`. |

---

## 6. Referencias

- **Manual General:** [`README.md`](./README.md)
- **Arquitectura del Sistema:** [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- **Instanciación en Nueva Ruta:** [`SETUP.md`](./SETUP.md)
- **Preguntas Técnicas y Arquitectónicas:** [`QUESTIONS.md`](./QUESTIONS.md)
- **Manifiesto:** [`manifest.yaml`](./manifest.yaml)
- **Catálogo Backstage:** [`catalog-info.yaml`](./catalog-info.yaml)
