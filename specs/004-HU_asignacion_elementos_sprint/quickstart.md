# Quickstart: validación de la HU-004

Guía de validación de extremo a extremo. Contratos en [contracts/](./contracts/); modelo en [data-model.md](./data-model.md).

## Prerrequisitos
- Docker (PostgreSQL y Keycloak) y .NET 8 SDK; Node >= 22.22.3 para el build del frontend.
- Variables de entorno o `appsettings.Development.json` con `ConnectionStrings:Database` y la configuración de Keycloak (sin credenciales en el repositorio).
- HU-001 (elementos) y HU-003 (Sprints) operativas.

## Preparación
```text
docker-compose up -d
dotnet build app/backend/TechWorkHub.sln
Database:MigrateOnStartup=true  →  dotnet run --project app/backend/src/Bootstrapper/Api
```
La migración `AddSprintItems` se aplica en el arranque y solo crea `sprints."SprintItems"`.

## Escenarios (con token válido, salvo el 5)
| # | Acción | Resultado esperado |
|---|---|---|
| 1 | Crear un Sprint y un elemento; `POST /api/sprints/{sprintId}/items` con `{ "itemId": "<guid>" }` | 201, cuerpo `{ sprintId, itemId }`, `Location` hacia el GET; fila con `CreatedBy` = `sub` |
| 2 | `GET /api/sprints/{sprintId}/items` | 200 con exactamente el elemento (`id, title, type, devPoints, qaPoints`); el elemento conserva sus datos |
| 3 | Asignar un segundo elemento distinto al mismo Sprint | 201; el GET devuelve exactamente dos |
| 4 | GET de un Sprint sin elementos / de un Sprint inexistente | 200 `[]` / 404 |
| 5 | POST y GET sin token o con token inválido | 401, sin lectura ni escritura |
| 6 | POST con Sprint inexistente / elemento inexistente | 404 (el `detail` distingue Sprint de elemento); tabla vacía |
| 7 | POST con `sprintId` o `itemId` ausente, malformado o `Guid.Empty` (4 casos) | 400 con `errors.sprintId` o `errors.itemId`; tabla vacía |
| 8 | Reasignar el mismo elemento al mismo Sprint y a otro Sprint (US3, escenario 4; FR-017) | 409 con el mismo mensaje; una sola fila |
| 9 | Disparar N solicitudes simultáneas del mismo elemento a dos Sprints (US3, escenario 5; FR-017) | Exactamente un 201 y el resto 409; una sola fila |
| 10 | Forzar fallo de persistencia | 500 ProblemDetails sin traza; sin fila |
| 11 | Asignar un elemento con `DevPoints` 2.5 y `QAPoints` nulo y consultar `GET /api/sprints/{sprintId}/items` (FR-018) | `devPoints: 2.5` y `qaPoints: null`; sin redondeo ni `null` convertido a 0 |

## Pruebas automatizadas
```text
dotnet test app/backend/TechWorkHub.sln          # integración de Docker en serie
npm test   (en app/frontend)
npm run build (en app/frontend)
```
Comprobaciones adicionales:
- Prueba de migración: SQL directo viola `UX_SprintItems_ItemId` (también con otro `SprintId`) y la FK a `sprints."Sprints"`; `backlog` y `application` no cambian.
- No regresión: suites de HU-001, HU-002 y HU-003 sin modificaciones; 400, 401, 404 y 500 conservan su formato tras añadir el 409.
- Rendimiento (SC-006): 100 elementos asignados, consulta < 2 s.

## Validación del frontend
1. Abrir `/sprints/{id}`: solo aparece el botón `Elementos asignados` (los cuatro datos del Sprint no cambian).
2. En `/sprints/{id}/elementos`: grilla, estado vacío, diálogo de asignación; tras el éxito el diálogo se cierra y la grilla se consulta de nuevo al servidor.
3. Con 404 de elemento, 409, 400 y 500 el diálogo conserva el valor y muestra el error; el 404 de Sprint bloquea el reintento.
4. La vista no ofrece quitar, mover ni reasignar.
