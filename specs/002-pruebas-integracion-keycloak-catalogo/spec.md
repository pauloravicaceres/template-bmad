# Feature Specification: Pruebas de Integración contra Keycloak Real y Catálogo Real del Módulo Application

**Feature Branch**: `feat/002-HU_pruebas_integracion_keycloak_y_catalogo_application`

**Created**: 2026-10-03

**Status**: 🔗 Consolidado en specs/README.md (Product State Ledger)

**Input**: User description: "documents/business-analyst/002-HU_pruebas_integracion_keycloak_y_catalogo_application.md"

## User Scenarios & Testing *(mandatory)*

### User Story 1 - Consulta del catálogo de aplicaciones con identidad real (Priority: P1)

Como Líder Técnico o miembro del equipo de Desarrollo/QA responsable de la calidad del backlog multitipo, quiero que la suite de integración obtenga una credencial emitida por un servidor de identidad real y consulte con ella el catálogo real de aplicaciones, sin sustitutos de prueba, para tener evidencia automatizada de que autenticación y catálogo funcionan de extremo a extremo.

**Why this priority**: Es la verificación base que cierra el riesgo residual aceptado en HU-001 (identidad y catálogo simulados). Sin ella, el resto de escenarios no tiene fundamento.

**Independent Test**: Se prueba creando aplicaciones de prueba en el catálogo, obteniendo una credencial válida del servidor de identidad real y consultando el listado de aplicaciones; entrega por sí sola la evidencia de integración de lectura.

**Acceptance Scenarios**:

1. **Given** aplicaciones de prueba creadas por la suite y una credencial válida emitida por el servidor de identidad real, **When** el cliente solicita el listado de aplicaciones (`GET /api/applications`) con dicha credencial, **Then** el sistema responde HTTP 200 con exactamente las aplicaciones creadas, cada una con `id` y `name`, ordenadas por nombre.
2. **Given** el mismo escenario, **When** se inspecciona el origen de la respuesta, **Then** esta proviene de la implementación real del módulo Application (no de un catálogo simulado).

---

### User Story 2 - Registro de un ítem de backlog referenciando una aplicación real (Priority: P1)

Como responsable de la calidad del backlog, quiero verificar que registrar un ítem con una aplicación existente en el catálogo real resuelve la referencia contra dicho catálogo y conserva la identidad real del usuario como autor.

**Why this priority**: Verifica el único punto de HU-001 donde confluyen identidad y catálogo; es el flujo de negocio que se quiere proteger.

**Independent Test**: Se prueba enviando `POST /api/backlog/items` con una credencial real y el identificador de una aplicación de prueba existente, y comprobando el ítem persistido.

**Acceptance Scenarios**:

1. **Given** una credencial válida del servidor de identidad real y una aplicación de prueba existente con identificador conocido, **When** el cliente envía `POST /api/backlog/items` con ese `applicationId` y un payload válido de HU-001, **Then** el sistema responde HTTP 201 con estado inicial `Backlog`.
2. **Given** el escenario anterior, **When** se revisa el ítem persistido, **Then** `CreatedBy` es igual al identificador del sujeto (`sub`) de la credencial emitida por el servidor de identidad real, y la existencia de la aplicación se resolvió contra el catálogo real.
3. **Given** una credencial válida y un `applicationId` que no existe en el catálogo, **When** el cliente envía `POST /api/backlog/items`, **Then** el sistema responde HTTP 400 indicando que la aplicación referenciada no existe y no se persiste ningún ítem.

---

### User Story 3 - Rechazo de credenciales inválidas por el servidor de identidad real (Priority: P2)

Como responsable de la calidad del backlog, quiero verificar que credenciales ausentes, alteradas, vencidas, de otro emisor o de otra audiencia son rechazadas tanto al consultar el catálogo como al registrar ítems.

**Why this priority**: Protege la seguridad de los dos puntos de entrada que consumen identidad; es crítico pero se apoya en la infraestructura de las historias anteriores.

**Independent Test**: Se prueba enviando, a ambas rutas, cada tipo de credencial inválida y verificando HTTP 401 sin efectos sobre el catálogo ni la persistencia.

**Acceptance Scenarios**:

1. **Given** la API configurada con la validación de identidad de producción y verificación de audiencia activa, **When** el cliente solicita `GET /api/applications` o `POST /api/backlog/items` sin cabecera de autorización, **Then** el sistema responde HTTP 401.
2. **Given** la misma configuración, **When** el cliente usa una credencial con firma alterada, **Then** el sistema responde HTTP 401 en ambas rutas.
3. **Given** la misma configuración, **When** el cliente usa una credencial expirada, **Then** el sistema responde HTTP 401 en ambas rutas.
4. **Given** la misma configuración, **When** el cliente usa una credencial de un emisor distinto al configurado, **Then** el sistema responde HTTP 401 en ambas rutas.
5. **Given** la misma configuración, **When** el cliente usa una credencial emitida por el servidor de identidad real para otra audiencia, **Then** el sistema responde HTTP 401 en ambas rutas.
6. **Given** cualquiera de los rechazos anteriores, **When** se revisa el efecto, **Then** la solicitud no alcanzó el catálogo ni se persistió ningún ítem de backlog.

---

### Edge Cases

- **Credencial vencida emitida por el servidor real**: se rechaza en la autenticación con HTTP 401 antes de llegar a la lógica de negocio.
- **Firma inválida o emisor distinto al configurado**: rechazo inmediato con HTTP 401.
- **Audiencia no esperada**: rechazo por verificación de audiencia con HTTP 401.
- **`applicationId` inexistente en el catálogo real**: HTTP 400 (comportamiento heredado de HU-001), sin persistencia.
- **Servidor de identidad no disponible al iniciar la suite**: la política no está definida en las fuentes; se asume fallo explícito de la suite (ver Assumptions). No se define escenario de aceptación para este caso.

## Requirements *(mandatory)*

### Functional Requirements

- **FR-001**: La suite de integración DEBE ejercitar un servidor de identidad real (emisión y validación de credenciales JWT) en lugar de cualquier esquema de autenticación de prueba.
- **FR-002**: La suite DEBE ejercitar el catálogo real del módulo Application, sin catálogos simulados, sobre una base de datos con las migraciones aplicadas.
- **FR-003**: La API bajo prueba DEBE usar la configuración de autenticación de producción, con verificación de audiencia activa.
- **FR-004**: La suite DEBE crear por sí misma las aplicaciones de prueba que los escenarios requieren en el catálogo.
- **FR-005**: El listado de aplicaciones DEBE responder HTTP 200 a una credencial válida real, devolviendo exactamente las aplicaciones creadas, cada una con `id` y `name`, ordenadas por nombre.
- **FR-006**: El registro de un ítem con una aplicación existente DEBE responder HTTP 201 con estado inicial `Backlog`, resolviendo la existencia de la aplicación contra el catálogo real.
- **FR-007**: El ítem persistido DEBE conservar como `CreatedBy` el identificador de sujeto (`sub`) de la credencial emitida por el servidor de identidad real.
- **FR-008**: El registro con un `applicationId` inexistente DEBE responder HTTP 400 indicando que la aplicación no existe, sin persistir ningún ítem.
- **FR-009**: Ambas rutas (listado de aplicaciones y registro de ítems) DEBEN responder HTTP 401 ante credencial ausente, con firma alterada, expirada, de emisor distinto o de audiencia distinta.
- **FR-010**: Las solicitudes rechazadas con 401 NO DEBEN alcanzar el catálogo ni la persistencia del backlog.
- **FR-011**: Los escenarios de lectura y de rechazo NO DEBEN mutar datos; el escenario de registro exitoso DEBE persistir un único ítem.
- **FR-012**: Ninguna prueba de esta historia DEBE usar el esquema de autenticación de prueba ni el catálogo simulado de HU-001.
- **FR-013**: Esta historia NO DEBE modificar el comportamiento de producción de HU-001 (contratos HTTP, validaciones, estados); solo añade verificación.
- **FR-014**: Las pruebas DEBEN poder ejecutarse repetidamente sin dejar configuración persistente ni datos residuales que afecten ejecuciones posteriores.

### Key Entities *(include if feature involves data)*

- **Credencial de acceso (token JWT)**: Prueba de identidad emitida por el servidor de identidad real; atributos relevantes: sujeto (`sub`), emisor, audiencia, firma y vigencia.
- **Aplicación**: Elemento del catálogo del módulo Application con `id` y `name`; es la referencia que debe existir para registrar un ítem de backlog.
- **Ítem de backlog**: Elemento registrado según HU-001; para esta historia importan su estado inicial `Backlog`, su `applicationId` y su autor `CreatedBy`.
- **Entorno de pruebas de identidad**: Servidor de identidad con realm, cliente y usuario de prueba disponibles para la suite.

## Success Criteria *(mandatory)*

### Measurable Outcomes

- **SC-001**: El 100% de los escenarios de aceptación (listado, registro exitoso, aplicación inexistente y las 10 combinaciones ruta × credencial inválida) se ejecutan de forma automatizada y pasan sin intervención manual.
- **SC-002**: 0 pruebas de la historia dependen de autenticación o catálogo simulados; esto se puede comprobar por revisión de la suite.
- **SC-003**: El 100% de las 10 combinaciones de credencial inválida sobre las dos rutas resultan en rechazo 401 sin efectos en catálogo ni persistencia.
- **SC-004**: El autor registrado del ítem coincide en el 100% de los casos con el sujeto de la credencial real utilizada.
- **SC-005**: Dos ejecuciones consecutivas de la suite completa producen el mismo resultado, sin datos ni configuración residuales.
- **SC-006**: El riesgo residual de HU-001 (identidad y catálogo simulados) queda cerrado con evidencia automatizada que cualquier miembro del equipo puede reproducir con un solo comando de ejecución de pruebas.

## Assumptions

- Los usuarios objetivo son el Líder Técnico, Desarrolladores y Analistas/Ingenieros de QA.
- La semilla reproducible del catálogo como capacidad propia queda **fuera de alcance** y se deriva al Product Manager; aquí las aplicaciones son datos de prueba creados por la propia suite.
- El realm, cliente y usuario de prueba del servidor de identidad no están definidos en las fuentes; se asume que la suite dispone de un servidor de identidad de prueba aprovisionado de forma que no requiera intervención manual (contenedor efímero o equivalente) y que sus valores se definirán en la fase de planificación.
- Política ante servidor de identidad no disponible (CB-05, no documentada): se asume que la suite falla de forma explícita en lugar de omitirse en silencio; a confirmar en planificación.
- HU-001 solo exige una credencial válida con identidad (`sub`); no se verifican roles porque no hay roles documentados para el backlog.
- Los tipos de rechazo adicionales a "ausente" y "expirada" (firma alterada, emisor distinto, otra audiencia) son una propuesta de cobertura.
- Dependencia: HU-001 (`001-HU_registro_elementos_backlog_multitipo`) ya fusionada; su infraestructura de base de datos para pruebas se reutiliza.
- Restricciones de la Constitución: schemas aislados por módulo, sin consultas entre schemas, y Keycloak como proveedor de identidad.
