---
description: 'Usar EXCLUSIVAMENTE cuando el QT aprueba la arquitectura. Plantilla determinista para consolidar db_*.md y api_*.md en el documento maestro tech-design_[nombre_corto].md.'
applyTo: '**'
---

# Plantilla del Tech Design Maestro (Consolidado)

> Este documento unifica la visión de componentes, el MER, la API, los diagramas de arquitectura y centraliza todos los ADRs generados por los arquitectos especialistas.

## Convención de Nombres de Archivo
`tech-design_[nombre_corto].md` (ej. `tech-design_motor_reservas.md`)

## Estructura Canónica Obligatoria

```markdown
# TECH-DESIGN: {{TITULO_DEL_PROYECTO}}

- **Fecha de Compilación:** {{FECHA_ACTUAL}}
- **Auditor y Consolidador:** Agente QT Senior BMAD
- **Estado:** ✅ AUDITADO Y APROBADO

---

## 1. Architecture Overview
*(Resumen de alto nivel del propósito técnico del sistema y su patrón de diseño principal, inferido a partir de los documentos analizados).*

---

## 2. Components
*(Listado de los módulos o subsistemas lógicos que componen la solución).*

---

## 3. Data Model
*(Integrar aquí el contenido completo y exacto de la sección Modelo Entidad-Relación y Diccionario de Datos extraído del archivo `db_*.md`).*

---

## 4. Integrations
*(Integrar aquí el contenido completo y exacto de los Contratos REST/GraphQL y endpoints extraídos del archivo `api_*.md`).*

---

## 5. DIAGRAMAS DE ARQUITECTURA (Componentes, Secuencia, Despliegue)

**Regla estricta de diagramación (`archify`):**
- Intenta utilizar la skill `archify` para generar estos diagramas de forma profesional. 
- Si la skill no está disponible en tu entorno de herramientas, **no te detengas**. Aplica el proceso de "Fallback": genera los diagramas utilizando sintaxis nativa de `mermaid` directamente en este documento.
- **Condición de Fallback:** Si usas `mermaid`, debes incluir explícitamente este texto debajo del bloque del diagrama:
  > *Nota de Arquitectura: Diagrama generado con Mermaid por ausencia de dependencias. Para regenerar la versión extendida, instale la skill en la raíz del proyecto (`npx skills add tt-a1i/archify -g`) y solicite la actualización de esta sección.*
- **Consistencia:** Sea cual sea la herramienta utilizada, el diagrama **no puede contradecir** lo estipulado en los ADRs. Si el ADR dice "Microservicios", el diagrama no puede mostrar un "Monolito".

---

## 6. Technology Stack
*(Listado de las tecnologías, bases de datos y frameworks asumidos o explícitamente requeridos por la arquitectura).*

---

## 7. Architecture Decisions (ADRs)
*(Consolidar en esta sección TODOS los ADRs que redactaron el Data Architect y el API Architect en sus respectivos documentos. Numerarlos secuencialmente).*

### ADR-001: {{Título del ADR original del DA}}
- **Contexto:** ...
- **Decisión:** ...

### ADR-002: {{Título del ADR original de la API}}
- **Contexto:** ...
- **Decisión:** ...
```


[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
