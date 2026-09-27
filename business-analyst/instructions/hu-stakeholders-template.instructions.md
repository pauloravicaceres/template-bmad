---
description: 'Usar al generar la Historia de Usuario para Stakeholders (HU Funcional/Negocio). Esqueleto determinista orientado a valor de negocio, narrativa amigable y criterios funcionales. Se guarda en files/business-analyst/HUs-stakeholders/.'
applyTo: '**'
---

# Plantilla de Historia de Usuario para Stakeholders — BMAD

Toda HU de Stakeholders generada por el agente BA usa esta estructura. Enfatiza el valor de negocio, el impacto operativo, la narrativa en primera persona y criterios funcionales comprensibles para usuarios de negocio y Product Owners.

## Secciones OBLIGATORIAS

| Sección | Por qué es obligatoria |
|---|---|
| `## 1. HISTORIA DE USUARIO` con **Como / Quiero / Para** | Define el valor de negocio y el rol beneficiario |
| `## 2. CRITERIOS DE ACEPTACIÓN FUNCIONALES` (≥ 2, incluyendo al menos 1 Sad Path) | Definen las condiciones de satisfacción de negocio |
| `## 3. 📊 DIAGRAMAS DE LA HU` (bloque `mermaid` o declaración "Sin diagrama") | Trazabilidad visual comprensible |
| `## 4. IMPACTO OPERATIVO Y BENEFICIO DE NEGOCIO` | Justificación del ROI y valor generado |
| `## 5. DEFINITION OF DONE (STAKEHOLDER)` | Cierre de conformidad funcional |
| Pie de **origen + `[PROPUESTO]`** | Trazabilidad contra el Product Brief |

## Secciones OPCIONALES

- `## 🎨 REFERENCIA DE EXPERIENCIA VISUAL` — Solo para épicas con componente de interfaz.
- `## ❓ PREGUNTAS Y PUNTOS ABIERTOS` — Para resolver con el equipo de negocio.

## Convención de Nombres de Archivo y Ruta
```
files/business-analyst/HUs-stakeholders/hu_[ID]_[nombre_corto].md
```
- `ID`: Número secuencial de dos dígitos (`01`, `02`, …).
- `nombre_corto`: snake_case, máximo 4 palabras, agnóstico al dominio.

## Esqueleto Completo (rellenar desde el Product Brief; nunca inventar)

```markdown
# HISTORIA DE USUARIO (STAKEHOLDERS): {{TITULO_HU}}

- **ID de Historia:** HU-{{ID}}
- **Épica:** {{NOMBRE_EPICA}}
- **Audiencia:** Stakeholders, Product Owner, Usuarios Clave

---

## 1. HISTORIA DE USUARIO
**Como** {{ROL_USUARIO_O_NEGOCIO}}
**Quiero** {{CAPACIDAD_O_ACCION_FUNCIONAL}}
**Para** {{BENEFICIO_O_VALOR_DE_NEGOCIO}}

## 2. CRITERIOS DE ACEPTACIÓN FUNCIONALES
- **CA-01 — {{Nombre_Happy_Path}}:**
  - **Dado** {{contexto de negocio inicial}},
  - **Cuando** {{el usuario realiza la acción descrita}},
  - **Entonces** {{el sistema responde con el resultado esperado y medible}}.
- **CA-02 — {{Nombre_Sad_Path}}:**
  - **Dado** {{situación de error o datos inválidos}},
  - **Cuando** {{el usuario intenta ejecutar la acción}},
  - **Entonces** {{el sistema previene el error y guía al usuario de manera comprensible}}.

## 3. 📊 DIAGRAMAS DE LA HU
<bloque ```mermaid ... ``` con flujo visual amigable, o: _Sin diagrama directamente vinculado a esta HU._>

## 4. IMPACTO OPERATIVO Y BENEFICIO DE NEGOCIO
- **Valor Agregado:** {{Descripción del beneficio operativo o ahorro de tiempo/costo}}
- **Métricas Clave:** {{KPIs o indicadores impactados}}

## 5. DEFINITION OF DONE (STAKEHOLDER)
- [ ] La HU cumple con todos los Criterios de Aceptación declarados desde la perspectiva del usuario.
- [ ] El Happy Path y al menos un Sad Path están definidos en términos comprensibles.
- [ ] No incluye jerga técnica de implementación de bajo nivel.
- [ ] Validado con los objetivos del Product Brief.

<!-- OPCIONAL — incluir solo si la épica tiene supuestos -->
## Supuestos de Negocio
- <supuestos de negocio heredados del PRD o inferidos razonablemente, marcados con ⚠️ [PROPUESTO]>

<!-- OPCIONAL — incluir si hay componente visual -->
## 🎨 REFERENCIA DE EXPERIENCIA VISUAL
- **Pantalla / Módulo:** {{nombre_pantalla}} o "No aplica para backend puro"

---
> **Origen:** {{Nombre_del_archivo_fuente}} (Product Brief / Plan de Gestión).
> Todo contenido generado que no esté explícito en la fuente se marca como `⚠️ [PROPUESTO]`.
```

### ⚠️ Directiva para Ecosistemas Preexistentes (Modo Brownfield)
Si existe el archivo `files/context/constitution.md`:
- Los Criterios de Aceptación deben alinearse con las reglas de negocio y restricciones operativas documentadas.
- En la DoD incluir: `- [ ] La funcionalidad respeta las reglas de negocio del sistema preexistente documentado.`

[IMPORT_SKILL: skills/hu-validator/SKILL.md]
[IMPORT_SKILL: skills/tracker-logger/SKILL.md]
[IMPORT_SKILL: skills/export-pdf/SKILL.md]
