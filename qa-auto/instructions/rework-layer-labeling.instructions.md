---
description: Etiquetado obligatorio de cada defecto rechazado por su CAPA de origen (ciclo de retrabajo SDD).
applyTo: "**"
---

# Etiquetado de defectos por capa (Retrabajo SDD)

Cuando tu dictamen sea **[RECHAZADO]**, el Watcher clasifica el rechazo por la **capa de origen** y corrige desde ahí hacia abajo (spec → plan → tasks → código) con `/speckit-converge` y `/speckit-implement`, y luego te devuelve el turno para revalidar. Para poder enrutarlo, **cada defecto (DEF-xx) debe llevar su etiqueta**:

| Etiqueta | Cuándo usarla |
|---|---|
| `[CAPA:SPEC]` | El criterio de aceptación o contrato de `spec.md` es errado o ambiguo, o dos artefactos se contradicen. |
| `[CAPA:PLAN]` | `plan.md` no define algo que el código necesita (p. ej. composición, DI, módulos expuestos para pruebas). |
| `[CAPA:TASKS]` | Una tarea está marcada `[X]` sin cumplirse, o falta una tarea necesaria. |
| `[CAPA:CODE]` | Spec y plan son correctos y el código no los cumple. |

## Reglas
1. Formato en `Estado`: `DEF-xx [CAPA:XXX] descripción breve y evidencia (comando, archivo, línea)`.
2. En el `Handoff`, asigna los defectos de servidor a `@DEV-BACK:` y los de interfaz a `@DEV-FRONT:`, conservando las etiquetas.
3. Una prueba que falla porque la spec es ambigua **no** se arregla "ajustando la prueba": etiqueta `[CAPA:SPEC]`.
4. Ante la duda entre `CODE` y una capa superior, elige la **superior**.
5. Una tarea `[X]` sin prueba real (`[Fact]` comentado, cero aserciones) es `[CAPA:TASKS]`: el estado terminado lo prueba la verificación, no el checkbox.
6. **Nunca escribas una macro del Watcher dentro de una frase** (`@WATCHER: GITOPS-MERGE-CLOSE <rama>`, `GITOPS-BRANCH-CREATE`, `SDD-FREEZE`): el Watcher la ejecuta al verla, aunque sea una cita. Para hablar de ella usa palabras.
7. **Un Handoff nombra a un solo agente destinatario por línea** con su token (`@AGENTE:`). Las referencias a otros agentes van como texto plano, sin `@`.
