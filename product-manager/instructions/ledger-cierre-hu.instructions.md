---
description: 'Mantenimiento del Product State Ledger al cerrarse una HU: promoción a ACTIVE antes de asignar la siguiente.'
applyTo: '**'
---

# Ledger al cierre de una HU

Recibes el turno cuando `code-review` cierra una HU (rama fusionada). **Antes de elegir y asignar la siguiente épica**, deja el ledger (`specs/README.md`) coherente con la realidad:

1. **Promociona a `ACTIVE` la fila de la HU recién cerrada.** Una HU fusionada y certificada ya no está `READY-FOR-DEV` ni `IN-PROGRESS`: su funcionalidad es la fuente de verdad actual. Identifica la fila por su columna *Rama* (la que acaba de cerrarse) y cambia solo su columna *Estado*, sin alterar el resto de la fila ni el formato de la tabla (el ledger se parsea de forma automatizada).
2. **Revisa también las HU anteriores:** si alguna fila de una HU ya fusionada sigue en `READY-FOR-DEV` o `IN-PROGRESS`, corrígela a `ACTIVE`.
3. **Descompón cada épica en historias y registra en `BACKLOG` las que falten.** Una épica NO se agota con la primera historia: tener una HU registrada no significa que su alcance esté cubierto. Para cada épica de tu plan (`docs/product-manager/mvp_*.md`) haz esto:
   - Toma las viñetas de su sección "Incluye" y agrúpalas en historias candidatas (una capacidad coherente por historia).
   - Compara con el ledger qué capacidades ya cubre alguna HU. Distingue las HU **funcionales** de las **de calidad derivadas de un riesgo** (p. ej. pruebas de integración contra servicios reales): estas últimas comparten la épica de origen pero **no avanzan** su alcance funcional.
   - Toda capacidad sin cubrir debe tener su fila en `BACKLOG`: numeración consecutiva, nombre `NNN-HU_nombre`, columna *Épica Origen* con el formato `[Pn] Nombre de la épica`, *Qué aporta* tomado de tu plan, *Rama* con `—` hasta que pase a `IN-PROGRESS`. Marca cada fila como propuesta tuya con `⚠️ [PROPUESTO]` en *Qué aporta*: aún no la validó el business analyst.
   - Si una capacidad depende de un punto abierto de negocio de tu plan (los marcados con ❓), regístrala igualmente y anota esa dependencia en *Qué aporta*; no la elijas como siguiente hasta que el humano la resuelva.
   - **No inventes alcance:** usa solo lo que dice tu plan. Esto evita que un revisor concluya "no queda nada" solo porque el ledger tiene pocas filas.
4. **Después** aplica la heurística de selección de `pm-strategic-prioritization` (sección 3.2): elige la siguiente **historia** (no la siguiente épica: puede ser otra porción de la misma épica o la primera de otra). Una épica solo está completa cuando todas sus HU funcionales están `ACTIVE`. Si la elección implica adelantar una porción de otra épica por una dependencia, o hay dos opciones razonables, NO abras rama: entrega un handoff a `@HUMANO:` con opciones numeradas y espera su respuesta.

Usa únicamente los estados del glosario del ledger. Si tras la descomposición no queda ninguna capacidad pendiente en ninguna épica, regístralo en tu bloque con un mensaje informativo y no emitas ninguna macro.
