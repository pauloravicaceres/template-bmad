---
description: 'Usar EXCLUSIVAMENTE cuando el QT aprueba la arquitectura. Plantilla determinista para consolidar db_*.md y api_*.md en el documento maestro tech-design_[nombre_corto].md con diagramación híbrida y matriz consolidada MADR.'
applyTo: '**'
---

# Plantilla del Tech Design Maestro (Consolidado)

> Este documento unifica la visión de componentes, el MER, la API, los diagramas de arquitectura y centraliza todos los ADRs generados por los arquitectos especialistas bajo el formato MADR.

## Convención de Nombres de Archivo
`tech-design_[nombre_corto].md` (ej. `tech-design_motor_reservas.md`)

## Estructura Canónica Obligatoria

```markdown
# TECH-DESIGN: {{TITULO_DEL_PROYECTO}}

- **Fecha de Compilación:** {{FECHA_ACTUAL}}
- **Auditor y Consolidador:** Agente QT Senior BMAD
- **Estado:** ✅ AUDITADO Y APROBADO (Auditoría Adversarial Exitosa)

---

## 1. Architecture Overview
*(Resumen de alto nivel del propósito técnico del sistema y su patrón de diseño principal, inferido a partir de los documentos analizados).*

---

## 2. Components
*(Listado de los módulos o subsistemas lógicos que componen la solución).*

---

## 3. Data Model
*(Integrar aquí el contenido completo y exacto de la sección Modelo Entidad-Relación y Diccionario de Datos extraído del archivo `db_*.md`, incluyendo la validación de no-orfandad frente al diseño UX).*

---

## 4. Integrations
*(Integrar aquí el contenido completo y exacto de los Contratos REST/GraphQL y endpoints extraídos del archivo `api_*.md`).*

---

## 5. DIAGRAMAS DE ARQUITECTURA (Componentes, Secuencia, Despliegue)

**Regla de diagramación híbrida y resiliente (`archify` + `mermaid`):**

- **Escenario A: Con acceso a la skill `archify` (Modo Dual Enriquecido):**
  - Si la skill `archify` está disponible en tu entorno, debes generar **AMBOS** formatos para cada diagrama:
    1. Genera los artefactos interactivos de `archify` (archivos HTML interactivos y especificaciones JSON) en la carpeta `files/qa-tech/diagrams/`.
    2. Incrusta obligatoriamente debajo de las referencias a los artefactos el bloque nativo en sintaxis `mermaid` correspondiente, garantizando visualización inmediata tanto en visores Markdown estándar como en navegadores web interactivos.
  - **Formato canónico obligatorio por diagrama en Escenario A:**
    ### 5.X. [Título del Diagrama] (`[tipo: sequence | workflow | component]`)
    - 🌐 **Visor Interactivo HTML:** [`diagrams/[nombre].html`](file:///D:/Paulo/Cursos/DMC/template-bmad/files/qa-tech/diagrams/[nombre].html)
    - 📄 **Especificación Fuente JSON:** [`diagrams/[nombre].[tipo].json`](file:///D:/Paulo/Cursos/DMC/template-bmad/files/qa-tech/diagrams/[nombre].[tipo].json)
    - **Estado de Validación:** ✅ *Showcase Pass (N/N checks)*

    \`\`\`mermaid
    [código nativo de mermaid representando la arquitectura]
    \`\`\`

- **Escenario B: Sin acceso a la skill `archify` (Fallback Nativo - Cero Fricción):**
  - Si la skill no está disponible en tu entorno de herramientas, **no te detengas ni solicites instalación manual al humano**.
  - Aplica el principio de degradación elegante y genera los diagramas **únicamente en sintaxis nativa `mermaid`** directamente dentro de este documento, omitiendo los enlaces HTML/JSON e incluyendo esta nota al pie del bloque:
    > *Nota de Arquitectura: Diagrama generado exclusivamente con Mermaid por ausencia de dependencias externas. Para habilitar visores HTML interactivos, instale la skill en la raíz del proyecto (`npx skills add tt-a1i/archify -g`) y solicite la actualización de esta sección.*

- **Consistencia Inmutable:** Sea cual sea el escenario aplicado, ningún diagrama puede contradecir lo estipulado en los ADRs (ej. si el ADR dice "Microservicios", el diagrama no puede mostrar un "Monolito").

---

## 6. Technology Stack
*(Listado de las tecnologías, bases de datos y frameworks asumidos o explícitamente requeridos por la arquitectura).*

---

## 7. Architecture Decisions (ADRs - Matriz Consolidada MADR)
*(Consolidar en esta sección TODOS los ADRs generados por SA, DA y API, verificando que ninguno mantenga alternativas cosméticas y que todos reconozcan sus consecuencias reales).*

| ID | Título de la Decisión | Área | Estado | Trade-off / Costo Admitido |
|:---:|---|:---:|:---:|---|
| **ADR-001** | {{Stack y Hosting}} | Infraestructura (SA) | Aceptado / Aceptado (heredado) | {{Costo operativo / Curva de aprendizaje}} |
| **ADR-002** | {{Estrategia de Estado}} | Arquitectura (SA) | Aceptado / Aceptado (heredado) | {{Latencia de sincronización}} |
| **ADR-003** | {{Modelo de Persistencia}} | Datos (DA) | Aceptado / Aceptado (heredado) | {{Sobrecarga en índices de búsqueda}} |
| **ADR-004** | {{Protocolo de Integración}} | APIs (API) | Aceptado / Aceptado (heredado) | {{Payload overhead en red}} |

### ADR-001: {{Título del ADR original del SA}}
- **Estado:** {{Aceptado | Aceptado (heredado)}}
- **Contexto:** ...
- **Decisión:** ...
- **Alternativas Evaluadas:** ...
- **Consecuencias (Beneficios y Costos Reales):** ...

### ADR-002: {{Título del ADR original del DA}}
- **Estado:** {{Aceptado | Aceptado (heredado)}}
- **Contexto:** ...
- **Decisión:** ...
- **Alternativas Evaluadas:** ...
- **Consecuencias (Beneficios y Costos Reales):** ...

### ADR-003: {{Título del ADR original de la API}}
- **Estado:** {{Aceptado | Aceptado (heredado)}}
- **Contexto:** ...
- **Decisión:** ...
- **Alternativas Evaluadas:** ...
- **Consecuencias (Beneficios y Costos Reales):** ...
```

---

### ⚠️ Directiva de Compilación para Ecosistemas Preexistentes (Modo Brownfield)
Si existe el archivo `files/context/legacy_ecosystem.md`:
1. **Auditoría Cruzada de Restricciones Legacy:** Verificar que el modelo de persistencia (`db_*.md`) y los contratos de red (`api_*.md`) respeten estrictamente las tecnologías, protocolos y motores especificados en el archivo legacy. Si se detectan violaciones, emite inmediatamente rechazo (`feedback_tech_*.md`).
2. **Registro MADR Heredado:** Asegurar que las decisiones técnicas provenientes del sistema existente estén registradas con estado `Aceptado (heredado)` sin requerir alternativas inventadas.
3. **Diagramas de Arquitectura (Sección 5):** Los diagramas de componentes y despliegue deben representar explícitamente la convivencia entre la nueva solución y la infraestructura/servidores heredados descritos en el archivo legacy.
4. **Sección de Integraciones (Sección 4):** Consignar formalmente los mecanismos de adaptación y protocolos de interoperabilidad con el sistema preexistente.
5. **Si el archivo NO existe (Modo Greenfield):** Compila el Tech Design Document estándar consolidando el MER, la API y los ADRs sin precondiciones heredadas.


[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
