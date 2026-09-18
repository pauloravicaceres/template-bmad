---
description: 'Usar al generar cualquier Historia de Usuario (HU). Esqueleto determinista: define qué secciones son OBLIGATORIAS en toda HU y cuáles son OPCIONALES según el tipo de épica. Palabras clave: plantilla HU, historia de usuario, criterios de aceptación, BDD, DoD, Gherkin.'
applyTo: '**'
---

# Plantilla de Historia de Usuario — BMAD

Toda HU generada por el agente BA usa esta estructura. Las secciones **OBLIGATORIAS** deben estar
presentes en cualquier épica. Las **OPCIONALES** solo si el tipo de cambio las requiere.

> El contrato de calidad del QA Documental evalúa la presencia de las secciones obligatorias.
> Una HU que omita cualquiera de ellas será rechazada automáticamente.

## Secciones OBLIGATORIAS

| Sección | Por qué es obligatoria |
|---|---|
| `## 1. HISTORIA DE USUARIO` con **Como / Quiero / Para** | Define el valor de negocio; sin esto no es una HU |
| `## 2. CRITERIOS DE ACEPTACIÓN` (≥ 2, incluyendo al menos 1 Sad Path) | Definen "hecho" y son la base del QA |
| `## 3. 📊 DIAGRAMAS DE LA HU` (bloque `mermaid` o declaración "Sin diagrama") | Trazabilidad visual del flujo |
| `## 4. DEFINITION OF DONE` | Cierre de calidad con ítems verificables |
| `## 5. ORDEN DE DELEGACIÓN PARA EL QA` | Handoff autónomo al siguiente agente |
| Pie de **origen + `[PROPUESTO]`** | Trazabilidad contra el Product Brief |

## Secciones OPCIONALES

- `## 🎨 REFERENCIA UX/UI` — Solo para épicas con componente de interfaz visual.
- `## ❓ PUNTOS ABIERTOS` — Registrar ambigüedades no bloqueantes para resolución posterior.

## Convención de Nombres de Archivo

```
hu_[ID]_[nombre_corto].md
```

- `ID`: Número secuencial de dos dígitos (`01`, `02`, …) asignado por el PM.
- `nombre_corto`: snake_case, máximo 4 palabras, **agnóstico al dominio** (sin nombre de proyecto ni cliente).

**Ejemplos válidos:** `hu_01_motor_reservas.md`, `hu_03_gestion_cancelacion.md`
**Ejemplos inválidos:** `hu_01_amely_spa_motor.md` ← contiene nombre de proyecto específico.

## Esqueleto Completo (rellenar desde el Product Brief; nunca inventar)

```markdown
## 1. HISTORIA DE USUARIO
**Como** {{ROL_USUARIO}}
**Quiero** {{CAPACIDAD_O_ACCION}}
**Para** {{VALOR_DE_NEGOCIO}}

## 2. CRITERIOS DE ACEPTACIÓN (BDD)
*(Cada CA debe ser testable e independiente)*

- **CA-01 — {{Nombre_Happy_Path}}:** Dado {{contexto}}, Cuando {{acción}}, Entonces {{resultado medible}}.
- **CA-02 — {{Nombre_Sad_Path}}:** Dado {{contexto_de_error}}, Cuando {{acción_con_fallo}}, Entonces {{manejo_del_error}}.

## 3. 📊 DIAGRAMAS DE LA HU
<bloque ```mermaid ... ``` relevante, o: _Sin diagrama directamente vinculado a esta HU._>

## 4. DEFINITION OF DONE
- [ ] La HU cumple con todos los Criterios de Aceptación declarados.
- [ ] El Happy Path y al menos un Sad Path están cubiertos con Gherkin testable.
- [ ] No existen detalles de implementación técnica en el cuerpo de la HU.
- [ ] Los ⚠️ SUPUESTOS y ❓ Puntos Abiertos están explícitamente registrados.

<!-- OPCIONAL — incluir solo si la épica tiene componente visual -->
## 🎨 REFERENCIA UX/UI
- **Pantalla / Módulo:** {{nombre_pantalla}} o "No aplica para backend puro"

<!-- OPCIONAL — incluir si hay ambigüedades no bloqueantes -->
## ❓ PUNTOS ABIERTOS
1. {{Pregunta o vacío de información que no bloquea la HU pero debe resolverse a nivel de negocio}}

---
> **Origen:** {{Nombre_del_archivo_fuente}} (Product Brief / Plan de Gestión).
> Todo contenido generado que no esté explícito en la fuente se marca como `⚠️ [PROPUESTO]`.

## 5. ORDEN DE DELEGACIÓN PARA EL QA
*(Generar como una sola línea de texto continuo, sin saltos de línea internos)*

@QA: La Historia de Usuario {{TITULO_HU}} está lista en el archivo hu_{{ID}}_{{nombre_corto}}.md. Por favor, procede con la auditoría documental contra el Product Brief para asegurar que la historia cumple con los requerimientos originales.
```

## Reglas de Formato

- El contenido `⚠️ [PROPUESTO]` aplica a todo lo inferido por el agente (anti-alucinación).
- La **Orden de Delegación** para el QA (sección 5) es siempre **una sola línea sin saltos de línea internos**. Este requisito es mecánico (el Watcher parsea línea por línea); no afecta al formato del resto del documento.
- No incluir detalles técnicos (stack, APIs, frameworks) en las secciones 1–4.
- En el **Escenario B (corrección por QA):** sobreescribir el archivo `hu_*.md` existente aplicando únicamente las observaciones del feedback. No alterar las secciones que el QA no marcó.


[IMPORT_SKILL: skills/hu-validator/SKILL.md]
[IMPORT_SKILL: skills/export-pdf/SKILL.md]