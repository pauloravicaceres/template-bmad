# 📜 Constitución Técnica Global de BMAD

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
