# Contratos de API: Registro de Elementos de Backlog

Este documento describe la interfaz expuesta para la creación de un ítem de backlog. El diseño sigue REST con esquemas JSON, expuesto bajo Carter Minimal APIs en .NET. Codificación del archivo: UTF-8.

## Endpoint: Crear Elemento de Backlog

**Ruta:** `POST /api/backlog/items`
**Seguridad:** Requiere Token Bearer (JWT) validado contra Keycloak (Rol requerido: Usuario Autenticado / Líder Técnico). El claim de identidad (`sub`) es obligatorio: sin él la petición se rechaza con HTTP 401 (FR-009).
**Content-Type:** `application/json`

### Request Body (Carga útil)

```json
{
  "title": "Configuración de CI/CD para el monolito",
  "description": "Establecer pipelines de build y test automatizados usando GitHub Actions.",
  "type": "TechRequirement",
  "priority": "High",
  "acceptanceCriteria": "El pipeline ejecuta build y pruebas en cada pull request.",
  "devPoints": 5.0,
  "qaPoints": null,
  "applicationId": "3fa85f64-5717-4562-b3fc-2c963f66afa6"
}
```

| Campo | Tipo JSON | Requerido | Restricciones |
|-------|-----------|-----------|---------------|
| `title` | `string` | Sí | No vacío, máximo 200 caracteres (FR-004). |
| `description` | `string` | No | Máximo 4000 caracteres (FR-012). |
| `type` | `string` | Sí | Valores permitidos: `UserStory`, `Bug`, `TechEvolution`, `TechRequirement`, `TechDebt`, `Research`, `Spike` (FR-005). Insensible a mayúsculas. |
| `priority` | `string` | Sí | Valores permitidos: `Low`, `Medium`, `High`, `Critical`. Se serializa como texto (FR-011); el servidor también acepta el entero equivalente (1 a 4) por compatibilidad. |
| `acceptanceCriteria` | `string` | No | Máximo 4000 caracteres (FR-012). |
| `devPoints` | `number` (decimal) | No | Debe ser >= 0 (FR-006). Ausente o `null` = no estimado. |
| `qaPoints` | `number` (decimal) | No | Debe ser >= 0 (FR-006). Ausente o `null` = no estimado. **Política (FR-008):** para los tipos técnicos (`TechEvolution`, `TechRequirement`, `TechDebt`, `Research`, `Spike`) debe ser nulo; si llega con valor, la petición se rechaza con HTTP 400 (no se descarta en silencio). Para `UserStory` y `Bug` el cliente no debe enviar `0` como valor por defecto. |
| `applicationId` | `string (UUID)` | No | Debe ser el UUID de una Aplicación existente (FR-007); si no existe se responde HTTP 400 con la clave `ApplicationId` en `errors`. |

Estado inicial: todo ítem se crea con estado `Backlog` (FR-003); el cliente no puede enviarlo.

### Respuestas (Responses)

#### 201 Created

Operación exitosa. El elemento fue persistido correctamente en base de datos y el evento de dominio `BacklogItemCreatedDomainEvent` se publicó antes de confirmar la transacción.
**Cabeceras:** `Location: /api/backlog/items/{id}`

```json
{
  "id": "123e4567-e89b-12d3-a456-426614174000"
}
```

#### 400 Bad Request

Todo HTTP 400 usa el formato `ProblemDetails` (`application/problem+json`) con el diccionario `errors` por campo (FR-013). Las claves de `errors` son los nombres de propiedad del comando (`Title`, `Type`, `Priority`, `DevPoints`, `QAPoints`, `ApplicationId`, `Description`, `AcceptanceCriteria`) o `Request` para errores generales (por ejemplo, JSON malformado). El cliente debe leer `errors` para mostrar el error específico por campo.

```json
{
  "type": "https://tools.ietf.org/html/rfc7231#section-6.5.1",
  "title": "One or more validation errors occurred.",
  "status": 400,
  "errors": {
    "Title": [
      "The length of 'Title' must be 200 characters or fewer."
    ],
    "QAPoints": [
      "Los ítems técnicos no admiten puntos de QA."
    ],
    "ApplicationId": [
      "The specified Application does not exist."
    ]
  }
}
```

Causas: validación estructural (título vacío o largo, tipo o prioridad fuera del catálogo, puntos negativos, textos que exceden el límite), `qaPoints` con valor en un tipo técnico y `applicationId` inexistente.

#### 401 Unauthorized

Petición realizada sin token JWT, con un token inválido / expirado, o con un token sin el claim de identidad (`sub`).

#### 500 Internal Server Error

Error inesperado durante la persistencia o la emisión del evento de dominio. Se responde `ProblemDetails` sin detalles internos.

## Endpoint: Listar Aplicaciones

**Ruta:** `GET /api/applications`
**Seguridad:** Requiere Token Bearer (JWT) validado contra Keycloak; sin token, HTTP 401.

#### 200 OK

Catálogo de aplicaciones para el selector de `applicationId`, leído a través de `IApplicationModuleApi`.

```json
[
  { "id": "3fa85f64-5717-4562-b3fc-2c963f66afa6", "name": "Portal Clientes" }
]
```

#### 401 Unauthorized

Sin token, con token inválido/expirado o sin claim `sub`.
