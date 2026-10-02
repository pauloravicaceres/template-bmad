# CONTRATO DE INTEGRACIÓN (API): 001-HU_catalogo_servicios_tarifario - Catálogo de Servicios y Tarifario Parametrizable

- **Especificación SDD Base:** `files/business-analyst/001-HU_catalogo_servicios_tarifario.md` (Scenarios SC-01 a SC-04, CB-01 a CB-05)
- **Modelo Base de Datos:** `files/data-architect/db_catalogo_servicios_tarifario.md` (Tabla `servicio`)
- **Fecha de Diseño:** 2026-10-02
- **API Architect:** Agente API Senior BMAD

---

## 1. ARCHITECTURE DECISION RECORDS (ADR - Formato MADR)

### ADR-01: Protocolo de Interfaz RESTful con Payloads JSON Estandarizados
- **Estado:** Aceptado (heredado)
  > *Nota: Proveniente de la Gobernanza Técnica (.specify/memory/constitution.md) y `files/solutions-architect/tech_guidelines.md`.*
- **Contexto:** Se requiere definir contratos de red para la gestión del catálogo de servicios interoperables entre el cliente frontend (`app/frontend/`) y la API backend (`app/backend/`).
- **Decisión:** Adoptar arquitectura REST sobre HTTP/HTTPS utilizando JSON como formato de transporte (`Content-Type: application/json`).
- **Consecuencias:**
  - ✅ **Beneficio / Impacto Positivo:** Amplia compatibilidad, simplicidad de consumo en SPA/móvil y desacoplamiento claro.
  - ⚠️ **Trade-off / Costo Real:** Mayor verbosidad en payloads en comparación con formatos binarios (gRPC/Protobuf).

### ADR-02: Convención de Nomenclatura y Estructura de Respuesta de Error (RFC 7807 / Standard Problem Details)
- **Estado:** Aceptado
- **Contexto:** Mapear los escenarios Sad Path (SC-03, SC-04) y Casos Borde (CB-01 a CB-05) hacia respuestas deterministas que permitan al cliente frontend/UI renderizar los mensajes correspondientes.
- **Decisión:** Estandarizar las respuestas de error usando la estructura JSON de tipo `{ "error": "CODIGO_ERROR", "message": "Descripción clara", "details": [] }`.
- **Alternativas Evaluadas:**
  - **Alternativa A (Respuestas de error genéricas sin código interno):** Descartada por dificultar el manejo de errores en la interfaz de usuario (ej. no diferenciar 400 por payload sintáctico de 400 por tarifa negativa).
- **Consecuencias:**
  - ✅ **Beneficio / Impacto Positivo:** Facilita el parseo automatizado de validaciones y errores de negocio en el cliente.
  - ⚠️ **Trade-off / Costo Real:** Requiere mantener un catálogo estructurado de excepciones customizadas en el backend.

### ADR-03: Paginación y Filtrado Paramétrico en Consulta de Catálogo
- **Estado:** Aceptado
- **Contexto:** El escenario SC-02 requiere consultar y filtrar el catálogo de servicios por categoría o estado operativamente.
- **Decisión:** Exponer parámetros query opcionales `categoria`, `estado`, `page` (default 1) y `limit` (default 20) en el endpoint `GET /api/v1/servicios`.
- **Alternativas Evaluadas:**
  - **Alternativa A (Carga total sin paginación):** Descartada por potenciales problemas de rendimiento y latencia a medida que el catálogo crezca.
- **Consecuencias:**
  - ✅ **Beneficio / Impacto Positivo:** Escalabilidad en la transferencia de datos y consumo eficiente de memoria.
  - ⚠️ **Trade-off / Costo Real:** El cliente debe gestionar la metainformación de paginación (`total`, `page`, `limit`).

---

## 2. ESPECIFICACIONES GLOBALES
- **Autenticación / Autorización:** Bearer Token JWT en Header `Authorization` (`Authorization: Bearer <token>`) ⚠️ [PROPUESTO]
- **Content-Type Requerido:** `application/json`
- **Base URL:** `/api/v1/servicios`

---

## 3. ENDPOINTS DEFINIDOS

### Endpoint 1: `POST /api/v1/servicios`
- **Tarea Spec Kit:** HU-001 (SC-01, SC-03, SC-04 / CB-01, CB-02, CB-03)
- **Propósito Funcional:** Registrar un nuevo servicio o componente funcional en el catálogo con su tarifa base.
- **Request Headers:**
  - `Content-Type`: `application/json`
- **Request Body (Payload JSON):**
```json
{
  "nombre": "Desarrollo de API REST",
  "descripcion": "Creación de endpoints RESTful con FastAPI y Prisma",
  "categoria": "Web",
  "unidad_medida": "Hora",
  "tarifa_base": 50.00,
  "moneda": "USD"
}
```
- **Respuestas (Status Codes):**
  - ✅ **201 Created** (Happy Path - SC-01):
  ```json
  {
    "id": "e4b1a2c3-8d9e-4f0a-b1c2-3d4e5f6a7b8c",
    "nombre": "Desarrollo de API REST",
    "descripcion": "Creación de endpoints RESTful con FastAPI y Prisma",
    "categoria": "Web",
    "unidad_medida": "Hora",
    "tarifa_base": 50.00,
    "moneda": "USD",
    "estado": "ACTIVO",
    "created_at": "2026-10-02T16:31:00Z",
    "updated_at": "2026-10-02T16:31:00Z"
  }
  ```
  - ❌ **400 Bad Request** (Sad Path - SC-03 / CB-01, CB-02):
  ```json
  {
    "error": "BAD_REQUEST",
    "message": "La solicitud contiene errores de validación",
    "details": [
      {
        "field": "tarifa_base",
        "issue": "La tarifa base debe ser un valor numérico mayor a 0"
      }
    ]
  }
  ```
  - ❌ **409 Conflict** (Sad Path - SC-04 / CB-03):
  ```json
  {
    "error": "CONFLICT",
    "message": "Ya existe un servicio registrado con el nombre 'Desarrollo de API REST' en la categoría 'Web'"
  }
  ```

---

### Endpoint 2: `GET /api/v1/servicios`
- **Tarea Spec Kit:** HU-001 (SC-02)
- **Propósito Funcional:** Consultar la lista de servicios del catálogo con filtros opcionales de categoría y estado.
- **Query Parameters:**
  - `categoria` *(opcional, string)*: Filtrar por nombre de categoría (ej. `Web`).
  - `estado` *(opcional, string)*: Filtrar por estado (`ACTIVO` | `INACTIVO`).
  - `page` *(opcional, integer, default: 1)*: Número de página.
  - `limit` *(opcional, integer, default: 20)*: Cantidad de registros por página.
- **Respuestas (Status Codes):**
  - ✅ **200 OK** (Happy Path - SC-02):
  ```json
  {
    "data": [
      {
        "id": "e4b1a2c3-8d9e-4f0a-b1c2-3d4e5f6a7b8c",
        "nombre": "Desarrollo de API REST",
        "descripcion": "Creación de endpoints RESTful con FastAPI y Prisma",
        "categoria": "Web",
        "unidad_medida": "Hora",
        "tarifa_base": 50.00,
        "moneda": "USD",
        "estado": "ACTIVO",
        "created_at": "2026-10-02T16:31:00Z",
        "updated_at": "2026-10-02T16:31:00Z"
      }
    ],
    "pagination": {
      "total": 1,
      "page": 1,
      "limit": 20,
      "total_pages": 1
    }
  }
  ```

---

### Endpoint 3: `GET /api/v1/servicios/{id}`
- **Tarea Spec Kit:** HU-001 (CB-04)
- **Propósito Funcional:** Obtener el detalle de un servicio específico por su identificador UUID.
- **Path Parameters:**
  - `id` *(string, UUID)*: Identificador del servicio.
- **Respuestas (Status Codes):**
  - ✅ **200 OK** (Happy Path):
  ```json
  {
    "id": "e4b1a2c3-8d9e-4f0a-b1c2-3d4e5f6a7b8c",
    "nombre": "Desarrollo de API REST",
    "descripcion": "Creación de endpoints RESTful con FastAPI y Prisma",
    "categoria": "Web",
    "unidad_medida": "Hora",
    "tarifa_base": 50.00,
    "moneda": "USD",
    "estado": "ACTIVO",
    "created_at": "2026-10-02T16:31:00Z",
    "updated_at": "2026-10-02T16:31:00Z"
  }
  ```
  - ❌ **404 Not Found** (Sad Path - CB-04):
  ```json
  {
    "error": "NOT_FOUND",
    "message": "No se encontró el servicio con el ID especificado"
  }
  ```

---

### Endpoint 4: `PUT /api/v1/servicios/{id}`
- **Tarea Spec Kit:** HU-001 (SC-04 / CB-01, CB-02, CB-03, CB-04)
- **Propósito Funcional:** Actualizar los datos de un servicio existente (nombre, descripción, categoría, tarifa, estado).
- **Path Parameters:**
  - `id` *(string, UUID)*: Identificador del servicio a actualizar.
- **Request Body (Payload JSON):**
```json
{
  "nombre": "Desarrollo de API RESTful",
  "descripcion": "Creación de endpoints RESTful optimizados con FastAPI y Prisma",
  "categoria": "Web",
  "unidad_medida": "Hora",
  "tarifa_base": 60.00,
  "moneda": "USD",
  "estado": "ACTIVO"
}
```
- **Respuestas (Status Codes):**
  - ✅ **200 OK** (Happy Path):
  ```json
  {
    "id": "e4b1a2c3-8d9e-4f0a-b1c2-3d4e5f6a7b8c",
    "nombre": "Desarrollo de API RESTful",
    "descripcion": "Creación de endpoints RESTful optimizados con FastAPI y Prisma",
    "categoria": "Web",
    "unidad_medida": "Hora",
    "tarifa_base": 60.00,
    "moneda": "USD",
    "estado": "ACTIVO",
    "created_at": "2026-10-02T16:31:00Z",
    "updated_at": "2026-10-02T16:32:00Z"
  }
  ```
  - ❌ **400 Bad Request** (Validaciones fallidas):
  ```json
  {
    "error": "BAD_REQUEST",
    "message": "La solicitud contiene errores de validación",
    "details": [
      {
        "field": "tarifa_base",
        "issue": "La tarifa base debe ser un valor numérico mayor a 0"
      }
    ]
  }
  ```
  - ❌ **404 Not Found** (CB-04):
  ```json
  {
    "error": "NOT_FOUND",
    "message": "No se encontró el servicio con el ID especificado"
  }
  ```
  - ❌ **409 Conflict** (SC-04 / CB-03):
  ```json
  {
    "error": "CONFLICT",
    "message": "Ya existe otro servicio con el nombre 'Desarrollo de API RESTful' en la categoría 'Web'"
  }
  ```

---

## 4. DEPENDENCIAS BLOQUEANTES
- `Ninguno`

---

## 5. ORDEN DE DELEGACIÓN PARA EL TRACKER

@QT: Los contratos de integración (API) y endpoints para 001-HU_catalogo_servicios_tarifario han sido definidos en api_catalogo_servicios_tarifario.md basados en spec.md y db_catalogo_servicios_tarifario.md. Por favor, procede con la auditoría cruzada y la compilación del Tech Design (TDD).
