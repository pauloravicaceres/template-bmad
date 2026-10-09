# Operación BMAD/SDD

Para preparar un proyecto desde cero, sigue la [guía canónica de inicio](SETUP.md). Este documento detalla la operación de las historias una vez preparado el workspace.

Selecciona el workspace en cada comando. La referencia de CLI, configuración, inicio y parada es [bmad_runtime/README.md](bmad_runtime/README.md). Inicializa y revisa los dry-runs antes del arranque; la flota y el watcher se ejecutan en terminales separadas.

## Flujo de una historia

1. Business Storyteller estructura la idea y la entrega a Product Analyst. El Product Brief se revisa mediante una pausa dirigida a `@HUMANO:`.
2. Product Manager prioriza el MVP y selecciona una historia; Business Analyst produce la HU técnica y su versión para stakeholders. QA Documental valida el alcance.
3. El watcher ejecuta `specify` y `clarify`. La carpeta de feature debe coincidir con el identificador de la HU. Una aclaración pendiente mantiene la pausa humana.
4. UX se decide mediante `project_type`, `ux_phase` y el campo `Requiere interfaz: Sí|No` de la HU. `ux_routing.py` calcula la decisión; cuando se omite UX, el flujo pasa a Solutions Architect.
5. Solutions Architect define guidelines y emite `@WATCHER: SDD-FREEZE`. El watcher ejecuta `plan`, `tasks` y `analyze`, verifica el freeze Git y deriva a Data Architect. API Architect interviene si corresponde; QA Tech revisa el diseño.
6. La implementación ejecuta SpecKit con alcance backend y luego frontend, montando sus perfiles. Debe actualizar las arquitecturas de capa y los README en las rutas `code_dirs` del workspace. QA Automation verifica y Code Review revisa la entrega.
7. El rechazo de un revisor activa `analyze → converge → implement` sobre las tareas de corrección. El máximo es dos iteraciones; después se escala al humano. El cierre aprobado permite seleccionar la siguiente HU.

## Handoffs y aprobaciones

El tracker es `handoffs/tracker_bmad.md` en un workspace explícito. Anexa bloques con fecha, autor, hora, artefacto, estado, puntos abiertos y una línea `Handoff`. Usa un único token de destinatario por derivación. Un aviso dirigido al humano debe mencionar otros agentes por nombre, sin tokens que puedan dispararlos.

`utils/approve_step.py --workspace RUTA` permite revisar y aprobar una transición. `utils/response_sa.py --workspace RUTA` captura respuestas estratégicas hasta la línea `FIN` y las anexa para Solutions Architect. Ambos scripts interactivos escriben en el tracker elegido.

Las macros GitOps se escriben como líneas independientes antes del handoff:

```text
@WATCHER: GITOPS-BRANCH-CREATE feat/XXX-HU_nombre
@WATCHER: SDD-FREEZE
@WATCHER: GITOPS-MERGE-CLOSE feat/XXX-HU_nombre
```

Un `@HUMANO:` real pausa el despacho. La macro de cierre independiente evita tratar un aviso final como una nueva solicitud de aprobación. Los avisos informativos del watcher no liberan una pausa humana.

## Seguimiento y recuperación

El dashboard proyecta tracker, entregables, gates, retrabajo y telemetría Git del workspace seleccionado. Su backend se fija a un proyecto por proceso; el frontend debe apuntar a esa API. Consulta sus [README](bmad-control-center/backend/README.md).

| Situación | Acción |
|---|---|
| Proveedor o skill pendiente | Revisar capacidades y cotejar la skill instalada con la fuente; no hay fallback automático |
| ID o ruta incorrectos | Corregir selección y project.json; no se adopta otro proyecto |
| Evento `uncertain` o `in_flight` | Inspeccionar panel, artefactos y SQLite antes del acknowledgement explícito |
| Tracker truncado o modificado | Detener y reconciliar el historial y cursor; no borrar estado para forzar reintentos |
| Agente ocupado | Esperar; la parada controlada no fuerza el cierre de paneles ocupados |
| Cambio de configuración | Reiniciar los procesos afectados; Runtime cachea la configuración |
| Git rechaza una rama | Guardar los cambios propios y revisar staging; no usar checkout forzado |

La aceptación de un comando por Herdr y el estado idle/done requieren comprobar el artefacto y el handoff. La rotación automática de contexto no está habilitada. La inspección y acknowledgement del estado se describen en el contrato del runtime.
