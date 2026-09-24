---
description: 'Usar EXCLUSIVAMENTE cuando el QT detecta inconsistencias entre la Base de Datos y la API. Plantilla para el archivo feedback_tech_[nombre_corto].md.'
applyTo: '**'
---

# Plantilla de Rechazo de Arquitectura

## Convención de Nombres de Archivo
`feedback_tech_[nombre_corto].md`

## Estructura Canónica Obligatoria

```markdown
# REPORTE DE INCONSISTENCIA ARQUITECTÓNICA ❌

- **Fecha de Auditoría:** {{FECHA_ACTUAL}}
- **Archivos Evaluados:** `db_*.md` y `api_*.md`

## 1. DESCRIPCIÓN DEL FALLO DE INTEGRIDAD
*(Explicar claramente por qué la API y la Base de Datos chocan. Ej: "El endpoint POST /usuarios requiere el campo 'telefono', pero la tabla USUARIOS en el MER no posee esa columna").*

## 2. DIRECTIVA DE SUBSANACIÓN
*(Indicar explícitamente a qué agente se devuelve el flujo)*

- **Agente Responsable:** [ @DA: para modificar tablas | @API: para modificar endpoints | @SA: para coordinar la resolución ]
- **Acción Requerida:** {{Instrucción técnica precisa para corregir el fallo y mantener la coherencia}}.
```
