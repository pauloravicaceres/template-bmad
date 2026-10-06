# Quickstart de Validación: Pruebas de Integración Keycloak + Catálogo

Guía para comprobar que la feature funciona de extremo a extremo. Detalle de datos en [data-model.md](./data-model.md); contratos en [contracts/test-contract.md](./contracts/test-contract.md).

## Prerrequisitos
- .NET SDK 8 o superior (la solución usa `net8.0`).
- Demonio Docker activo. Primera ejecución: descarga de `quay.io/keycloak/keycloak:24.0` y `postgres:16-alpine` (varios minutos).
- No se requiere `docker-compose`, base de datos local ni Keycloak preinstalado.
- Opcional: `IDENTITY_TESTS_STARTUP_TIMEOUT_SECONDS` (por defecto 120) para equipos lentos.

## Escenario 1 — Ejecución completa con un solo comando (SC-006)
```powershell
dotnet test app/backend/TechWorkHub.sln
```
**Esperado**: todas las pruebas de `Identity.IntegrationTests` en verde: listado (200), registro exitoso (201 con `CreatedBy == sub`), aplicación inexistente (400) y las 10 combinaciones de credencial inválida (401).

## Escenario 2 — Solo esta suite
```powershell
dotnet test app/backend/tests/Integration/Identity/Identity.IntegrationTests.csproj
```
**Esperado**: mismo resultado; arranque de Keycloak de decenas de segundos una sola vez por ejecución.

## Escenario 3 — Idempotencia (SC-005, FR-014)
Ejecutar el escenario 2 dos veces seguidas.
**Esperado**: mismo resultado en ambas; `docker ps -a` no muestra contenedores residuales de Testcontainers al terminar.

## Escenario 4 — Fallo explícito sin Docker (CB-05)
Detener Docker y ejecutar el escenario 2.
**Esperado**: la suite **falla** con un mensaje que nombra el componente que no arrancó; no se omite ni se marca como aprobada.

## Escenario 5 — Ausencia de simulados (SC-002, FR-012)
```powershell
rg -n "TestAuthHandler|FakeApplicationCatalog|RemoveAll<|Skip\s*=|SkippableFact|Backlog\.IntegrationTests" app/backend/tests/Integration/Identity
```
**Esperado**: sin coincidencias.

## Escenario 6 — Producción intacta (FR-013)
```powershell
git diff --stat main -- app/backend/src
```
**Esperado**: sin cambios en `app/backend/src/**`.

## Escenario 7 — La prueba puede fallar (anti-tautología)
Comprobación manual puntual: en el realm de prueba, quitar el *audience mapper* del cliente `techworkhub-tests` y ejecutar la suite.
**Esperado**: las pruebas de camino feliz fallan con 401; restaurar el realm después.
