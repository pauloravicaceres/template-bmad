---
description: Etiquetado obligatorio de cada hallazgo rechazado por su CAPA de origen (ciclo de retrabajo SDD).
applyTo: "**"
---

# Etiquetado de hallazgos por capa (Retrabajo SDD)

Cuando tu dictamen sea **[RECHAZADO]**, el Watcher no manda el rechazo directamente a programar: lo clasifica por la **capa de origen** y corrige desde ahí hacia abajo (spec → plan → tasks → código) con `/speckit-converge` y `/speckit-implement`. Para poder enrutarlo, **cada hallazgo debe llevar su etiqueta**:

| Etiqueta | Cuándo usarla | Ejemplo |
|---|---|---|
| `[CAPA:SPEC]` | El contrato o requisito de `spec.md` está errado, ambiguo o contradice otro artefacto. | `priority` es string en el contrato pero enum INT en el modelo. |
| `[CAPA:PLAN]` | El diseño técnico de `plan.md` está incompleto: falta una pieza que el código necesita. | No hay DbContext ni DI definidos para el slice. |
| `[CAPA:TASKS]` | Una tarea de `tasks.md` está marcada `[X]` sin cumplirse, o falta una tarea necesaria. | T018 marcada `[X]` con el interceptor vacío. |
| `[CAPA:CODE]` | La spec y el plan son correctos y el código no los cumple. | Falta `CancellationToken` en `mediator.Send`. |

## Reglas
1. Formato de cada hallazgo en el campo `Estado`: `(n) [CAPA:XXX] descripción breve con archivo:línea`.
2. En el `Handoff`, asigna cada grupo de hallazgos con su token (`@DEV-BACK:` servidor, `@DEV-FRONT:` interfaz, `@QA-AUTO:` pruebas) conservando las etiquetas.
3. Si un hallazgo viola un principio de `.specify/memory/constitution.md`, etiquétalo `[CAPA:CODE]` y cita el principio: **la constitución es el árbitro**. Si la constitución es ambigua, dilo explícitamente para que se enmiende con `/speckit-constitution`.
4. Ante la duda entre `CODE` y una capa superior, elige la capa **superior**: corregir solo el código sin actualizar la spec reintroduce el defecto en la próxima regeneración.
5. No marques como aprobado nada que no hayas verificado leyendo el código; un `[X]` en `tasks.md` no es evidencia.
6. **Nunca escribas una macro del Watcher dentro de una frase** (`@WATCHER: GITOPS-MERGE-CLOSE <rama>`, `GITOPS-BRANCH-CREATE`, `SDD-FREEZE`). El Watcher la ejecuta de verdad al verla, aunque sea una cita: así se cerró y fusionó una rama sin que nadie lo pidiera. Para hablar de ella usa palabras ("la macro de cierre de rama"). Solo se emite como línea independiente cuando realmente quieras ejecutarla.
7. **Un Handoff nombra a un solo agente destinatario por línea** con su token (`@AGENTE:`). Las referencias a otros agentes van como texto plano, sin `@`.
8. **`@HUMANO:` es solo para PREGUNTAS reales** que el humano debe contestar, con las preguntas numeradas debajo. Nunca lo uses como aviso o notificación de cierre: pausa el watcher y deja la etapa en "POR APROBAR".
9. **Cierre de una HU (dictamen APROBADO y macro de cierre de rama emitida): el Handoff va al `@PM:`**, no al humano. Antes de decidir a quién entregar el turno NO te bases solo en las filas en BACKLOG del ledger (`specs/README.md`): el ledger solo contiene las historias que el PM ya registró. Abre el plan del PM (`documents/product-manager/mvp_*.md`) y compara sus épicas (P1..Pn) con el ledger: si queda alguna épica sin historia registrada, o una épica con alcance pendiente, entrega el turno al `@PM:` indicando cuáles. Solo si TODAS las épicas del plan están cubiertas puedes cerrar el ciclo sin PM, y en ese caso hazlo con un bloque informativo sin ningún token de despacho, no con `@HUMANO:`. Decidir cuál es la siguiente historia le corresponde al PM, no a ti.
