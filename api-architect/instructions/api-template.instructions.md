---
description: 'Plantilla determinista para el artefacto generado por el API Architect (api_[nombre_corto].md). Incluye contratos REST/GraphQL mapeados desde spec.md y tasks.md de Spec Kit, registro de decisiones (ADR) en formato MADR y orden de delegación hacia el QA Técnico.'
applyTo: '**'
---

# Plantilla de Contratos API y Decisiones (API + ADR) — SDD Bridge

## Convención de Nombres de Archivo
`api_[nombre_corto].md` (ej. `api_motor_reservas.md`)

## Estructura Canónica Obligatoria

```markdown
# CONTRATO DE INTEGRACIÓN (API): {{TITULO_EPICA}}

- **Especificación SDD Base:** `spec.md` y `tasks.md` (Spec Kit)
- **Modelo Base de Datos:** {{Nombre del archivo db_*.md}}
- **Fecha de Diseño:** {{FECHA_ACTUAL}}
- **API Architect:** Agente API Senior BMAD

---

## 1. ARCHITECTURE DECISION RECORDS (ADR - Formato MADR)
*(Registro de las decisiones de diseño sobre protocolos, seguridad y estructuras de payload)*

### ADR-01: {{Título de la decisión, ej. Elección del método de Autenticación o formato de Payload}}
- **Estado:** {{ Aceptado | Aceptado (heredado) }}
  > *Regla: Usar "Aceptado (heredado)" si la decisión proviene de files/context/constitution.md o .specify/memory/constitution.md. Las decisiones heredadas no requieren alternativas consideradas.*
- **Contexto:** {{Qué requerimiento de spec.md, seguridad o limitación del MER motivó la decisión}}.
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
*(Mapeo 1 a 1 de endpoints y operaciones requeridas en spec.md y tasks.md)*

### Endpoint: `{{VERBO HTTP}} {{RUTA}}`
- **Tarea Spec Kit:** {{ID de Tarea en tasks.md, ej. Task 2.1: API Endpoints}}
- **Propósito Funcional:** {{Relación con el escenario de spec.md, ej. "Registrar nueva cita"}}
- **Request Headers:**
  - `Content-Type`: `application/json`
- **Request Body (Payload JSON):**
```json
{
    "ejemplo_campo": "valor estricto mapeado desde el db_*.md"
}
```
- **Respuestas (Status Codes):**
  - ✅ **200 OK / 201 Created** (Happy Path):
  ```json
  { "id": "uuid", "status": "CONFIRMADA" }
  ```
  - ❌ **400 Bad Request** (Sad Path - Validaciones Gherkin / spec.md):
  ```json
  { "error": "BAD_REQUEST", "message": "El formato del correo es inválido" }
  ```
  - ❌ **409 Conflict** (Sad Path - Regla de Negocio):
  ```json
  { "error": "CONFLICT", "message": "El horario seleccionado ya está ocupado" }
  ```

---

## 4. DEPENDENCIAS BLOQUEANTES
- `⚠️ BLOQUEO:` {{Si el db_*.md omite una tabla necesaria para que la API funcione, regístralo aquí. Si todo está correcto, escribe "Ninguno"}}.

---

## 5. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Instrucción de una sola línea continua para notificar al QA Técnico)*

@QT: Los contratos de integración (API) y endpoints para {{TITULO_EPICA}} han sido definidos en api_{{nombre_corto}}.md basados en spec.md y db_{{nombre_corto}}.md. Por favor, procede con la auditoría cruzada y la compilación del Tech Design (TDD).
```

---

### ⚠️ Directiva de Interfaz para Ecosistemas Preexistentes (Modo Brownfield)
Si existe el archivo `files/context/constitution.md` o `.specify/memory/constitution.md`:
1. **Subordinación Estricta de Interfaz (Lex Superior):** Los contratos de integración deben subordinarse a los protocolos de comunicación, servicios de red y mecanismos de autenticación especificados en el documento de constitución.
2. **Capa de Adaptación:** Diseñar los adaptadores necesarios (BFF / Facade) y el mapeo formal de códigos de error hacia respuestas estándar.
3. **Nulidad de Peticiones y Salvoconducto Único:** Si en el tracker se solicitan protocolos incompatibles, queda anulado salvo que exista una sección `## ⚠️ CLÁUSULA DE EXCEPCIÓN ARQUITECTÓNICA`.
4. **ADR Obligatorio de Interfaz Heredada (MADR):** Redactar un ADR justificando la compatibilidad con los protocolos heredados con estado `Aceptado (heredado)`.

[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
