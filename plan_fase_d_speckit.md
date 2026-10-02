# 🎯 PLAN TÉCNICO: FASE D (MOTOR SPECKIT + ALMA AGÉNTICA)

Este documento define la estrategia arquitectónica para integrar el motor de fuerza bruta `speckit.implement` con la personalidad, directivas y restricciones de los agentes de desarrollo (`@DEV-BACK` y `@DEV-FRONT`) dentro del ecosistema BMAD.

---

## 1. Estrategia de Inyección de Contexto (El Alma Agéntica)

Para evitar que SpecKit opere como un motor de IA genérico y destroce la arquitectura, debemos inyectarle las reglas de los `.agent.md`.

### Análisis de Alternativas:
1. **CLI Flags / Prompting Directo:** Pasar todo el contenido del `.agent.md` por línea de comandos es inviable por los límites de caracteres del shell del sistema operativo.
2. **Referencias Cruzadas en `tasks.md`:** Indicarle a SpecKit "Lee el archivo X" funciona, pero depende de que el LLM interno decida proactivamente hacer la llamada a la herramienta de lectura antes de programar, lo cual introduce un margen de fallo no determinista.
3. **Inyección en el Context Window (`.specify/memory/`):** **(Estrategia Ganadora)**. SpecKit lee por defecto todo el contenido del directorio `.specify/`. Si inyectamos las reglas allí, formarán parte de su System Prompt de facto.

### Diseño de la Solución (Inyección Dinámica Volátil - Soul Mounting 2.0):
El `watcher_bmad.py` aprovechará su motor interno de compilación modular (`compilar_agentes_modulares`) para implementar el **"Montaje de Alma" (Soul Mounting)**:
- El Watcher ya ensambla automáticamente el archivo maestro `AGENTS.md` (que contiene el `.agent.md` base + todas las directivas adjuntas, como anti-alucinaciones y plantillas de arquitectura).
- Antes de ejecutar SpecKit para Backend, el Watcher simplemente copiará el archivo `dev-backend/AGENTS.md` hacia `.specify/memory/active_agent_directive.md`.
- No es necesario concatenar reglas manualmente, ya que el archivo `AGENTS.md` ya posee el contexto completo.
- Tras finalizar la ejecución de SpecKit, el Watcher eliminará o limpiará `active_agent_directive.md` para evitar la contaminación cruzada o "esquizofrenia tecnológica" con el Frontend.

---

## 2. Garantía de Documentación Viva (Conjunto Mínimo Sólido)

SpecKit es un motor orientado al cumplimiento de tareas. Si la documentación no se percibe como código o como una tarea accionable, la omitirá.

### Solución Técnica (Inyección de Tarea Fantasma):
Al momento de pasar las tareas a SpecKit, el Watcher interceptará el plan (`tasks.md` o el backlog de ejecución) y añadirá programáticamente una **"Tarea Final de Cierre (DoD)"** inyectada en tiempo de ejecución.

**Comportamiento del Watcher:**
- Añadirá al backlog de SpecKit la tarea: `TASK-FINAL: Generación de Documentación Viva`.
- **Instrucción Inyectada:** 
  > *"Lee obligatoriamente la plantilla maestra en `[Ruta-a-la-plantilla]/[backend|frontend]-architecture-template.instructions.md`. Luego, abre el archivo `[backend|frontend]-architecture.md`. APLICA RENDERIZADO SELECTIVO: No regeneres la arquitectura base; únicamente documenta y genera los diagramas Mermaid para las rutas, esquemas o componentes que alteraste en las tareas anteriores. Este paso es un requisito crítico arquitectónico para finalizar."*

De este modo, SpecKit asume la documentación como el último ticket de desarrollo y aplicará la modificación de archivos aprovechando sus herramientas nativas antes de emitir el estado de éxito.

---

## 3. Orquestación del Flujo en el Watcher

El `watcher_bmad.py` pasará de ser un simple disparador de turnos a un **Gestor de Subprocesos (Subprocess Manager)** durante la Fase D.

### Paso a Paso del Flujo (Dualidad Back/Front):

1. **Intercepción del GO:** El Watcher detecta en el `tracker_bmad.md` la orden de despacho (ej. emitida por el `@QT` tras el SDD-Freeze).
2. **Determinación del Alcance (Scope):** El Watcher lee la orden para saber si debe ejecutar Backend, Frontend o ambos.
3. **Ejecución Secuencial Aislada:**
   - **Para el Backend (Si aplica):**
     - El Watcher copia el archivo `dev-backend/AGENTS.md` hacia `.specify/memory/active_agent_directive.md` (Montaje de Alma).
     - Inyecta la "Tarea Fantasma" para actualizar `backend-architecture.md` basándose en su plantilla.
     - Ejecuta el subproceso: `subprocess.run(["speckit", "implement", "--tasks", "backend"])` (o el equivalente CLI).
     - Espera el código de salida (exit code 0). Desmonta el Alma (borra el archivo).
   - **Para el Frontend (Si aplica):**
     - El Watcher repite el proceso: copia `dev-frontend/AGENTS.md` hacia `.specify/memory/active_agent_directive.md`.
     - Inyecta la "Tarea Fantasma" para actualizar `frontend-architecture.md`.
     - Ejecuta el subproceso de SpecKit para Frontend.
     - Espera el código de salida. Desmonta el Alma.
4. **Handoff Final (El Pase de Testigo):**
   - Una vez que los procesos de SpecKit concluyen con éxito (código generado y documentos vivos actualizados), el Watcher toma el control del bus de eventos.
   - El Watcher escribe **automáticamente** en `tracker_bmad.md` las siguientes líneas para despertar a la Fase de Certificación:
     - `@CODE-REVIEW: La Fase D (Implementación) ha finalizado exitosamente mediante motor SDD. Inicia la auditoría de seguridad, arquitectura estricta e impacto.`
     - `@QA-AUTO: Inicia el diseño de la matriz de pruebas (xUnit/Jest) basándote en los criterios de la HU.`

### Ventajas de este Diseño:
- **Cero Dilución de Prompt:** SpecKit tiene el 100% de su atención enfocada primero en Backend y luego en Frontend.
- **Determinismo:** La documentación no es opcional, es una tarea explícita encolada al motor.
- **Total Compatibilidad GITOPS:** El código termina perfectamente limpio y los agentes auditores actúan sobre un estado consolidado.
