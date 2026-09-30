# 🎯 Plan Arquitectónico: Ciclo de Vida de Ramas Automático (GitOps en BMAD)

Este documento contiene la auditoría, el análisis de riesgos y la propuesta arquitectónica para implementar un flujo GitOps de Feature Branching dinámico, respetando estrictamente los pilares de **Autonomía**, **Degradación Elegante** y **Zero-Trust Agéntico**.

---

## 1. Auditoría de Estado Actual

*   **`watcher_bmad.py`**: Actualmente, la gestión de ramas ocurre únicamente durante el arranque del orquestador en modo interactivo (solicita al usuario seleccionar o crear una rama de forma manual, especialmente si se encuentra en `main/master`). Durante el ciclo de vida del enjambre, el watcher se limita a iterar de manera pasiva y despachar tareas vía CLI (`herdr pane run`) al detectar etiquetas como `@BA:`. No posee heurística en vivo para bifurcaciones de VCS post-arranque.
*   **El Bus de Datos (`tracker_bmad.md`)**: Funciona como un _Append-only bus_ estricto. Las intercepciones que existen actualmente (ej. la compuerta de `QA Documental` o la intercepción `@SPEC-KIT:`) sirven para pausar procesos o disparar Spec Kit, pero ninguna emite comandos contra `git`.
*   **Capacidad Agéntica (`@PM`, `@QT`, etc.)**: Poseen herramientas de File System (como `write_file`) y actualizan metadatos globales como el `specs/README.md`. No obstante, **carecen por completo de capacidad de ejecución en terminal** que afecte el VCS, lo cual está alineado por ahora con la separación entre Fase de Diseño y Fase de Implementación (Fase D).

---

## 2. Análisis de Riesgos

La implementación de automatizaciones sobre `git` presenta vectores de riesgo si no se aísla correctamente el plano de control:

1.  **Riesgo Crítico A (Delegación a Agentes):**
    Permitir que agentes de diseño (ej. `@PM`, `@BA` o `@QT`) ejecuten directamente comandos como `git checkout -b` viola el principio de **Zero-Trust Agéntico**. Al ser entes asíncronos y estadísticos, si un agente genera un nombre de rama con caracteres inválidos, altera el File System mientras otro proceso está leyendo, o se desincroniza respecto de la rama activa del orquestador, el ecosistema colapsará.
2.  **Riesgo Crítico B (Merge Silencioso y Conflictos):**
    Si se programa al `watcher_bmad.py` para reaccionar ciegamente ante un cambio en `specs/README.md` e iniciar un auto-merge hacia `dev`:
    *   **Race Conditions:** Podría disparar el `git merge` antes de que el agente haya terminado de consolidar todos los commits de la feature.
    *   **Merge Conflicts Seguros:** Al trabajar en ramas aisladas, archivos de estado global como el propio `specs/README.md` o el `tracker_bmad.md` generarán inevitablemente conflictos al ser reintegrados a `dev` si esta rama base avanzó por el trabajo de otras HUs.
    *   **Bloqueo de Estado (MERGE_HEAD):** Implementar un bloque `try/except` que falle en silencio dejará el entorno bloqueado en medio del conflicto, paralizando el enjambre y violando el pilar de **Degradación Elegante**.

> **Conclusión de Riesgos:** Todo comando de mutación de VCS debe estar centralizado y sincronizado en un hilo maestro (el Watcher). El Watcher no debe deducir intenciones basándose en cambios de archivos, sino reaccionar a **comandos explícitos, deterministas y estandarizados** vertidos en el Tracker por los agentes autorizados.

---

## 3. Propuesta Arquitectónica (La Vía Segura)

El plan consiste en escalar el rol de `watcher_bmad.py` para convertirlo en el único **Event-Sourcing Git Controller**, orquestando el VCS de forma síncrona mediante señales estandarizadas.

### Lógica Core del Orquestador (`watcher_bmad.py`)

1.  **State Hydration (Arranque):**
    *   Durante su inicialización (`iniciar_watcher()`), el script realizará un barrido retrospectivo completo del `tracker_bmad.md`.
    *   Buscará pares desbalanceados analizando las macros `@WATCHER: GITOPS-BRANCH-CREATE` y `@WATCHER: GITOPS-MERGE-CLOSE`.
    *   Si encuentra un "CREATE" sin su respectivo "CLOSE" (macro huérfana), inferirá que hay una operación en curso e intentará alinearse automáticamente ejecutando `git checkout <rama_huérfana>`.
2.  **Intercepción en Vivo:**
    *   Se modificará el loop principal de lectura del tracker para que, antes de parsear turnos de agentes (ej. buscar `@BA:` o `@QT:`), intercepte y procese primero las instrucciones dirigidas a `@WATCHER: GITOPS-`.
3.  **Ejecución Segura (REGLA CRÍTICA DE INTEGRIDAD):**
    *   Antes de ejecutar *cualquier* salto de rama (`git checkout`) o fusión (`git merge`), el orquestador verificará imperativamente si el *working directory* está limpio usando `git status --porcelain`.
    *   Si existen archivos sin commitear, forzará un autoguardado ejecutando `git add .` seguido de `git commit -m "chore: auto-commit pre-branch switch"`.
    *   Esto garantiza que Git nunca bloquee o aborte la operación a la mitad por cambios no guardados.
4.  **Manejo de Conflictos:**
    *   Las operaciones de `git merge --no-ff <rama>` estarán encapsuladas en un bloque `try/except`.
    *   **Degradación Elegante y Amnesia Estratégica:** Si la fusión falla por conflictos, el watcher ejecutará de inmediato `git merge --abort` para devolver el repositorio a un estado seguro.
    *   Retornará a la rama de origen y emitirá en el tracker el fallback: `@HUMANO: 🚨 ALERTA GITOPS: Conflicto de fusión...` detallando los pasos de recuperación. El Watcher asumirá amnesia estratégica, permitiendo que el humano resuelva el conflicto en su terminal y reinicie el sistema sin alterar el historial del tracker.

### Actualización de Agentes (Emisores de Eventos)

Para disparar los comportamientos del orquestador de manera determinista, se ajustarán las plantillas de dos agentes clave:

1.  **Módulo `@PM` (Product Manager):**
    *   **Acción:** Es el responsable de iniciar el ciclo.
    *   **Disparo:** Justo después de estructurar el MVP de una Epic/HU y *antes* de dar el handoff al `@BA`, el PM deberá imprimir estrictamente en el tracker la macro:
        `@WATCHER: GITOPS-BRANCH-CREATE feat/HU_[nombre_corto_hu]`
2.  **Módulo `@QT` (QA Tech):**
    *   **Acción:** Es el responsable de auditar y cerrar la fase de diseño.
    *   **Disparo:** Justo después de aprobar el Tech Design, actualizar el Ledger (`specs/README.md`) al estado `READY-FOR-DEV` y *antes* de derivar el trabajo a la Fase de Desarrollo (vía `/speckit.implement` o comandos hacia `@DEV-BACK`), el QT deberá imprimir en el tracker la macro:
        `@WATCHER: GITOPS-MERGE-CLOSE feat/HU_[nombre_corto_hu]`

---

Esta arquitectura consolidada garantiza cero interrupciones incontroladas, blinda la gobernanza del repositorio, preserva los avances automáticos sin perder trabajo y exige intervención humana (HITL) solo frente a colisiones estrictas de VCS.
