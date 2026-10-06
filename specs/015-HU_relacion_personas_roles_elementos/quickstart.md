# Quickstart: validación de la HU-015

Guía de validación de extremo a extremo. Contrato en [contracts/](./contracts/item-assignments-api.openapi.yaml); modelo en [data-model.md](./data-model.md).

## Prerrequisitos
- Docker (PostgreSQL y Keycloak), .NET 8 SDK y Node >= 22.22.3 para el frontend.
- Variables de entorno o `appsettings.Development.json` con `ConnectionStrings:Database` y la configuración de Keycloak (sin credenciales en el repositorio).
- HU-001 (elementos del backlog) y HU-012 (miembros y roles) operativas; deben existir un elemento "item-101" (y opcionalmente "item-102") y los miembros "Ana Torres" (Desarrollo) y "Luis Rojas" (QA).

## Preparación
```text
docker-compose up -d
dotnet build app/backend/TechWorkHub.sln
Database:MigrateOnStartup=true  →  dotnet run --project app/backend/src/Bootstrapper/Api
```
La migración `AddItemAssignments` se aplica en el arranque mediante el `MigrateTeamsModuleAsync` existente y solo crea objetos en el schema `teams`.

## Escenarios (con token válido, salvo el 9)
| # | Acción | Resultado esperado |
|---|---|---|
| 1 | `POST /api/backlog-items/{item-101}/assignees` con `{ memberId: Ana }` | 201, `Location` hacia el GET, cuerpo `{ itemId, memberId, memberName, role: "Desarrollo" }`; fila con `CreatedBy` = `sub`; `devPoints`, `qaPoints`, estado y Sprint del elemento intactos |
| 2 | `POST` con `{ memberId: Luis }` sobre el mismo elemento | 201; la fila de Ana permanece idéntica |
| 3 | `POST` repetido con `{ memberId: Ana }` | 200 con el mismo cuerpo; una sola fila, `CreatedAt`/`CreatedBy` sin cambios |
| 4 | `GET /api/backlog-items/{item-101}/assignees` | 200 con exactamente Ana (Desarrollo) y Luis (QA) |
| 5 | `GET` de un elemento sin responsables | 200 `[]` |
| 6 | Ana asignada a item-101 e item-102; `GET /api/team-members/{Ana}/items` | 200 con exactamente ambos elementos (`id, title, type`) |
| 7 | `POST` con miembro inexistente; con elemento inexistente; con ambos inexistentes | 404 con `detail` de miembro, de elemento y de miembro respectivamente; tabla sin filas nuevas |
| 8 | `POST` con elemento ausente/malformado y con miembro ausente/malformado (4 casos, más `Guid.Empty`) | 400 con `errors.itemId` o `errors.memberId`; tabla sin filas nuevas |
| 9 | Las tres operaciones sin token, con token inválido y con token expirado | 401, sin lectura ni escritura |
| 10 | Forzar fallo de persistencia en el `POST` | 500 ProblemDetails sin traza; sin fila |
| 11 | N solicitudes simultáneas del mismo par | exactamente un 201, el resto 200, una sola fila |
| 12 | `GET /api/backlog-items` | 200 con `[{ id, title, type }]`, sin estimaciones, estado ni Sprint |
| 13 | Comparar `backlog`, `sprints`, `application` y los registros de `TeamMembers` antes y después | Sin cambios (FR-013, FR-014) |

## Pruebas automatizadas
```text
dotnet test app/backend/TechWorkHub.sln          # integración con contenedores en serie
npm test   (en app/frontend)
npm run build (en app/frontend)
```
Comprobaciones adicionales:
- Migración: SQL directo viola `UX_ItemAssignments_ItemId_MemberId` con un segundo par igual, admite el mismo elemento con otro miembro y el mismo miembro con otro elemento, y la FK rechaza un `MemberId` inexistente; `backlog`, `sprints` y `application` no cambian.
- No regresión: suites de HU-001, HU-002, HU-003, HU-004 y HU-012 sin modificaciones; el `POST` de elementos conserva su comportamiento tras añadir `GET /api/backlog-items`.
- UI (manual o Jest): pestaña `Responsables`, rutas `/equipos/responsables` y `/equipos/responsables/miembro`; toasts distintos para 201 y 200; el diálogo conserva el campo no culpable ante 404/400/500 y el rol es de solo lectura.
