# Modelo de Datos (Fase 1): Pruebas de Integración Keycloak + Catálogo

La historia **no cambia el modelo de producción**. Este documento describe las entidades de producción que la suite lee o escribe y las entidades del entorno de pruebas.

## 1. Entidades de producción utilizadas (solo lectura de modelo)

### Aplicación (`application."Applications"`, `RegisteredApplication`)
| Campo | Tipo | Reglas |
|---|---|---|
| `Id` | `Guid` | Clave; la suite genera el valor. |
| `Name` | `string` (máx. 200) | Orden de listado ascendente por nombre. |

- Creación en la suite: `RegisteredApplication.Create(id, name)` guardada con `ApplicationDbContext` (FR-004).
- Respuesta de listado: `ApplicationSummary(Id, Name)`.

### Ítem de backlog (`backlog."BacklogItems"`, `BacklogItem`)
Campos relevantes para esta historia: `Id`, `Status` (inicial `Backlog`), `ApplicationId` (nullable, resuelto contra el catálogo real), `CreatedBy` (= `sub` del JWT, vía `AuditableEntityInterceptor`).
- Verificación: lectura con `BacklogDbContext` desde un scope nuevo y `AsNoTracking()`.

**Relaciones**: `BacklogItem.ApplicationId` es una referencia lógica entre módulos validada por `IApplicationModuleApi.ExistsAsync`; no hay FK ni JOIN cross-schema.

## 2. Entidades del entorno de pruebas

### Realm principal `techworkhub`
| Elemento | Configuración | Propósito |
|---|---|---|
| Cliente `techworkhub-api` | Recurso destino del claim `aud` | Coincide con `Keycloak:resource` del host. |
| Cliente `techworkhub-tests` | Público; *direct access grants*; *Audience mapper* → `techworkhub-api` | Emite el token **válido**. |
| Cliente `techworkhub-tests-noaud` | Público; *direct access grants*; **sin** audience mapper | Emite el token de **otra audiencia**. |
| Cliente `techworkhub-tests-shortlived` | Como `techworkhub-tests` con `access.token.lifespan=1` | Emite el token **expirado** (tras esperar). |
| Usuario `qa.user` | Habilitado, contraseña de prueba, sin roles | Sujeto (`sub`) de las credenciales; el `sub` se lee del token, no se fija. |

### Realm secundario `techworkhub-other`
Cliente `techworkhub-tests` con *audience mapper* → `techworkhub-api` y usuario `qa.user`. Emite el token de **otro emisor**.

### Credencial de prueba (token JWT)
| Variante | Origen | Resultado esperado en ambas rutas |
|---|---|---|
| Válida | `techworkhub` / `techworkhub-tests` | 200 (listado) / 201 (registro) |
| Ausente | Sin cabecera `Authorization` | 401 |
| Firma alterada | Válida con firma mutada | 401 |
| Expirada | `techworkhub-tests-shortlived` tras vencer `exp` | 401 |
| Otro emisor | `techworkhub-other` | 401 |
| Otra audiencia | `techworkhub-tests-noaud` | 401 |

## 3. Estados y transiciones
Único estado relevante: un ítem creado nace en `Backlog` (FR-006). Sin transiciones en esta historia.

## 4. Reglas de validación verificadas (heredadas de HU-001)
- `applicationId` inexistente → 400 `ProblemDetails` con la clave `ApplicationId` en `errors`; sin persistencia (FR-008).
- Rechazo 401 antes de alcanzar catálogo y persistencia (FR-010): conteos de filas sin cambios.

## 5. Ciclo de vida de los datos de prueba
Contenedores y bases de datos son efímeros: se crean por suite/prueba y se destruyen al terminar; no persiste configuración ni datos (FR-014, SC-005).
