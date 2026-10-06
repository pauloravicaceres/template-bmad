# Quickstart: validación de Gestión de Sprint de Dos Semanas

Guía de validación end-to-end. Contrato en [contracts/sprints-api.openapi.yaml](./contracts/sprints-api.openapi.yaml); modelo en [data-model.md](./data-model.md).

## Prerrequisitos
- .NET 8 SDK, Node.js (Angular 22), Docker (PostgreSQL y Keycloak).
- Variables de entorno o `appsettings.Development.json` con `ConnectionStrings:Database`, configuración de Keycloak y `Database:MigrateOnStartup=true`.

## Preparación
```bash
docker-compose up -d
dotnet build app/backend/TechWorkHub.sln
dotnet run --project app/backend/src/Bootstrapper/Api   # migra el schema `sprints` al arrancar
cd app/frontend && npm start
```
Obtener un token Bearer de Keycloak (mismo procedimiento que HU-001/HU-002) y exportarlo como `TOKEN`.

## Escenarios

| # | Acción | Resultado esperado | Spec |
|---|---|---|---|
| 1 | `POST /api/sprints` `{identification:"Sprint 2026-01", startDate:"2026-10-05", endDate:"2026-10-18"}` | 201, `Location` y cuerpo con 4 campos; fila con `CreatedBy` = `sub` | FR-001/002/006 |
| 2 | Mismo POST con fin a 6, 12, 14 o 20 días del inicio | 400 con mensaje de ventana de 2 semanas; tabla sin filas nuevas | FR-003 |
| 3 | POST con fin ≤ inicio | 400; sin persistencia | FR-004 |
| 4 | POST con identificación vacía, fecha ausente o `"no-es-fecha"` | 400 con `errors` por campo | FR-005 |
| 5 | `GET /api/sprints` con Sprints creados | 200 con exactamente los registrados | FR-007 |
| 6 | `GET /api/sprints/{id}` existente / inexistente | 200 / 404 | FR-008/009 |
| 7 | Las tres operaciones sin token | 401 sin leer ni persistir | FR-010 |
| 8 | Insertar por SQL una fila de 13 o 15 días | Rechazada por `CK_Sprints_Window` | FR-015 |
| 9 | Tras crear un Sprint, revisar `backlog."BacklogItems"` | Sin cambios | FR-013 |
| 10 | Con 100 Sprints sembrados, listar y consultar detalle | < 2 s | SC-005 |
| 11 | UI: `/sprints/nuevo` → crear → redirige a `/sprints` y lo muestra | Sprint visible tras consulta fresca | SC-001 |

## Pruebas automatizadas
```bash
dotnet test app/backend/TechWorkHub.sln          # incluye Sprints.UnitTests y Sprints.IntegrationTests; HU-001/002 sin regresión
cd app/frontend && npm test && npm run build
```

## Criterio de aceptación
Escenarios 1–11 verificados, `dotnet test` y `npm test` en verde, ningún fichero modificado fuera de los permitidos en [plan.md](./plan.md) y sin estado, relación con tarjetas, unicidad ni paginación en el modelo.
