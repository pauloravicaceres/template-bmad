# Fase 4B — Gestión controlada del ciclo de vida de sesiones

Apruebo implementar la Fase 4B del framework BMAD/SDD: CLEAR y ROTATE supervisados por operador, integrados con Herdr, SQLite y el watcher existente.

## Objetivo

Permitir liberar el contexto de agentes Claude Code y Codex CLI de manera segura, sin perder roles, perfiles, estado de tareas, handoffs ni aislamiento entre proyectos.

## 1. Comandos de mantenimiento

Implementa comandos equivalentes a:

```powershell
python -m bmad_runtime.maintenance --workspace <ruta> --plan-clear
python -m bmad_runtime.maintenance --workspace <ruta> --rotate <rol> --confirm
python -m bmad_runtime.maintenance --workspace <ruta> --clear <rol> --confirm
```

El comando `--clear` solo debe estar disponible para Claude Code con capacidad verificada. Para Codex CLI, únicamente ROTATE.

Mantén `--plan-clear` estrictamente en modo de solo lectura.

## 2. Seguridad y coordinación

Antes de cualquier operación:

- Resolver inequívocamente proyecto, workspace, sesión Herdr y agente.
- Exigir confirmación explícita del operador.
- Adquirir un mecanismo de exclusión mutua compartido con el watcher.
- Volver a evaluar la elegibilidad después de adquirir la exclusión.
- Comprobar que no existan tareas pendientes, despachos inciertos, followups activos ni problemas de integridad.
- Rechazar operaciones sobre agentes ocupados, bloqueados o con identidad inconsistente.
- No ejecutar mantenimiento si el watcher no participa en el mecanismo de coordinación.

La exclusión debe funcionar entre procesos independientes y recuperarse de cierres inesperados. Evita bloqueos permanentes y condiciones TOCTOU.

No implementes un segundo orquestador.

## 3. ROTATE

Implementa una máquina de estados persistente:

REQUESTED → QUIESCED → STOPPING → STARTING → VERIFYING → COMPLETED.

Incluye estados FAILED y REQUIRES_INTERVENTION para errores o resultados inciertos.

El procedimiento debe:

1. Confirmar elegibilidad.
2. Guardar un resumen verificable de la sesión anterior.
3. Regenerar el contrato con las fuentes actuales.
4. Enviar `/exit` al agente correspondiente.
5. Verificar que el proceso anterior terminó y que el panel volvió al shell.
6. Relanzar el mismo rol en el workspace correcto.
7. Verificar identidad, rol, perfil y workspace.
8. Incrementar la generación de sesión únicamente después de una verificación exitosa.
9. Liberar la coordinación con el watcher.

Si la operación falla, no declarar éxito ni reintentar ciegamente.

No afectar otros paneles ni agentes.

## 4. CLEAR

Implementa CLEAR exclusivamente para Claude Code.

Procedimiento:

1. Confirmar elegibilidad y capacidad verificada.
2. Persistir el resumen de sesión.
3. Enviar `/clear` mediante el mecanismo validado con Herdr.
4. Confirmar que se reinició el contexto.
5. Recargar explícitamente el perfil y las instrucciones vigentes.
6. Verificar rol, perfil y workspace.
7. Actualizar la generación de sesión solo al confirmar éxito.

Si falla la recuperación, marcar REQUIRES_INTERVENTION.

No realizar ROTATE como fallback automático sin nueva confirmación del operador.

No habilitar CLEAR para Codex.

## 5. Persistencia y recuperación

Reutiliza SQLite y las estructuras existentes.

Registra:

- ID de operación.
- Proyecto y workspace.
- Agente y proveedor.
- Generación anterior y nueva.
- Estado de mantenimiento.
- Fecha y resultado.
- Resumen persistido.
- Evidencia de verificación.
- Errores e incertidumbre.

Después de reiniciar el watcher o el comando de mantenimiento, una operación incompleta debe permanecer visible y bloquear nuevas intervenciones hasta reconciliarse.

## 6. Pruebas

Incluye pruebas de:

- CLEAR exitoso en Claude.
- ROTATE exitoso en Claude y Codex.
- Agente ocupado o bloqueado.
- Handoff pendiente o incierto.
- Tracker inconsistente.
- Dos workspaces independientes.
- Dos mantenimientos concurrentes.
- Reinicio del watcher durante mantenimiento.
- Terminación inesperada del proceso.
- Fallo de `/exit`.
- Fallo de `/clear`.
- Fallo de recuperación del perfil.
- Identidad incorrecta.
- Idempotencia y recuperación desde SQLite.

Ejecuta la regresión completa y validate_offline.py.

## 7. Integración real

Realiza pruebas únicamente en una sesión Herdr aislada y un workspace desechable.

Valida:

- CLEAR de Claude después de un handoff confirmado.
- ROTATE de Claude.
- ROTATE de Codex.
- Ejecución de una nueva tarea después del mantenimiento.
- Persistencia de resúmenes y generaciones.
- Ausencia de duplicaciones y afectación a otros agentes.

No intervengas proyectos activos.

Si una operación requiere aprobar permisos no previstos o modificar controles de seguridad, detente y solicita autorización.

## 8. Restricciones

- No activar mantenimiento automático.
- No cambiar gatekeepers BMAD/SDD.
- No cambiar el formato del tracker.
- No desactivar permisos ni sandbox.
- No introducir módulos redundantes.
- No modificar configuraciones globales.
- No sobrescribir cambios externos.
- No realizar commits sin autorización.
- No continuar con la Fase 4C.

## 9. Entregables

Presenta:

1. Archivos modificados.
2. Máquina de estados implementada.
3. Pruebas y regresión.
4. Evidencia de integración real.
5. Ejemplos de comandos.
6. Riesgos residuales.
7. Procedimiento de recuperación.
8. Procedimiento de reversión.
9. Recomendaciones para la Fase 4C.

**Implementa únicamente la Fase 4B y espera mi aprobación antes de continuar.**