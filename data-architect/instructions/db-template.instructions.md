---
description: 'Plantilla determinista para el artefacto generado por el Data Architect (db_[nombre_corto].md). Incluye MER, diccionario de datos y registro de decisiones (ADR).'
applyTo: '**'
---

# Plantilla de Base de Datos y Decisiones (MER + ADR)

## Convención de Nombres de Archivo
`db_[nombre_corto].md` (ej. `db_motor_reservas.md`)

## Estructura Canónica Obligatoria

```markdown
# DISEÑO DE PERSISTENCIA (MER): {{TITULO_EPICA}}

- **Historias de Usuario Base:** {{Nombres de los archivos hu_*.md procesados}}
- **Fecha de Diseño:** {{FECHA_ACTUAL}}
- **Data Architect:** Agente DA Senior BMAD

---

## 1. ARCHITECTURE DECISION RECORDS (ADR)
*(Justificación técnica de las decisiones estructurales más importantes tomadas para este diseño)*

### ADR-01: {{Título de la decisión, ej. Uso de UUIDs vs Enteros Incrementales}}
- **Contexto:** {{Qué problema o requerimiento forzó esta decisión}}.
- **Alternativas Evaluadas (Descartadas):** {{Qué otras opciones se consideraron y por qué se descartaron}}.
- **Decisión:** {{Qué estrategia o tipo de dato exacto se eligió y por qué}}.
- **Consecuencias:** {{Impacto positivo esperado y posibles trade-offs a considerar}}.

---

## 2. MODELO ENTIDAD-RELACIÓN (MER)

\`\`\`mermaid
erDiagram
    %% Reemplazar con el diseño exacto basado en las Historias de Usuario
    USUARIO ||--o{ RESERVA : "realiza"
    USUARIO {
        uuid id PK
        string email UK
        datetime created_at
    }
\`\`\`

---

## 3. DICCIONARIO DE DATOS Y RESTRICCIONES

### Tabla: `USUARIO`
- `id` (UUID): Llave primaria.
- `email` (VARCHAR 255): Único, requerido. Formato validado.

---

## 4. RIESGOS DE INTEGRIDAD Y ESCALABILIDAD
- `⚠️ RIESGO:` {{Posibles cuellos de botella en la concurrencia o límites del motor de base de datos según los requerimientos}}.

---

## 5. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Analiza el Product Brief y el MVP para determinar el siguiente paso y genera una sola línea de texto continuo sin saltos internos)*

- **SI EL PROYECTO REQUIERE COMUNICACIÓN EXTERNA (APIs REST/GraphQL/Eventos):**
  `@API: El modelo de datos (MER) y la persistencia han sido definidos. Por favor, diseña los contratos de integración (Endpoints/Payloads) basados en estas tablas.`

- **SI EL PROYECTO ES PURAMENTE DE PROCESAMIENTO / ETL (Sin endpoints externos):**
  `@QT: El modelo de datos y las reglas de procesamiento ETL han sido definidos. Al no requerir capa de API, procede directamente con la auditoría y compilación del Tech Design Document (TDD).`
```


[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
