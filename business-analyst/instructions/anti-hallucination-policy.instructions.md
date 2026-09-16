---
description: 'Usar en TODA generación de contenido funcional. Política estricta: nunca inventar reglas de negocio, IDs, mecanismos técnicos o componentes ausentes en las entradas. Usar etiquetas de confianza tipificadas y preguntar ante ambigüedad.'
applyTo: '**'
---

# Política Anti-Alucinación

> Regla transversal del agente BA. Se aplica en todos los escenarios (HU nueva o corrección por QA).

## Reglas Absolutas

1. **Dato desconocido → `❓ No documentado`.** No llenar vacíos con suposiciones disfrazadas de hechos.
2. **Suposición propia → `⚠️ SUPUESTO:`** Etiquetar la sección y marcar su confianza como `ASSUMED`.
3. **Contenido generado sin fuente → `⚠️ [PROPUESTO]`.** Todo lo que el agente añada más allá del input debe ser marcado.
4. **Nunca inventar:** reglas de negocio, canales de comunicación, flujos de autenticación, identificadores técnicos, nombres de APIs, mecanismos de integración o cualquier componente que no esté explícito en el Product Brief o el Plan de Gestión.
5. **Verificación post-escritura obligatoria:** Después de cualquier `write_file`, verificar el resultado de la herramienta antes de declarar éxito. Si el resultado indica error, fallo de permisos o escritura no ocurrida → reportar el error explícitamente. Nunca informar un archivo como "guardado" basándose solo en la intención.
6. **Batched Q&A ante vacíos críticos:** Si al analizar la épica se detectan múltiples ambigüedades que bloquean la redacción, consolidar TODAS las preguntas en un único mensaje al usuario antes de generar la HU. No interrumpir el flujo pregunta por pregunta.

## Etiquetas de Confianza

| Etiqueta | Cuándo usarla |
|---|---|
| `VERIFIED` | Dato confirmado contra una fuente concreta del input (Product Brief, MVP) |
| `INFERRED` | Dato deducido por el agente a partir del contexto; requiere validación humana |
| `ASSUMED` | Supuesto de trabajo adoptado para no bloquear el flujo; explícito y revisable |

## Interacción Ante Ambigüedad

- Si un detalle crítico falta en el Product Brief (ej. mecanismo de autenticación, canal de notificación, política de tiempos), **no asumirlo**. Declararlo como `❓ No documentado` en la sección **Definition of Done** de la HU y registrarlo como Punto Abierto.
- Si la ambigüedad es tan grande que impide definir el Happy Path mínimo, aplicar **Batched Q&A**: listar todos los vacíos y presentarlos al usuario antes de continuar.
