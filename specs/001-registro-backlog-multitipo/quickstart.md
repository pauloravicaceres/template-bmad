# Gua de Validacin Rápida (Quickstart)

Este documento detalla los escenarios ejecutables para validar el funcionamiento End-to-End del registro de elementos de Backlog de acuerdo a los Acceptance Scenarios de la especificacin.

## Requisitos Previos

- El entorno de la aplicacin `.NET 8/10 Modulith` debe estar en ejecucin (ej: `dotnet run` o `docker compose up`).
- La instancia de Keycloak (puerto `9090`) debe estar levantada.
- La base de datos PostgreSQL debe tener migraciones aplicadas (`BacklogItems` schema configurado).
- Contar con un Token JWT de prueba vlido (`$JWT_TOKEN`). Puedes obtenerlo invocando a Keycloak usando las credenciales de prueba.

## Setup del Entorno de Prueba (Bash)

```bash
# Variables de Entorno
export API_URL="http://localhost:5000/api"
export JWT_TOKEN="eyJhbGciOiJIUzI1..." # Sustituir por token vlido
export TEST_APP_ID="3fa85f64-5717-4562-b3fc-2c963f66afa6" # Asegurar que existe en base de datos de Apps
```

## Escenarios de Prueba (cURL)

### 1. Happy Path: Registro de Historia de Usuario (US 1)

**Objetivo:** Verificar la creacin de un tem con estimaciones para Dev y QA.

```bash
curl -X POST "$API_URL/backlog/items" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Configurar integracin con pago",
    "description": "El usuario debe poder pagar con tarjeta.",
    "type": "UserStory",
    "devPoints": 5,
    "qaPoints": 3,
    "applicationId": "'$TEST_APP_ID'"
  }' -v
```

**Resultado Esperado:** HTTP `201 Created` y un JSON con el identificador (`{"id": "..."}`).

---

### 2. Elemento Tcnico sin Estimacin de QA (US 2)

**Objetivo:** Crear una investigacin preliminar o Spike que no requiere QA.

```bash
curl -X POST "$API_URL/backlog/items" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Investigar migracin a .NET 10",
    "description": "Revisar breaking changes del marco.",
    "type": "Spike",
    "devPoints": 2,
    "qaPoints": null
  }' -v
```

**Resultado Esperado:** HTTP `201 Created`. `qaPoints` se habr almacenado internamente como `null`.

---

### 3. Error por Ttulo Invlido (Edge Case)

**Objetivo:** Verificar las validaciones de negocio en los comandos HTTP (400).

```bash
curl -X POST "$API_URL/backlog/items" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "", 
    "type": "UserStory"
  }' -v
```

**Resultado Esperado:** HTTP `400 Bad Request` informando en la respuesta de validacin que el campo `Title` no puede estar vaco.

---

### 4. Error por Tipo Desconocido (Edge Case)

**Objetivo:** Rechazar elementos con `type` fuera de catlogo.

```bash
curl -X POST "$API_URL/backlog/items" \
  -H "Authorization: Bearer $JWT_TOKEN" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Algo",
    "type": "FormatoInvalido"
  }' -v
```

**Resultado Esperado:** HTTP `400 Bad Request`.

---

### 5. Intento sin Token (Edge Case)

**Objetivo:** Validar reglas de seguridad del endpoint.

```bash
curl -X POST "$API_URL/backlog/items" \
  -H "Content-Type: application/json" \
  -d '{
    "title": "Historia Oculta",
    "type": "UserStory"
  }' -v
```

**Resultado Esperado:** HTTP `401 Unauthorized`.
