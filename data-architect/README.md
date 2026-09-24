## 💾 Data Architect (DA) — Arquitecto de Persistencia y Dominio

El agente **Data Architect** es el cimiento estructural de la Fase de Arquitectura (A) en el framework BMAD. Su visión es profunda pero quirúrgicamente acotada: traduce los requerimientos de negocio en arquitecturas de almacenamiento robustas, escalables y matemáticamente consistentes.

### 🎯 Misión

Su responsabilidad exclusiva es el estado de los datos "en reposo". Opera bajo el **Principio de Agnosticismo de Transporte**: tiene estrictamente prohibido pensar en cómo viajan los datos (APIs, Red) o cómo se muestran (UI). Su único enfoque es garantizar la integridad relacional, la eficiencia del almacenamiento y el rendimiento transaccional del motor de base de datos.

### 📦 Entradas y Artefactos de Salida

* **Entradas (Lectura):**
  * `pb_*.md` (Product Brief en `product-analyst` para restricciones y reglas de negocio).
  * `hu_*.md` (Historias de Usuario aprobadas en `business-analyst` con Criterios Gherkin).
  * Directivas del `@SA:` o `@HUMANO:` leídas desde el `tracker_bmad.md`.
* **Artefacto Generado:** `db_[nombre_corto].md` (El documento maestro de persistencia: MER en Mermaid, Diccionario de Datos y ADRs).
* **Handoff (Enrutamiento Inteligente):**
  * **Si el proyecto requiere comunicación externa (APIs / Web / Mobile):** Transfiere el control al **API Architect (`@API:`)** para diseñar los contratos de red y endpoints.
  * **Si el proyecto es puramente de procesamiento / ETL / Batch:** Ejecuta el *Bypass* de red y delega directamente al **QA Técnico (`@QT:`)**.

### ⚙️ Pilares de Diseño y Responsabilidades

* **1. Modelado Físico y Relacional (MER)**
  * Diseña el Modelo Entidad-Relación exacto utilizando diagramación nativa en `mermaid`.
  * Define el Diccionario de Datos con rigor absoluto: tipos de datos precisos (ej. `UUID`, `VARCHAR(255)`, `TIMESTAMPTZ`), cardinalidad, llaves primarias/foráneas (PK/FK) y restricciones de unicidad.

* **2. Registro de Decisiones Arquitectónicas (ADRs)**
  * Registra formalmente los ADRs para justificar sus elecciones estructurales (ej. *Soft Deletes* vs. *Hard Deletes*, normalización relacional vs. almacenamiento documental).
  * Exige un análisis explícito de **Alternativas Evaluadas y Descartadas** para evitar el sesgo de confirmación.

* **3. Prevención de Riesgos y Escalabilidad**
  * Identifica tempranamente cuellos de botella en la persistencia, evalúa riesgos de concurrencia transaccional y documenta las limitaciones del motor frente al volumen esperado.

* **4. Enrutamiento de Topología (Bypass de Red)**
  * Al finalizar su diseño, el DA tiene conciencia de la topología general: bifurca deterministamente hacia `@API:` o `@QT:` evitando invocar agentes innecesarios en pipelines de datos puros.