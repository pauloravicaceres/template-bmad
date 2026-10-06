# Quickstart: validación de la HU-012

Guía de validación de extremo a extremo. Contrato en [contracts/](./contracts/teams-api.openapi.yaml); modelo en [data-model.md](./data-model.md).

## Prerrequisitos
- Docker (PostgreSQL y Keycloak) y .NET 8 SDK; Node >= 22.22.3 para el build del frontend.
- Variables de entorno o `appsettings.Development.json` con `ConnectionStrings:Database` y la configuración de Keycloak (sin credenciales en el repositorio).
- No requiere ninguna HU previa; HU-001 a HU-004 deben seguir operativas sin cambios.

## Preparación
```text
docker-compose up -d
dotnet build app/backend/TechWorkHub.sln
Database:MigrateOnStartup=true  →  dotnet run --project app/backend/src/Bootstrapper/Api
```
La migración `InitialTeamsSchema` se aplica en el arranque y solo crea objetos en el schema `teams` (tablas `TechnicalRoles` y `TeamMembers`, y la semilla de "Desarrollo" y "QA").

## Escenarios (con token válido, salvo el 8)
| # | Acción | Resultado esperado |
|---|---|---|
| 1 | `GET /api/technical-roles` | 200 con al menos "Desarrollo" y "QA", cada uno con `id` y `name` (los GUID de la semilla) |
| 2 | `POST /api/team-members` con `{ "name": "Ana Torres", "role": "Desarrollo" }` | 201, cuerpo `{ id, name, role }`, `Location` hacia el GET; fila con `CreatedBy` = `sub` y `CreatedAt` informado |
| 3 | `POST /api/team-members` con `{ "name": "Luis Rojas", "role": "QA" }` | 201 con `role: "QA"` |
| 4 | `GET /api/team-members` | 200 con exactamente los dos miembros (`id, name, role`), sin `CreatedAt` ni `CreatedBy` |
| 5 | `GET /api/team-members` sin miembros registrados | 200 `[]` |
| 6 | `POST` con rol "Chef" | 400 con el detalle "El rol indicado no es válido."; tabla `TeamMembers` sin filas nuevas |
| 7 | `POST` con nombre ausente, nombre de solo espacios, rol ausente y rol de solo espacios (4 casos) | 400 con `errors.name` o `errors.role`; tabla sin filas nuevas |
| 8 | Las tres operaciones sin token, con token inválido y con token expirado | 401, sin lectura ni escritura |
| 9 | Forzar fallo de persistencia en el `POST` | 500 ProblemDetails sin traza; sin fila |
| 10 | Registrar y comparar los schemas `backlog` y `sprints` antes y después | Sin cambios (FR-014) |

## Pruebas automatizadas
```text
dotnet test app/backend/TechWorkHub.sln          # integración de Docker en serie
npm test   (en app/frontend)
npm run build (en app/frontend)
```
Comprobaciones adicionales:
- Prueba de migración: base vacía → solo objetos del schema `teams`; semilla con exactamente dos roles y GUID fijos; SQL directo viola `UX_TechnicalRoles_Name` y la FK `TeamMembers.TechnicalRoleId`; `backlog`, `sprints` y `application` no cambian.
- No regresión: suites de HU-001 a HU-004 sin modificaciones; 400, 401 y 500 conservan su formato.
- Rendimiento (SC-007): 100 miembros sembrados, ambas consultas < 2 s.

## Validación del frontend
1. Abrir `/equipos`: pestaña Miembros con la grilla (o estado vacío) y botón de registro; `/equipos/roles` abre la pestaña Roles técnicos.
2. Diálogo de registro: el selector se alimenta del catálogo; tras el éxito el diálogo se cierra, aparece el toast con los datos del servidor y la grilla se consulta de nuevo.
3. Con 400 (rol o campos) y 500 el diálogo conserva los valores y muestra el error; el botón se deshabilita durante el envío.
4. Un error de lectura muestra el mensaje genérico con `Reintentar`, sin exponer el cuerpo de la respuesta.
5. La vista no ofrece editar, desactivar ni eliminar miembros ni administrar roles.
