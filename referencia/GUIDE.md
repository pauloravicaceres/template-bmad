# ibk-apolo-plugin — Guía de uso

> Esta guía orienta a usuarios de negocio y analistas para iniciar el flujo de definición de producto y avanzar de forma segura por las tres etapas del plugin.

## 1. Requisitos previos

- Python 3 instalado y dependencias del plugin disponibles.
- Conocido el objetivo de la iniciativa o artefacto de entrada.
- Variables de entorno configuradas para Jira, Figma o GitHub cuando se requiere integración real.
- Si el proyecto tiene acceso limitado, seguir en modo degradado y documentar la condición.

## 2. Conceptos clave

| Etapa | Agente que la ejecuta | Acción / qué produce |
|---|---|---|
| Initiative Specification | `ibk-apolo-business-analyst` | Convierte texto libre, CSV, transcripción o documentos en la especificación, validada como `INITIATIVE-SPEC-COMPLETE`. |
| Solution Design Package | `ibk-apolo-system-design-architect` | Resuelve huecos de la Initiative Specification, genera diagramas y diseño, y sella el paquete como `SOLUTION-DESIGN-SEALED`. |
| Delivery Plan | `ibk-apolo-tech-delivery-planner` | Convierte el Solution Design Package sellado en Épica/HU/ET/HAB y los carga a Jira como Delivery Backlog. |

| Término | Significado |
|---|---|
| `Initiative Specification` | Documento de definición inicial de la iniciativa, validado como `INITIATIVE-SPEC-COMPLETE`. |
| `Solution Design Package` | Carpeta de enriquecimiento + diseño (documento + diagramas), validada como `SOLUTION-DESIGN-SEALED`. |
| `Handoff` | Paso entre etapas que valida entrada y salida del artefacto antes de avanzar. |
| `Handoff-hash` | Marca de integridad que ayuda a detectar cambios no autorizados después de generar un artefacto. |

## 3. Uso paso a paso

1. Comienza con el orquestador.
   ```text
   @ibk-apolo-orchestrator iniciar una iniciativa
   ```
   El agente clasifica si la entrada es nueva, una Initiative Specification o un Solution Design Package y delega la tarea correcta.

2. Si la entrada es una nueva iniciativa, el orquestador delega a **Initiative Specification** (`ibk-apolo-business-analyst`).
   - Se recopila el contexto y se produce la especificación.
   - La salida debe validar (estado `INITIATIVE-SPEC-COMPLETE`).

3. Cuando ya existe una Initiative Specification válida, el orquestador delega a **Solution Design Package** (`ibk-apolo-system-design-architect`).
   - Se resuelven huecos, se confirma diseño y se genera el paquete.
   - El cliente valida que el paquete esté sellado antes de pasar a la siguiente etapa.

4. Con un Solution Design Package listo, el orquestador delega a **Delivery Plan** (`ibk-apolo-tech-delivery-planner`).
   - Se generan HU, épicas, subtareas y ET/HAB según el desglose.
   - Se integra con Jira para cargar el trabajo de desarrollo como Delivery Backlog.

5. Revisa el resultado.
   - Confirmar que el estado del artefacto y las incidencias cumplen el criterio de entrada.
   - Si algo falla, corregir antes de avanzar.

## 4. Entrada y salida

**Entrada:** una iniciativa nueva, un documento de contexto, una Initiative Specification previa o un Solution Design Package sellado.

**Salida esperada:**
- Initiative Specification (`ibk-apolo-business-analyst`) → especificación completa y validada.
- Solution Design Package (`ibk-apolo-system-design-architect`) → paquete con diagramas y diseño relevante.
- Delivery Plan (`ibk-apolo-tech-delivery-planner`) → HU/épicas/subtareas y Delivery Backlog cargado en Jira.

## 7. Solución de problemas

| Síntoma | Causa | Solución |
|---|---|---|
| El flujo no avanza | El artefacto no cumple el contrato de handoff | Revisar la validación de entrada/salida y corregir el artefacto |
| Faltan credenciales | Jira/Figma/GitHub no está configurado | Cargar variables de entorno y reintentar |
| Al invocar un subagente (p. ej. sellar **Solution Design Package**, `ibk-apolo-system-design-architect`) aparece `400 invalid_request_body` / "resource not found" antes de que el subagente ejecute cualquier acción | Incidente transitorio del servicio de agentes, no un problema del documento ni del plugin | Reintentar más tarde en el mismo chat (el orquestador reintenta una vez y luego se detiene) o invocar el subagente de la etapa directamente |
| Se detecta degradación | No hay token o servicio no disponible | Continuar en modo reducido y documentar el estado |
| La etapa es ambigua | El usuario no especifica si va a Initiative Specification (`ibk-apolo-business-analyst`), Solution Design Package (`ibk-apolo-system-design-architect`) o Delivery Plan (`ibk-apolo-tech-delivery-planner`) | Preguntar por la etapa actual y luego enrutar |

## 9. Referencias
- Portada → [`README.md`](./README.md)
- Arquitectura → [`ARCHITECTURE.md`](./ARCHITECTURE.md)
- Validador de handoff → [`skills/ibk-apolo-handoff-validator/SKILL.md`](./skills/ibk-apolo-handoff-validator/SKILL.md)
- Orquestador → [`agents/ibk-apolo-orchestrator.agent.md`](./agents/ibk-apolo-orchestrator.agent.md)
