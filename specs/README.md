# 🗺️ Mapa de Specs (Product State Ledger)

> **Regla de Actualización:** Este archivo es el registro histórico del estado del producto. Las modificaciones a la tabla deben respetar estrictamente el formato Markdown para permitir su parseo automatizado.

### Glosario de Estados Permitidos (Diccionario Finito)
Para mantener el determinismo del *Ledger*, los agentes mutadores y lectores utilizarán estrictamente este conjunto cerrado de estados:
* **`ACTIVE`**: Funcionalidad probada y en producción. Es la fuente de verdad actual.
* **`IN-PROGRESS`**: Spec en diseño activo.
* **`READY-FOR-DEV`**: Diseño técnico aprobado, listo para Fase D.
* **`DRAFT` / `BACKLOG`**: Idea o requerimiento sin refinar; sin diseño técnico ni código asociado.
* **`BLOCKED`**: Avance detenido por falta de definiciones o dependencias externas.
* **`DEPRECATED`**: Funcionalidad completamente obsoleta o reemplazada. Estrictamente prohibido usarla como base.
* **`DEPRECATED-PARTIAL`**: Funcionalidad reemplazada solo parcialmente. Obligatorio consultar las *Notas de Relación* para identificar qué partes siguen vivas.

---

### Registro del Ledger

| N° | Épica Origen | Nombre spec / HU | Qué aporta | Estado | Rama |
|----|--------------|------------------|------------|--------|------|
| 001 | [P1] Planificación y Control de Sprints con Backlog Multitipo | 001-HU_registro_elementos_backlog_multitipo | Registro y tipificación de ítems en backlog multitipo con estimación por rol (Dev/QA) | ACTIVE | feat/001-HU_registro_elementos_backlog_multitipo |
| 002 | [P1] Planificación y Control de Sprints con Backlog Multitipo | 002-HU_pruebas_integracion_keycloak_y_catalogo_application | Cubre el riesgo residual de HU-001: pruebas de integración contra un Keycloak real (emisión y validación de JWT) y contra el catálogo real del módulo Application (`ApplicationModuleApi` y `GET /api/applications` sin dobles), más una semilla del catálogo | ACTIVE | feat/002-HU_pruebas_integracion_keycloak_y_catalogo_application |
| 003 | [P1] Planificación y Control de Sprints con Backlog Multitipo | 003-HU_gestion_sprint_dos_semanas | ⚠️ [PROPUESTO] Crear y gestionar Sprints de 2 semanas: configuración del ciclo (identificación y fechas de inicio y fin acotadas estrictamente a una ventana de 2 semanas) y consulta y seguimiento del Sprint. Sin dependencia de otras épicas; el ciclo de vida (estados, apertura y cierre) queda bloqueado por ❓ reglas de apertura, cierre y estados de un Sprint. Sin dependencias de otras historias; la 004 depende de ella. | ACTIVE | feat/003-HU_gestion_sprint_dos_semanas |
| 004 | [P1] Planificación y Control de Sprints con Backlog Multitipo | 004-HU_asignacion_elementos_sprint | ⚠️ [PROPUESTO] Asignación de elementos del backlog a un Sprint de 2 semanas. Depende de 003 (el Sprint debe existir); sin otros puntos abiertos. | ACTIVE | feat/004-HU_asignacion_elementos_sprint |
| 005 | [P1] Planificación y Control de Sprints con Backlog Multitipo | 005-HU_flujo_estados_backlog | ⚠️ [PROPUESTO] Seguimiento del flujo de estados de las tarjetas. Bloqueada por ❓ catálogo de estados y reglas de transición. | BACKLOG | — |
| 006 | [P1] Planificación y Control de Sprints con Backlog Multitipo | 006-HU_fechas_compromiso_vs_reales | ⚠️ [PROPUESTO] Fechas de compromiso versus fechas reales de las tarjetas. Depende de 004 y del flujo de estados (005). | BACKLOG | — |
| 007 | [P1] Planificación y Control de Sprints con Backlog Multitipo | 007-HU_bloqueos_backlog | ⚠️ [PROPUESTO] Detección y registro de bloqueos de tarjetas. Depende de 005. | BACKLOG | — |
| 008 | [P1] Planificación y Control de Sprints con Backlog Multitipo | 008-HU_retrasos_backlog | ⚠️ [PROPUESTO] Identificación de tarjetas retrasadas. Bloqueada por ❓ definición formal de "Retrasada"; depende de 006. | BACKLOG | — |
| 009 | [P1] Planificación y Control de Sprints con Backlog Multitipo | 009-HU_tarjetas_en_riesgo | ⚠️ [PROPUESTO] Identificación de tarjetas en riesgo. Bloqueada por ❓ definición formal de "En riesgo"; depende de 006. | BACKLOG | — |
| 010 | [P1] Planificación y Control de Sprints con Backlog Multitipo | 010-HU_relaciones_backlog_con_entidades | ⚠️ [PROPUESTO] Relaciones de las tarjetas con personas, actividades, reuniones, incidentes y aplicaciones. Depende de datos de P2, P3, P4 y P5. | BACKLOG | — |
| 011 | [P1] Planificación y Control de Sprints con Backlog Multitipo | 011-HU_historial_eventos_tarjetas | ⚠️ [PROPUESTO] Historial de eventos relevantes de las tarjetas (capacidad transversal Timeline). Depende de 005; implementación técnica a definir en Architecture. | BACKLOG | — |
| 012 | [P2] Gestión de Equipos y Roles Técnicos | 012-HU_miembros_equipo_y_roles_tecnicos | ⚠️ [PROPUESTO] Gestión de miembros del equipo y roles técnicos como datos maestros. Sin dependencia de puntos abiertos. | ACTIVE | feat/012-HU_miembros_equipo_y_roles_tecnicos |
| 013 | [P2] Gestión de Equipos y Roles Técnicos | 013-HU_capacidades_y_asignaciones | ⚠️ [PROPUESTO] Capacidades y asignaciones de las personas. Bloqueada por ❓ modelo de cálculo de capacidad individual y por rol; depende de 012. | BACKLOG | — |
| 014 | [P2] Gestión de Equipos y Roles Técnicos | 014-HU_actividades_y_carga_por_persona | ⚠️ [PROPUESTO] Actividades y carga de trabajo por persona. Depende de 012 y de actividades de P4. | BACKLOG | — |
| 015 | [P2] Gestión de Equipos y Roles Técnicos | 015-HU_relacion_personas_roles_elementos | ⚠️ [PROPUESTO] Relación entre personas, roles y elementos de trabajo. Depende de 012 y de P1. | READY-FOR-DEV | feat/015-HU_relacion_personas_roles_elementos |
| 016 | [P3] Catálogo y Documentación de Aplicaciones | 016-HU_ficha_general_aplicacion | ⚠️ [PROPUESTO] Información general, responsables, equipo relacionado y tecnologías de cada aplicación. Sin dependencia de puntos abiertos; el catálogo base ya existe por HU-002. | BACKLOG | — |
| 017 | [P3] Catálogo y Documentación de Aplicaciones | 017-HU_ambientes_componentes_integraciones | ⚠️ [PROPUESTO] Ambientes, componentes e integraciones de la aplicación. Depende de 016. | BACKLOG | — |
| 018 | [P3] Catálogo y Documentación de Aplicaciones | 018-HU_referencias_repositorios_y_documentacion | ⚠️ [PROPUESTO] Referencias a repositorios y documentación de la aplicación. Bloqueada por ❓ almacenamiento físico vs. referencias externas y ❓ visibilidad/edición; depende de 016. | BACKLOG | — |
| 019 | [P3] Catálogo y Documentación de Aplicaciones | 019-HU_diagramas_arquitectura_aplicacion | ⚠️ [PROPUESTO] Diagramas de arquitectura de la aplicación. Bloqueada por ❓ formatos/tamaño de adjuntos y ❓ visibilidad/edición; depende de 016. | BACKLOG | — |
| 020 | [P3] Catálogo y Documentación de Aplicaciones | 020-HU_contexto_relacionado_aplicacion | ⚠️ [PROPUESTO] Vista de incidentes, actividades, tarjetas y reuniones relacionadas con la aplicación. Depende de 016 y de datos de P1, P4 y P5. | BACKLOG | — |
| 021 | [P4] Gestión de Actividades Operativas e Incidentes Fuera de Sprint | 021-HU_registro_actividades_operativas | ⚠️ [PROPUESTO] Registro de actividades operativas con responsable, fechas, estado, duración y prioridad. Depende de 012 para responsables. | BACKLOG | — |
| 022 | [P4] Gestión de Actividades Operativas e Incidentes Fuera de Sprint | 022-HU_relaciones_actividades_operativas | ⚠️ [PROPUESTO] Relaciones de actividades con aplicaciones, tarjetas, incidentes y reuniones. Depende de 021 y de datos de P1, P3 y P5. | BACKLOG | — |
| 023 | [P4] Gestión de Actividades Operativas e Incidentes Fuera de Sprint | 023-HU_registro_incidentes | ⚠️ [PROPUESTO] Registro de incidentes: reportante, aplicación afectada, fecha y hora, categorización, severidad, estado y responsable. Bloqueada por ❓ flujo de estados de incidentes; depende de 016 y 012. | BACKLOG | — |
| 024 | [P4] Gestión de Actividades Operativas e Incidentes Fuera de Sprint | 024-HU_atencion_y_resolucion_incidentes | ⚠️ [PROPUESTO] Inicio y fin de atención, tiempos de atención y resolución, diagnóstico y solución. Depende de 023; afectada por ❓ flujo de estados de incidentes. | BACKLOG | — |
| 025 | [P4] Gestión de Actividades Operativas e Incidentes Fuera de Sprint | 025-HU_evidencias_adjuntos_incidentes | ⚠️ [PROPUESTO] Evidencias y adjuntos de incidentes. Bloqueada por ❓ tamaño máximo y formatos permitidos; depende de 023. | BACKLOG | — |
| 026 | [P4] Gestión de Actividades Operativas e Incidentes Fuera de Sprint | 026-HU_relaciones_e_historial_incidente | ⚠️ [PROPUESTO] Relaciones del incidente con tarjetas, actividades, reuniones y documentación, e historial del incidente. Depende de 023 y de datos de P1, P3 y P5. | BACKLOG | — |
| 027 | [P5] Reuniones, Acuerdos y Compromisos | 027-HU_registro_reuniones | ⚠️ [PROPUESTO] Registro de reuniones: fecha y hora, participantes, motivo, acta o minuta y adjuntos. Adjuntos bloqueados por ❓ tamaño y formatos; depende de 012. | BACKLOG | — |
| 028 | [P5] Reuniones, Acuerdos y Compromisos | 028-HU_acuerdos_y_compromisos | ⚠️ [PROPUESTO] Acuerdos y compromisos con responsable, fecha compromiso y estado. Bloqueada por ❓ criterio para convertir compromisos en actividades; depende de 027. | BACKLOG | — |
| 029 | [P5] Reuniones, Acuerdos y Compromisos | 029-HU_relaciones_reuniones | ⚠️ [PROPUESTO] Relación de reuniones con elementos del backlog, actividades, incidentes, aplicaciones y Sprints. Depende de 027 y de datos de P1, P3 y P4. | BACKLOG | — |
| 030 | [P5] Reuniones, Acuerdos y Compromisos | 030-HU_timeline_transversal | ⚠️ [PROPUESTO] Timeline cronológico transversal sobre incidentes, aplicaciones y demás elementos (extiende 011). Depende de 011; implementación técnica a definir en Architecture. | BACKLOG | — |
| 031 | [P6] Dashboard Ejecutivo del Líder Técnico | 031-HU_dashboard_estado_sprint | ⚠️ [PROPUESTO] Estado del Sprint activo, distribución de tarjetas por estado y puntos planificados y completados por rol. Depende de 004 y 005. | BACKLOG | — |
| 032 | [P6] Dashboard Ejecutivo del Líder Técnico | 032-HU_dashboard_alertas_retrasos_bloqueos_riesgo | ⚠️ [PROPUESTO] Tarjetas retrasadas, bloqueadas y en riesgo, y alertas relevantes. Bloqueada por ❓ definiciones de "Retrasada" y "En riesgo"; depende de 007, 008 y 009. | BACKLOG | — |
| 033 | [P6] Dashboard Ejecutivo del Líder Técnico | 033-HU_dashboard_trabajo_no_planificado | ⚠️ [PROPUESTO] Trabajo planificado versus no planificado, actividades pendientes y en progreso, incidentes abiertos y atendidos y tiempo invertido en incidentes. Depende de P4. | BACKLOG | — |
| 034 | [P6] Dashboard Ejecutivo del Líder Técnico | 034-HU_dashboard_compromisos_pendientes | ⚠️ [PROPUESTO] Compromisos pendientes de reuniones. Depende de 028. | BACKLOG | — |
| 035 | Deuda Técnica / UI Core | 035-HU_refactorizacion_esqueleto_ui | Layout de aplicación y estructura de páginas y formularios alineados al Skeleton de la Constitución, con PrimeNG 22 nativo | READY-FOR-DEV | feat/035-HU_refactorizacion_esqueleto_ui |

---

## 🔗 Notas de Relación entre Specs
* (Aún no hay relaciones registradas)
