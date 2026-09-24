---
description: 'Plantilla determinista para el artefacto generado por el API Architect (api_[nombre_corto].md). Incluye contratos REST/GraphQL, registro de decisiones (ADR) y orden de delegación hacia el QA Técnico.'
applyTo: '**'
---

# Plantilla de Contratos API y Decisiones (API + ADR)

## Convención de Nombres de Archivo
`api_[nombre_corto].md` (ej. `api_motor_reservas.md`)

## Estructura Canónica Obligatoria

```markdown
# CONTRATO DE INTEGRACIÓN (API): {{TITULO_EPICA}}

- **Modelo Base de Datos:** {{Nombre del archivo db_*.md}}
- **Fecha de Diseño:** {{FECHA_ACTUAL}}
- **API Architect:** Agente API Senior BMAD

---

## 1. ARCHITECTURE DECISION RECORDS (ADR)
*(Registro de las decisiones de diseño sobre protocolos, seguridad y estructuras de payload)*

### ADR-01: {{Título de la decisión, ej. Elección del método de Autenticación o formato de Payload}}
- **Contexto:** {{Qué requerimiento de negocio o limitación del MER motivó la decisión}}.
- **Alternativas Evaluadas (Descartadas):** {{Qué otras opciones se consideraron y por qué se descartaron}}.
- **Decisión:** {{Qué patrón de API, verbo HTTP inusual o estructura JSON se eligió y por qué}}.
- **Consecuencias:** {{Trade-offs en latencia, tamaño del payload o complejidad en el frontend}}.

---

## 2. ESPECIFICACIONES GLOBALES
- **Autenticación:** {{Mecanismo exigido, ej. JWT en Header Authorization}}
- **Base URL:** `/api/v1/{{recurso_principal}}`

---

## 3. ENDPOINTS DEFINIDOS

### Endpoint: `{{VERBO HTTP}} {{RUTA}}`
- **Propósito Funcional:** {{Relación con el Criterio de Aceptación, ej. "Registrar nueva cita"}}
- **Request Headers:**
  - `Content-Type`: `application/json`
- **Request Body (Payload JSON):**
\`\`\`json
{
    "ejemplo_campo": "valor estricto mapeado desde el db_*.md"
}
\`\`\`
- **Respuestas (Status Codes):**
  - ✅ **200 OK** (Happy Path):
  \`\`\`json
  { "id": "uuid", "status": "CONFIRMADA" }
  \`\`\`
  - ❌ **400 Bad Request** (Sad Path - Validaciones Gherkin):
  \`\`\`json
  { "error": "BAD_REQUEST", "message": "El formato del correo es inválido" }
  \`\`\`
  - ❌ **409 Conflict** (Sad Path - Regla de Negocio):
  \`\`\`json
  { "error": "CONFLICT", "message": "El horario seleccionado ya está ocupado" }
  \`\`\`

---

## 4. DEPENDENCIAS BLOQUEANTES
- `⚠️ BLOQUEO:` {{Si el db_*.md omite una tabla necesaria para que la API funcione, regístralo aquí. Si todo está correcto, escribe "Ninguno"}}.

---

## 5. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Instrucción de una sola línea continua para notificar al QA Técnico)*

@QT: Los contratos de integración (API) y endpoints para {{TITULO_EPICA}} han sido definidos en api_{{nombre_corto}}.md. Por favor, procede con la auditoría cruzada contra el modelo de persistencia (db_*.md) y la compilación del Tech Design (TDD).
```

[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
