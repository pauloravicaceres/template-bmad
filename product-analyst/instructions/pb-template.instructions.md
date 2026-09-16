---
description: 'Usar para estructurar la salida física del archivo pb_[Nombre_Corto].md en la carpeta product-analyst. Define las 8 secciones canónicas obligatorias validadas por el Quality Gate del Watcher en BMAD.'
applyTo: '**'
---

# Plantilla Determinista del Product Brief

> Estructura canónica obligatoria para el artefacto generado por el Product Analyst (`pb_[Nombre_Corto].md`).
> Las 8 secciones son de presencia obligatoria para superar el Quality Gate hacia el Product Manager.

---

## Convención de Nombres de Archivo
```
pb_[Nombre_Corto].md
```
- `Nombre_Corto`: snake_case, máximo 4 palabras, representativo del producto (ej. de `idea_reserva_citas.md` se genera `pb_reserva_citas.md`).

---

## Estructura Canónica de las 8 Secciones

```markdown
# PRODUCT BRIEF: {{TITULO_DEL_PRODUCTO}}

- **Documento Fuente:** {{NOMBRE_ARCHIVO_IDEA}}
- **Fecha de Elaboración:** {{FECHA_ACTUAL}}
- **Product Analyst:** Agente PA Senior BMAD (Fase Discovery)

---

## 1. PROBLEMA
*(Diferenciar hechos comprobables de inferencias lógicas)*

- **Hechos Comprobables:** {{Dolor, fricción o necesidad de negocio explícitamente descrita en la idea de entrada}}.
- **Inferencias Lógicas:** {{Deducciones analíticas sobre la causa raíz, etiquetadas obligatoriamente con ⚠️ SUPUESTO:}}.

---

## 2. USUARIOS
*(Actores que experimentan el problema y usuarios que operarán la solución)*

- **Usuario Principal / Beneficiario:** {{Perfil del actor que sufre la fricción y recibe el valor directo}}.
- **Usuarios Secundarios / Operativos:** {{Colaboradores, administradores o terceros que interactúan con el flujo}}.

---

## 3. OBJETIVO (OUTCOME)
*(Resultado de negocio deseado o cambio de comportamiento observable; no una lista de features)*

- **Propósito Central:** {{Qué cambio cuantificable o mejora cualitativa de negocio se espera alcanzar con esta solución}}.

---

## 4. ALCANCE INICIAL (MVP)
*(Límites y módulos funcionales prioritarios para la primera versión)*

- **Módulos Incluidos:**
  - {{Módulo 1: Descripción macro de la capacidad}}.
  - {{Módulo 2: Descripción macro de la capacidad}}.
- **Exclusiones Explícitas (Fuera de Alcance):**
  - {{Capacidades complejas o secundarias que NO deben construirse en el MVP inicial}}.

---

## 5. RESTRICCIONES
*(Limitaciones de negocio, legales, regulatorias u operativas inquebrantables)*

- {{Restricción 1: Regla de negocio innegociable, ej. no mostrar precios o requerir confirmación previa}}.
- {{Restricción 2: Limitación operativa o de canal}}.

---

## 6. CRITERIOS DE ÉXITO
*(Métricas o evidencias para determinar si la solución resolvió el problema)*

- **Indicador Primario:** {{Métrica cuantitativa extraída del input o marcada como ⚠️ [PROPUESTO]:}}.
- **Evidencia Cualitativa:** {{Criterio de validación observable o marcado como ❓ No documentado si el brief no aportó métricas}}.

---

## 7. SUPUESTOS
*(Hipótesis asumidas como verdaderas que condicionan la viabilidad de la solución y requieren validación)*

- `⚠️ SUPUESTO:` {{Hipótesis operativa o de comportamiento de usuario asumida}}.
- `⚠️ SUPUESTO:` {{Hipótesis de disponibilidad de canales o información}}.

---

## 8. PREGUNTAS ABIERTAS
*(Vacíos críticos de información que deben resolverse antes o durante la fase de Management)*

1. {{Pregunta crítica 1 relacionada a un dato marcado como ❓ No documentado}}.
2. {{Pregunta crítica 2 sobre reglas de negocio ambiguas que el PM y BA no deben inventar}}.
```
