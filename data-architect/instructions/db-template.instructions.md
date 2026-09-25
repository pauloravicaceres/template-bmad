---
description: 'Plantilla determinista para el artefacto generado por el Data Architect (db_[nombre_corto].md). Incluye MER, diccionario de datos, trazabilidad UI-Data y registro de decisiones (ADR) en formato MADR.'
applyTo: '**'
---

# Plantilla de Base de Datos y Decisiones (MER + ADR)

## Convención de Nombres de Archivo
`db_[nombre_corto].md` (ej. `db_motor_reservas.md`)

## Estructura Canónica Obligatoria

```markdown
# DISEÑO DE PERSISTENCIA (MER): {{TITULO_EPICA}}

- **Historias de Usuario Base:** {{Nombres de los archivos hu_*.md procesados}}
- **Diseño Visual UX Auditado:** {{Nombre de ux_*.md auditado o "N/A - Bypass Headless"}}
- **Fecha de Diseño:** {{FECHA_ACTUAL}}
- **Data Architect:** Agente DA Senior BMAD

---

## 1. ARCHITECTURE DECISION RECORDS (ADR - Formato MADR)
*(Justificación técnica de las decisiones estructurales más importantes tomadas para este diseño)*

### ADR-01: {{Título de la decisión, ej. Motor de Persistencia o Tipo de Llave Primaria}}
- **Estado:** {{ Aceptado | Aceptado (heredado) }}
  > *Regla: Usar "Aceptado (heredado)" si la decisión proviene de files/context/legacy_ecosystem.md. Las decisiones heredadas no requieren alternativas consideradas.*
- **Contexto:** {{Qué necesidad de modelado, regla funcional o restricción del legacy_ecosystem.md motiva la elección}}.
- **Decisión:** {{Tipo de dato, motor, particionamiento o normalización seleccionada en una frase clara y verificable}}.
- **Alternativas Evaluadas (Obligatorio en decisiones nuevas):**
  - **Alternativa A:** {{Opción viable descartada y justificación técnica con argumentos reales}}.
  - **Alternativa B:** {{Opción viable descartada y justificación técnica con argumentos reales}}.
  - *(Exento de alternativas si el estado es Aceptado (heredado))*.
- **Consecuencias:**
  - ✅ **Ventajas / Impacto Positivo:** {{Eficiencia transaccional o integridad garantizada}}.
  - ⚠️ **Trade-off / Costo Real:** {{Complejidad en migraciones, costo de storage o sobrecarga de índices. Prohibido omitir trade-offs reales}}.

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

---

### ⚠️ DIRECTIVA OBLIGATORIA DE TRAZABILIDAD UI -> DATA (Cruce con UX)
1. **Inspección Visual de Datos:** Si el proyecto cuenta con diseño visual (`files/designer-ux/ux_*.md`), el Data Architect debe auditar cada wireframe y estado visual antes de cerrar el MER.
2. **Cero Campos Huérfanos:** Cada elemento de interfaz que requiera persistencia o cálculo (ej. etiquetas de descuento, badges de estado, contadores, timestamps de edición, preferencias de visualización) debe tener su columna y tipo correspondiente en el Diccionario de Datos.
3. **Excepción Headless:** Si el proyecto proviene de un Bypass Headless (sin `ux_*.md`), el modelo se deriva exclusivamente de las Historias de Usuario (`hu_*.md`) y del Product Brief (`pb_*.md`).

---

### ⚠️ Directiva de Persistencia para Ecosistemas Preexistentes (Modo Brownfield)
Si existe el archivo `files/context/legacy_ecosystem.md`:
1. **Subordinación Estricta de Persistencia:** Lee el archivo legacy en su totalidad. El motor de persistencia, dialecto SQL, tipos de datos y convenciones relacionales deben subordinarse estrictamente a lo establecido en dicho archivo.
2. **Prohibición de Incompatibilidad:** Queda estrictamente prohibido proponer motores de base de datos que colisionen con las directivas del archivo legacy.
3. **ADR Obligatorio de Coexistencia (MADR):** Redactar un ADR justificando la integración, extensiones de tablas o coexistencia con las entidades y procedimientos del esquema heredado, utilizando el estado `Aceptado (heredado)` sin requerir alternativas consideradas.
4. **Si el archivo NO existe (Modo Greenfield):** Modela el MER y diccionario de datos libremente según lo dispuesto en `tech_guidelines.md` sin precondiciones heredadas.


[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
