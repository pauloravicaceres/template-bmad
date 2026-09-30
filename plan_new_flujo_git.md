# Plan de Refactorización: Desacoplamiento del SDD Auto-Runner

## 1. Auditoría del Orquestador (`watcher_bmad.py`)
He revisado la función `ejecutar_ciclo_sdd(ruta_hu)` y su integración en `extraer_instrucciones()`. Actualmente, el orquestador funciona como un **monolito de ráfaga**: en cuanto detecta el handoff o la aprobación del QA Documental (`@QA`), detiene el flujo y ejecuta secuencialmente `/speckit.specify`, `clarify`, `plan`, `tasks` y `analyze`. 

**Impacto del Monolito:** 
Este diseño genera un grave problema de "alucinación arquitectónica". Spec-Kit ejecuta `/speckit.plan` e intenta trazar la arquitectura *antes* de que el `@SA` (Solutions Architect) haya evaluado el contexto, consultado la Constitución (`constitution.md`) y definido los ADRs reales en `tech_guidelines.md`. En la práctica, esto invierte la topología: la IA externa (Spec-Kit) decide el stack antes de que el cerebro arquitectónico de BMAD lo autorice.

---

## 2. Diseño del Nuevo Flujo Desacoplado (Vertical Slicing Branching)
Para respetar el principio Zero-Trust y la jerarquía de roles sin cerrar prematuramente la rama GitOps, el ciclo se fragmentará en dos pausas lógicas distintas dentro de la **misma Feature Branch**.

*   **Hito 1: Fase de Negocio (Post-QA Documental)**
    *   **Gatillo:** El orquestador intercepta el certificado `aprobado_qa_*.md`.
    *   **Ejecución Restringida:** El orquestador ejecuta **SOLO** `/speckit.specify` y `/speckit.clarify`. Esto define los escenarios BDD funcionales pero NO propone arquitectura.
    *   **Reanudación:** El Watcher cede el paso al `@UX` (o directamente al `@SA` si el proyecto es headless).
*   **Hito 2: Fase de Arquitectura (Post-SA)**
    *   **Gatillo:** El `@SA` diseña el stack técnico formal (`tech_guidelines.md`) y emite una macro determinista (ej. `@WATCHER: SDD-FREEZE`).
    *   **Ejecución Restringida:** El orquestador intercepta, ejecuta **SOLO** `/speckit.plan`, `/speckit.tasks` y `/speckit.analyze`. Spec-Kit ahora leerá el `tech_guidelines.md` recién creado por el SA para alinear su plan a la gobernanza dictada. El Watcher ejecuta el commit `[SPEC-FREEZE]` y permite el handoff al `@DA:`.
*   **Hito 3: Implementación (Fase D)**
    *   Los desarrolladores operan en la misma rama consumiendo el `tasks.md` exacto mediante `/speckit.implement`.
*   **Hito 4: Cierre (Merge-Close)**
    *   El `@QT`, tras la Fase D (o equivalente de calidad final), despacha el `@WATCHER: GITOPS-MERGE-CLOSE` cerrando la rama de manera atómica.

---

## 3. Plan de Implementación a Nivel de Código (Acciones)

**A. Refactorización en `watcher_bmad.py`:**
1.  **Eliminar:** Borrar la función `ejecutar_ciclo_sdd()`.
2.  **Crear:** `ejecutar_sdd_fase_negocio(ruta_hu)` (contiene `specify`, `clarify` y auto-handoff a UX/SA).
3.  **Crear:** `ejecutar_sdd_fase_arquitectura()` (contiene `plan`, `tasks`, `analyze`, commit `[SPEC-FREEZE]` y auto-handoff a DA).
4.  **Actualizar Interceptor de QA:** En `extraer_instrucciones`, el bloque `SDD GATEKEEPER` llamará únicamente a `ejecutar_sdd_fase_negocio`.
5.  **Nuevo Interceptor de SA:** Se creará un bloque adicional en `extraer_instrucciones` que escuche la etiqueta `@WATCHER: SDD-FREEZE` para disparar `ejecutar_sdd_fase_arquitectura()`.

**B. Expresiones Regulares (Regex) / Palabras Clave:**
*   **Interceptor Negocio:** Sigue usando `es_aprobacion_qa = "aprobado_qa_" in linea_lower or ("@qa:" in linea_lower and "aprobado" in linea_lower)`.
*   **Interceptor Arquitectura:** `es_sdd_freeze = "@watcher: sdd-freeze" in linea_lower`. 

**C. Actualización en las Instrucciones de Agentes (`.agent.md` / `.instructions.md`):**
*   **`@SA` (Solutions Architect):** Obligarlo a inyectar en el tracker la etiqueta `@WATCHER: SDD-FREEZE` y hacer Handoff al `@DA:`. Aclarar que él dicta la pauta *antes* de que Spec-Kit haga el plan.
*   **`@DA` y `@API`:** Aclarar que leerán `spec.md`, `plan.md` y `tasks.md` que serán generados **inmediatamente después** de la directriz del SA.

---

## 4. Estrategia de Actualización de Documentación Global

Para evitar fisuras cognitivas en el ecosistema, se inyectarán las siguientes definiciones:

*   **`framework_bmad.md` y `ARCHITECTURE.md`:** 
    *   Reescribir las secciones de "SDD Auto-Runner". Introducir la noción de **Doble Compuerta SDD (Two-Stage Gatekeeper)**: una para Negocio (`specify`) y otra para Arquitectura (`plan/tasks`).
    *   Actualizar los diagramas Mermaid `sequenceDiagram` para mostrar que el Watcher detiene el flujo en dos puntos distintos de la línea de tiempo.
*   **`GUIDE.md`:** 
    *   Modificar la sección de "Uso Paso a Paso", indicando al humano que verá al Watcher pausar dos veces en su consola: una antes del `@UX` y otra antes del `@DA`.
*   **`constitution.md` (y lineamiento transversal):**
    *   Se inyectará un bloque conceptual de "Prolongación de Feature Branch". Debe reafirmarse que la rama de Git (`feat/XXX-HU...`) es un contenedor de ciclo de vida completo: nace con el PM en la fase de ideación, madura a través del QA y la Arquitectura, y solo se cierra cuando el QA-Tech (`@QT`) estampa el dictamen final, asegurando que ninguna abstracción o Spec quede huérfana de código.
