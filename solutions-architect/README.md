## 🏗️ Solutions Architect (SA) — Arquitecto de Soluciones y Gobernanza

El agente **Solutions Architect** (o Enterprise Architect) es el estratega fundacional de la Fase de Arquitectura (A). Mientras otros agentes diseñan los engranajes específicos (tablas, endpoints), el SA define el "tablero de juego", los límites de infraestructura y el ecosistema tecnológico donde vivirá el software.

### 🎯 Misión

Su misión es traducir las restricciones de negocio, el presupuesto y las capacidades operativas del equipo (leídas desde el Product Brief y el Backlog) en un marco arquitectónico viable. No diseña el MER ni los contratos JSON; establece el stack tecnológico, los estándares de seguridad, la estrategia de despliegue en la nube y la gobernanza global del proyecto.

### 📦 Entradas y Artefactos de Salida

* **Entradas (Lectura):** `pb_*.md` (Product Brief), `mvp_*.md` (Backlog), `files/context/legacy_ecosystem.md` (opcional) y las directivas del operador en el `tracker_bmad.md`.
* **Artefacto Intermedio:** Cuestionario estratégico de 5 preguntas clave dirigido al `@HUMANO:` en el tracker (exclusivo para Modo Greenfield).
* **Artefacto Generado:** `tech_guidelines.md` (El manifiesto oficial de infraestructura y reglas arquitectónicas corporativas).
* **Handoff:**
  * **Modo Greenfield (Proyecto Nuevo):** Formula las 5 preguntas y delega el turno al **`@HUMANO:`**. Tras recibir las respuestas, compila las directrices y delega al **Data Architect (`@DA:`)**.
  * **Modo Brownfield (Cero Fricción):** Detecta `files/context/legacy_ecosystem.md`, omite el cuestionario interactivo genérico, compila de inmediato `tech_guidelines.md` subordinado al sistema legado y delega directamente al **Data Architect (`@DA:`)**.

### ⚙️ Pilares de Diseño y Responsabilidades

* **1. Gobernanza, Stack, Estado y Resiliencia (Greenfield vs. Brownfield)**
  * Evalúa la presencia física de `files/context/legacy_ecosystem.md`: si existe, adopta de forma determinista la arquitectura y servidores preexistentes; si no existe, asume desarrollo desde cero (*Greenfield*).
  * Define el proveedor Cloud, lenguajes, frameworks, estilos arquitectónicos, fronteras de manejo de estado y patrones de tolerancia a fallos/resiliencia.

* **2. Dinámica Interactiva vs. Ingesta Silenciosa**
  * En Greenfield, formula al `@HUMANO:` 5 preguntas clave sobre Cloud, lenguajes, presupuesto y restricciones. En Brownfield, ingiere autónomamente las reglas sin generar cuellos de botella.

* **3. Trazabilidad de Handoffs (Conciencia de Bypass)**
  * **Recepción Flexible:** Sabe que puede ser invocado por el agente **UX** (al concluir el diseño visual de todas las épicas del MVP) o directamente por el **QA Documental** (mediante el *Bypass Headless* para proyectos de datos puros o SSIS).
  * **Imposición de Restricciones:** Al transferir el turno al Data Architect (`@DA:`), fija el motor de base de datos exacto sobre el cual se debe construir el MER.

* **4. Propiedad de los ADRs Macro (Formato MADR)**
  * Inicia el registro de los Architecture Decision Records (ADRs) bajo el estándar formal MADR, documentando formalmente las decisiones de infraestructura con alternativas viables reales y costos/trade-offs explícitos.
  * Para entornos Brownfield, cataloga las decisiones impuestas como `Aceptado (heredado)` sin requerir alternativas ficticias.