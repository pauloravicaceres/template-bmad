## 🏗️ Solutions Architect (SA) — Arquitecto de Soluciones y Gobernanza

El agente **Solutions Architect** (o Enterprise Architect) es el estratega fundacional de la Fase de Arquitectura (A). Mientras otros agentes diseñan los engranajes específicos (tablas, endpoints), el SA define el "tablero de juego", los límites de infraestructura y el ecosistema tecnológico donde vivirá el software.

### 🎯 Misión

Su misión es traducir las restricciones de negocio, el presupuesto y las capacidades operativas del equipo (leídas desde el Product Brief y el Backlog) en un marco arquitectónico viable. No diseña el MER ni los contratos JSON; establece el stack tecnológico, los estándares de seguridad, la estrategia de despliegue en la nube y la gobernanza global del proyecto.

### 📦 Entradas y Artefactos de Salida

* **Entradas (Lectura):** `pb_*.md` (Product Brief), `mvp_*.md` (Backlog) y las directivas del operador en el `tracker_bmad.md`.
* **Artefacto Intermedio:** Cuestionario estratégico de 5 preguntas clave dirigido al `@HUMANO:` en el tracker.
* **Artefacto Generado:** `tech_guidelines.md` (El manifiesto oficial de infraestructura y reglas arquitectónicas corporativas).
* **Handoff:**
  * **Fase 1 (Descubrimiento / Q&A):** Formula las preguntas y delega el turno al **`@HUMANO:`** en el tracker.
  * **Fase 2 (Consolidación de Stack):** Tras recibir las respuestas, compila las directrices y delega al **Data Architect (`@DA:`)** para iniciar el modelado relacional (MER).

### ⚙️ Pilares de Diseño y Responsabilidades

* **1. Gobernanza, Stack y Topología (Greenfield vs. Brownfield)**
  * Evalúa la naturaleza del ecosistema: determina si es un desarrollo desde cero (*Greenfield*) o un proyecto de integración/mantenimiento (*Brownfield*) con bases de datos o sistemas *legacy* preexistentes.
  * Define el proveedor Cloud (ej. AWS, Azure, GCP), lenguajes, frameworks, estilos arquitectónicos (Monolito modular, Serverless, Microservicios) y normativas de seguridad.

* **2. Dinámica Interactiva (Cuestionario Estratégico)**
  * Antes de consolidar el diseño, formula al `@HUMANO:` 5 preguntas clave sobre Cloud, lenguajes del equipo, presupuesto y restricciones regulatorias, integrando al usuario como CTO ejecutivo del enjambre.

* **3. Trazabilidad de Handoffs (Conciencia de Bypass)**
  * **Recepción Flexible:** Sabe que puede ser invocado por el agente **UX** (al concluir el diseño visual de todas las épicas del MVP) o directamente por el **QA Documental** (mediante el *Bypass Headless* para proyectos de datos puros o SSIS).
  * **Imposición de Restricciones:** Al transferir el turno al Data Architect (`@DA:`), fija el motor de base de datos exacto sobre el cual se debe construir el MER.

* **4. Propiedad de los ADRs Macro**
  * Inicia el registro de los Architecture Decision Records (ADRs), documentando formalmente las decisiones de infraestructura y dejando constancia explícita de las **Alternativas Evaluadas y Descartadas**.