# Feature Specification: FEAT-001 - Catálogo de Servicios y Tarifario Parametrizable

**Feature Branch**: `feat/001-HU_catalogo_servicios_tarifario`
**Created**: 2026-10-02
**Status**: `IN-PROGRESS`

---

## User Scenarios & Testing

### User Story 1 - Registro exitoso de servicios y componentes en el catálogo (Priority: P1)

Como Desarrollador Freelance (Administrador de Propuestas Comerciales), quiero registrar un nuevo servicio o componente funcional con su tarifa base y unidad de medida en el catálogo para disponer de un listado estandarizado y reutilizable en la elaboración de cotizaciones.

**Why this priority**: Es la capacidad fundamental (P1) para que el desarrollador pueda definir su oferta comercial. Sin datos en el catálogo, no se pueden realizar búsquedas ni motorizar cotizaciones.

**Independent Test**: Puede probarse completamente realizando una petición `POST /api/v1/servicios` con payload válido (Nombre, Categoría, Unidad de Medida, Tarifa Base) y verificando la persistencia, asignación de ID único, estado activo y respuesta HTTP 201 Created.

**Acceptance Scenarios**:
1. **Given** que el desarrollador freelance se encuentra autenticado en el sistema y el catálogo está disponible para edición, **When** ingresa un servicio con nombre "Desarrollo de API REST", categoría "Web", unidad de medida "Hora" y tarifa base 50.00 en moneda configurable, **Then** el sistema valida la completitud y el formato numérico positivo de la tarifa, persiste el nuevo servicio con un ID único y estado activo, y retorna HTTP 201 Created.
2. **Given** que el desarrollador está en el formulario de registro de servicios, **When** intenta guardar un servicio omitiendo el nombre o ingresando una tarifa base menor o igual a cero (`tarifa <= 0`), **Then** el sistema rechaza la operación antes de la persistencia, retorna un mensaje explícito de las reglas violadas con código HTTP 400 Bad Request, y el estado de la base de datos permanece inmutable.
3. **Given** que existe un servicio registrado en el catálogo con el nombre "Landing Page Básica", **When** el desarrollador intenta registrar un nuevo servicio con el mismo nombre "Landing Page Básica" en la misma categoría, **Then** el sistema detecta la duplicidad de nombre/identificador único, rechaza el registro emitiendo una excepción de duplicidad con código HTTP 409 Conflict y no crea registros duplicados.

---

### User Story 2 - Consulta y filtrado del catálogo de servicios (Priority: P2)

Como Desarrollador Freelance, quiero consultar y filtrar los servicios del catálogo por categoría o estado para encontrar rápidamente los componentes necesarios durante la preparación de una propuesta o cotización.

**Why this priority**: Facilita la reutilización de servicios y agiliza la localización de tarifas al momento de armar presupuestos.

**Independent Test**: Puede probarse mediante una petición `GET /api/v1/servicios` pasando parámetros opcionales `categoria` o `estado` y validando que el cuerpo devuelto corresponda al listado paginado/filtrado con HTTP 200 OK.

**Acceptance Scenarios**:
1. **Given** que existen servicios registrados previamente en el catálogo, **When** el desarrollador consulta el catálogo aplicando un filtro opcional por categoría o estado, **Then** el sistema retorna la lista paginada o completa de servicios coincidentes con sus respectivas tarifas base y unidades de medida con código HTTP 200 OK y el listado ordenado.

---

### Edge Cases

- **Payload incompleto o nulo (CB-01)**: Solicitud sin campos obligatorios. HTTP 400 / `ValidationException`.
- **Tarifa menor o igual a cero (CB-02)**: Intento de guardar `tarifa <= 0`. HTTP 400 / `InvalidTariffException`.
- **Conflicto por duplicidad (CB-03)**: Nombre de servicio duplicado en misma categoría. HTTP 409 / `DuplicateResourceException`.
- **Recurso no encontrado (CB-04)**: ID inexistente en operaciones. HTTP 404 / `NotFoundException`.
- **Falla de persistencia / infraestructura (CB-05)**: Caída de base de datos. HTTP 500 / `InternalServerErrorException`.

---

## Requirements

### Functional Requirements

- **FR-001**: El sistema DEBE permitir registrar servicios y componentes en el catálogo especificando Nombre, Categoría, Unidad de Medida (ej. Hora, Módulo) y Tarifa Base.
- **FR-002**: El sistema DEBE validar que la Tarifa Base sea strictly un valor numérico positivo (`tarifa > 0`).
- **FR-003**: El sistema DEBE prevenir el registro o actualización de servicios con nombres duplicados dentro de la misma categoría.
- **FR-004**: El sistema DEBE permitir consultar y listar los servicios del catálogo con soporte para filtrado por categoría y/o estado.
- **FR-005**: El sistema DEBE asignar un identificador único, estado (activo/inactivo) y marca de auditoría de fecha a cada servicio registrado.
- **FR-006**: El sistema DEBE garantizar integridad referencial y no permitir la eliminación física de servicios vinculados a cotizaciones históricas emitidas.
- **FR-007**: El sistema DEBE permitir definir la moneda por servicio (código ISO de 3 letras, ej. USD, PEN), utilizando USD como valor por defecto si no es especificado.

### Key Entities

- **Servicio/Componente**:
  - `id`: Identificador único (UUID / Auto-incremental).
  - `nombre`: Cadena de texto única por categoría.
  - `descripcion`: Descripción detallada del servicio/componente (Opcional).
  - `categoria`: Categoría del servicio (ej. Web, Móvil, Backend, Frontend).
  - `unidad_medida`: Unidad de cobro/estimación (ej. Hora, Módulo, Proyecto).
  - `tarifa_base`: Valor numérico positivo (`decimal > 0`).
  - `moneda`: Código ISO de 3 letras (ej. USD, PEN). Por defecto: `USD`.
  - `estado`: Estado del registro (`ACTIVO`, `INACTIVO`).
  - `created_at` / `updated_at`: Marcas de tiempo de auditoría.

---

## Success Criteria

- **SC-001**: El registro de un nuevo servicio en el catálogo completa la persistencia en menos de 500 ms.
- **SC-002**: Cobertura del 100% de escenarios BDD mediante pruebas automatizadas de integración/API backend.
- **SC-003**: 0% de registros duplicados en el catálogo gracias al control de unicidad por categoría.
- **SC-004**: Respuestas de error estructuradas con códigos HTTP (400, 409, 404, 500).
