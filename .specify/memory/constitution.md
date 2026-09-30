# 📜 Constitución Técnica Global de BMAD

## 🌐 REGLAS DE COMPORTAMIENTO Y LOCALIZATION (LEX SUPERIOR)
1. **Idioma Estricto:** Independientemente del idioma original en el que estén redactadas las plantillas base del sistema, TODO el contenido generado (escenarios BDD, ADRs, tareas técnicas) DEBE redactarse en **Español**.
2. **Modo Máquina (Anti-Conversacional):** Tienes ESTRICTAMENTE PROHIBIDO actuar como un chatbot o asistente de cortesía. Nunca saludes, nunca te despidas, ni ofrezcas ayuda adicional. No hagas preguntas triviales ni pidas permiso para continuar (ej. prohibido preguntar "¿Te gustaría que asuma el rol de...?"). **Excepción Técnica:** Si tu diagrama de flujo (Máquina de Estados) requiere recabar requisitos críticos antes de generar un entregable (ej. el `@SA` recopilando preferencias de infraestructura), SÍ debes emitir tu cuestionario técnico de forma directa y delegar el turno al `@HUMANO:`. Todo lo demás debe emitirse silenciosamente.

## ESTÁNDAR GITOPS Y CICLO DE VIDA (FEATURE BRANCHING)

El ecosistema BMAD opera bajo un modelo automatizado de integración continua local donde el orquestador **`watcher_bmad.py` es el único controlador autorizado del repositorio (VCS)**. 

### Principios Fundamentales
1. **Aislamiento por Defecto:** El desarrollo de cada Historia de Usuario (HU) ocurre estrictamente en ramas aisladas generadas automáticamente bajo la nomenclatura `feat/HU_[nombre_corto]`.
2. **Zero-Trust Agéntico:** Ningún agente LLM (Product Manager, QA, Business Analyst, etc.) tiene permitido ejecutar comandos transaccionales contra Git de forma directa. Toda manipulación se solicita de manera declarativa en el Bus de Datos (`tracker_bmad.md`) utilizando macros del sistema (ej. `@WATCHER: GITOPS-BRANCH-CREATE`).
3. **Product State Ledger:** El estado transaccional del proyecto se gobierna mediante el mapa inmutable en `specs/README.md`. Cuando el Tech Design de una característica recibe aprobación (QA-Tech) y cambia su estado a `READY-FOR-DEV`, el Watcher es invocado automáticamente para fusionar y cerrar la rama de la característica hacia la rama base (`dev` o `main`).

> **Nota de Resiliencia:** El Watcher realiza operaciones de hidratación (State Hydration) y _commits_ preventivos (`chore: auto-commit pre-branch switch`) para proteger el *working directory*. En caso de conflictos durante el auto-merge, el sistema aplicará un _abort_ seguro delegando la resolución al humano.

### Protocolo de Resolución de Conflictos (Fallback)
La resolución de conflictos de control de versiones (VCS) es de **jurisdicción estrictamente humana**. Tras un fallo en la fusión automática, el sistema asume una **"Amnesia Estratégica"**. 
Esto significa que el humano solo debe resolver el conflicto en Git manualmente (fusionando o haciendo rebase hacia la rama base) y luego **reiniciar el orquestador sin manipular el historial del tracker**. El orquestador, por diseño, asumirá que la rama problemática ha sido procesada exitosamente y continuará su operación normal de forma resiliente.

### Identificador Secuencial Universal (SSOT)
Para asegurar una trazabilidad absoluta entre el modelo de negocio, el control de versiones y los artefactos físicos (crítico en escenarios Brownfield), el ecosistema emplea la convención estricta `XXX-HU_[nombre_corto]`, donde `XXX` es un correlativo numérico de 3 dígitos (ej. `001`, `002`).
Esta nomenclatura nace obligatoriamente en el **Product State Ledger** (`specs/README.md`) calculado por el `@PM`, y debe permear simétricamente en:
1. El nombre de la rama GitOps (`feat/XXX-HU_[nombre]`).
2. El nombre del archivo físico de la Historia de Usuario en el disco (`files/business-analyst/XXX-HU_[nombre].md`).
3. Los Hand-offs y registros en el Tracker.

---

## 🛑 Regla de Oro: Principio de Vertical Slicing Estricto

El ecosistema BMAD v2.0 opera bajo un modelo de **Vertical Slicing Estricto** para garantizar la salud del State Ledger y evitar divergencias arquitectónicas.

*   **Prohibición de Desarrollo Horizontal:** Queda estrictamente prohibido abrir o diseñar múltiples Historias de Usuario (HUs) a la vez. No se puede avanzar al diseño de una nueva característica si la anterior no ha cerrado su ciclo.
*   **Ciclo de Vida de Rebanada Vertical:** Toda HU debe atravesar el ciclo completo antes de iniciar la siguiente: `PM -> BA -> QA -> UX -> SA -> (Fases Técnicas) -> QT -> Retorno a PM`.
*   **Regla de Ramas GitOps:** Queda terminantemente prohibido que el `@PM` inicie una nueva historia y emita un `GITOPS-BRANCH-CREATE` si la historia anterior no ha sido debidamente compilada y fusionada en el código base principal por el `@QT` mediante `GITOPS-MERGE-CLOSE`.

---

## 🔒 Consistencia de Nomenclatura y Trazabilidad (Identificador Universal)

El ecosistema BMAD v2.0 impone una trazabilidad matemática exacta (1:1) entre el Product State Ledger, el control de versiones y el sistema de archivos físico mediante el uso de un **Identificador Universal Estricto**.

1. **Formato Inmutable:** Todas las historias de usuario deben adoptar la nomenclatura `XXX-HU_nombre_en_snake_case` (ej. `001-HU_tarjeta_identidad_digital`).
2. **Columnas del Ledger:** La tabla del Ledger (`specs/README.md`) utiliza oficialmente la estructura: `| N° | Épica Origen | Nombre spec / HU | Qué aporta | Estado | Rama |`.
3. **Uso Obligatorio Transversal:** Este identificador exacto y sin truncar se utiliza obligatoriamente para:
   - Registrar la funcionalidad en la columna `Nombre spec / HU` y en la columna `Rama` (`feat/001-HU_...`) del Ledger.
   - Orquestar la bifurcación GitOps (`@WATCHER: GITOPS-BRANCH-CREATE feat/XXX-HU_...`).
   - Nombrar los archivos físicos `.md` generados por los agentes (`@BA`, `@BS`, `@SA`, etc.). Queda terminantemente prohibido truncar, resumir o alterar este identificador en los nombres de archivo.

---

## 🌿 Regla Inmutable: Prolongación del Feature Branch
La rama de Git creada para cada Historia de Usuario (`feat/XXX-HU...`) opera bajo el principio de **"Feature Branch Prolongada"**. Esta rama de trabajo es un contenedor de ciclo de vida completo:
1. **Nace** con el Product Manager en la fase de orquestación inicial y se registra en el Ledger.
2. **Madura** a través de la fase de Negocio (QA) y el modelado de Arquitectura (SA/DA/API).
3. **Aloja** todo el código fuente implementado por los agentes desarrolladores y scripts de QA-Auto (Fase D).
4. **Se congela** y **SOLO** se fusiona con la rama principal (`dev`/`main`) a través de la macro `@WATCHER: GITOPS-MERGE-CLOSE` cuando el QA-Tech (`@QT`) emite el dictamen aprobatorio final. Queda estrictamente prohibido cerrar, fusionar o abandonar la rama prematuramente.

---

## 📁 ESTRUCTURA DE CARPETAS DEL REPOSITORIO (WORKSPACE)
Para mantener un orden estricto y evitar archivos dispersos en la raíz del proyecto, todos los agentes constructores (Spec-Kit, `@DEV-BACK`, `@DEV-FRONT`, `@QA-AUTO`) deben respetar la siguiente partición física:
1. **Backend:** Todo el código fuente, pruebas, configuraciones y binarios correspondientes al lado del servidor (API, persistencia, lógica de negocio) DEBEN generarse y residir exclusivamente dentro de la carpeta `app/backend/`.
2. **Frontend:** Todo el código fuente, componentes UI, assets y configuraciones del cliente (SPA, interfaces) DEBEN generarse y residir exclusivamente dentro de la carpeta `app/frontend/`.

> **Directiva de Handoff:** Cuando los agentes planificadores (`@SA`, `@QT`, Spec-Kit) generen el `plan.md`, `tasks.md` o el `tech-design_*.md`, las rutas físicas propuestas para cada archivo deben estar obligatoriamente prefijadas con `app/backend/` o `app/frontend/` según corresponda. Ningún archivo de código de producción debe crearse en la raíz del repositorio.
