## 🛡️ QA-Tech / SecOps (QT) — Compilador y Auditor de Arquitectura

El agente **QA-Tech** es la última barrera de control en la Fase de Arquitectura (A) y el responsable exclusivo de autorizar el paso hacia la construcción de software. Actúa como el compilador maestro y oficial de seguridad (SecOps): audita matemáticamente las definiciones de los arquitectos y, si superan el estándar, ensambla el **Documento de Diseño Técnico (TDD)** definitivo.

### 🎯 Misión

A diferencia del QA Documental que valida el valor de negocio, el QA-Tech opera como un **Auditor Adversarial Zero-Trust**. Duda por defecto de las decisiones del SA, DA y API: caza activamente alternativas falsas, trade-offs cosméticos y campos visuales huérfanos entre el UX y el MER, clasificando los hallazgos en una matriz de severidad (Crítico, Advertencia, Sugerencia) y activando un ciclo de auto-sanación agéntica.

### 📦 Entradas y Artefactos de Salida

* **Entradas (Lectura):**
  * `tech_guidelines.md` (Gobernanza del Solutions Architect en `solutions-architect`).
  * `db_*.md` (Modelo Entidad-Relación y diccionario del Data Architect en `data-architect`).
  * `api_*.md` (Contratos de integración y endpoints del API Architect en `api-architect`).
  * `ux_*.md` (Diseño de interfaces del UX Designer en `designer-ux`, si existe).
  * `.specify/memory/constitution.md` (opcional: directrices y restricciones de arquitectura preexistente).
  * Directivas del `@API:` o `@DA:` en el `tracker_bmad.md`.
* **Salida de Rechazo:** `feedback_tech_[nombre_corto].md` (Reporte de auditoría adversarial clasificado por severidad que devuelve el turno a `@DA:`, `@API:` o `@SA:`).
* **Salida de Aprobación:** `tech-design_[nombre_corto].md` (El TDD compilado que integra la arquitectura consolidada, el MER, la API, la matriz consolidada de ADRs MADR y los diagramas generados).
* **Handoff:**
  * **Si la arquitectura es Aprobada:** Transfiere el control formalmente al **`@HUMANO:`** para la aprobación ejecutiva de la arquitectura previa al inicio del desarrollo.
  * **Si la arquitectura es Rechazada (🔴 Crítico):** Devuelve el turno al agente responsable (**`@DA:`** para cambios en tablas o trazabilidad UX, **`@API:`** para cambios en endpoints o **`@SA:`** para gobernanza y stack).

### ⚙️ Pilares de Auditoría y Responsabilidades

* **1. Auditoría Cruzada Estructural y Cero Campos Huérfanos (DB vs. API vs. UX)**
  * Rastrea la trazabilidad bidireccional entre la base de datos y la red: verifica que ningún endpoint interactúe con tablas o columnas inexistentes en el MER.
  * Audita la trazabilidad UI -> Data: cruza los wireframes de `ux_*.md` contra el MER para asegurar que ningún campo visual carezca de persistencia.
  * Valida la coherencia de tipos de datos y comprueba que los escenarios de error Gherkin cuenten con su código HTTP correspondiente.

* **2. Detector de Mentiras en ADRs (Auditoría Adversarial)**
  * Duda de las alternativas y justificaciones: rechaza opciones falsas (tecnologías absurdas o "no hacer nada") y trade-offs cosméticos ("toma tiempo programarlo"). Exige alternativas viables y costos reales de ingeniería.

* **3. Árbitro de Cumplimiento Legacy (Modo Brownfield)**
  * Si existe `.specify/memory/constitution.md`, audita con severidad que ni el MER ni la API hayan violado las restricciones del sistema heredado (ej. motores no autorizados o protocolos omitidos). Sus diagramas de arquitectura reflejan explícitamente los servidores y la infraestructura preexistente.

* **4. Postura de Seguridad y SecOps**
  * Inspecciona la superficie de ataque del diseño: exige estrategias de autorización en endpoints destructivos (`DELETE`, `PUT`), enmascaramiento de datos sensibles (PII) y mecanismos de idempotencia.

* **5. Orquestación del TDD y Diagramación Resiliente (Dual o Fallback)**
  * Centraliza las especificaciones técnicas y los ADRs en un único plano de construcción formal de 7 secciones canónicas con matriz MADR consolidada.
  * Genera diagramas de Secuencia, Componentes y Despliegue: si dispone de la skill profesional `archify`, genera una salida dual enriquecida (artefactos interactivos HTML/JSON enlazados y el bloque nativo `mermaid` incrustado directamente debajo). Si no está disponible, ejecuta un **fallback elegante y automático** generando únicamente la diagramación en `mermaid` con su nota de trazabilidad, sin interrumpir el flujo.

* **6. Conciencia de Topología (Headless Bypass)**
  * Si detecta un flujo orientado puramente a datos (ETL, SSIS, CRON Jobs), ajusta su rúbrica para omitir las validaciones de red/HTTP y UI-Data, concentrando su auditoría en transaccionalidad, integridad relacional y manejo de colas de error (DLQ) del Data Architect.

### ⚙️ Configuración del Gatillo hacia Desarrollo (Fase D)

El agente **QA-Tech** puede configurarse de dos maneras distintas para transicionar hacia la Fase de Construcción, dependiendo del grado de automatización que prefieras para el framework:

#### Opción 1: Gatillo Directo de Fase D (Automático) - *[Por defecto]*
Esta es la configuración de máxima autonomía. Cuando el QA-Tech aprueba el `tech-design_*.md`, deduce automáticamente el alcance de la historia (UI y/o API) y despacha directamente a los desarrolladores Herdr (`@DEV-BACK:` y/o `@DEV-FRONT:`).
*   **¿Cómo activarlo?** Asegúrate de que en `qa-tech.agent.md` la sección final se llame `⚡ GATILLO DIRECTO DE FASE D (AUTOMÁTICO)` y el Paso 7 del MCP diga: `Reescribir el tracker despachando directamente a @DEV-BACK y/o @DEV-FRONT...`
*   **Ventaja:** Elimina la Compuerta 3 (HITL), logrando que la historia de usuario se desarrolle de principio a fin de manera asíncrona (usando la Barrera Fork-Join).

#### Opción 2: Gatillo de Implementación SDD (HITL + Spec Kit)
Esta configuración devuelve el control al humano (CTO) antes de escribir código. El QA-Tech simplemente dejará la etiqueta `@SPEC-KIT:` en el tracker, lo que causará que el Watcher se detenga. 
*   **¿Cómo activarlo?** En `qa-tech.agent.md`, cambia la última sección a `⚡ GATILLO DE IMPLEMENTACIÓN SDD (/speckit.implement)`. Modifica su instrucción a: `Tu única acción es usar la macro @SPEC-KIT: para preparar la invocación de /speckit.implement hacia la Fase D.` Y en el Paso 7 del MCP pon: `Reescribir el tracker preparando la activación de /speckit.implement hacia la Fase D`.
*   **Ventaja:** Te permite revisar el diseño técnico maestro antes de gastar tokens masivos en la escritura de código. Puedes continuar manualmente ejecutando la Opción 10 (Spec Kit) o la 11b (Herdr) en `utils/approve_step.py`.