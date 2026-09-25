---
description: 'Plantilla determinista para el artefacto generado por el API Architect (api_[nombre_corto].md). Incluye contratos REST/GraphQL, registro de decisiones (ADR) en formato MADR y orden de delegación hacia el QA Técnico.'
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

## 1. ARCHITECTURE DECISION RECORDS (ADR - Formato MADR)
*(Registro de las decisiones de diseño sobre protocolos, seguridad y estructuras de payload)*

### ADR-01: {{Título de la decisión, ej. Elección del método de Autenticación o formato de Payload}}
- **Estado:** {{ Aceptado | Aceptado (heredado) }}
  > *Regla: Usar "Aceptado (heredado)" si la decisión proviene de files/context/legacy_ecosystem.md. Las decisiones heredadas no requieren alternativas consideradas.*
- **Contexto:** {{Qué requerimiento de negocio, seguridad o limitación del MER motivó la decisión}}.
- **Decisión:** {{Qué patrón de API, verbo HTTP, protocolo o estructura JSON se eligió y por qué en una frase clara y verificable}}.
- **Alternativas Evaluadas (Obligatorio en decisiones nuevas):**
  - **Alternativa A:** {{Opción viable descartada y justificación técnica con argumentos reales}}.
  - **Alternativa B:** {{Opción viable descartada y justificación técnica con argumentos reales}}.
  - *(Exento de alternativas si el estado es Aceptado (heredado))*.
- **Consecuencias:**
  - ✅ **Beneficio / Impacto Positivo:** {{Baja latencia, estandarización o simplicidad}}.
  - ⚠️ **Trade-off / Costo Real:** {{Trade-offs en latencia, tamaño del payload, sobrecarga de serialización o acoplamiento. Prohibido omitir trade-offs reales}}.

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

---

### ⚠️ Directiva de Interfaz para Ecosistemas Preexistentes (Modo Brownfield)
Si existe el archivo `files/context/legacy_ecosystem.md`:
1. **Subordinación Estricta de Interfaz:** Lee el archivo legacy en su totalidad. Los contratos de integración deben subordinarse a los protocolos de comunicación, servicios de red y mecanismos de autenticación especificados en el documento legacy.
2. **Capa de Adaptación y Mapeo de Errores:** Si el sistema preexistente utiliza protocolos específicos, servicios legados o procedimientos almacenados, diseñar los adaptadores necesarios (BFF / Facade) y el mapeo formal de códigos de error hacia respuestas estándar.
3. **ADR Obligatorio de Interfaz Heredada (MADR):** Redactar un ADR justificando la compatibilidad con los protocolos heredados, utilizando el estado `Aceptado (heredado)` sin requerir alternativas consideradas.
4. **Si el archivo NO existe (Modo Greenfield):** Diseña contratos de API estándar basados en el MER y las HUs sin restricciones heredadas.


[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
