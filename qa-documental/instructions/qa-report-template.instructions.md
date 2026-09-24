---
description: 'Usar para estructurar el reporte de salida del QA Documental. Define las dos únicas plantillas permitidas: Certificado de Aprobación (aprobado_qa_*.md) y Reporte de Observaciones (feedback_qa_*.md).'
applyTo: '**'
---

# Plantilla Determinista de Reportes de QA

> Formato estricto para los entregables del agente QA Documental en BMAD.
> Debes generar ÚNICAMENTE UNA de las dos opciones por cada evaluación. Está estrictamente prohibido combinarlas.

---

## Convención de Nombres de Archivo

El nombre del archivo de salida se construye tomando como base el nombre exacto del archivo de la Historia de Usuario evaluado:

| Dictamen | Patrón de Nombre | Ejemplo de Entrada | Nombre del Archivo QA |
|---|---|---|---|
| **Aprobado** | `aprobado_qa_[ID]_[nombre_corto].md` | `hu_01_motor_reservas.md` | `aprobado_qa_01_motor_reservas.md` |
| **Rechazado** | `feedback_qa_[ID]_[nombre_corto].md` | `hu_01_motor_reservas.md` | `feedback_qa_01_motor_reservas.md` |

---

## OPCIÓN A: Plantilla para Dictamen RECHAZADO

Se utiliza cuando la Historia de Usuario incumple cualquiera de las 5 dimensiones de la rúbrica.

```markdown
# REPORTE DE AUDITORÍA QA: RECHAZADO

- **Historia de Usuario Evaluada:** {{TITULO_HU}}
- **Archivo Fuente Evaluado:** {{NOMBRE_ARCHIVO_HU}}
- **Fecha de Auditoría:** {{FECHA_AUDITORIA}}
- **Dictamen:** ❌ RECHAZADO (Retorno a Business Analyst para Subsanación)

---

## 1. RESUMEN EJECUTIVO DE NO-CONFORMIDADES
{{Breve resumen analítico de 1 o 2 párrafos indicando los motivos estructurales que impiden el paso a la fase técnica}}.

---

## 2. TABLA DETALLADA DE HALLAZGOS

| ID Hallazgo | Dimensión Afectada | Gravedad (Bloqueante / Mayor) | Descripción de la No-Conformidad | Evidencia en el Documento | Acción Correctiva Requerida |
|---|---|---|---|---|---|
| H-01 | Trazabilidad / Casuística / etc. | Bloqueante | {{Explicación clara del fallo}} | {{Cita textual o sección de la HU}} | {{Instrucción puntual de lo que el BA debe corregir}} |
| H-02 | ... | ... | ... | ... | ... |

---

## 3. AUDITORÍA ESPECÍFICA DE CRITERIOS GHERKIN (BDD)
- **Happy Path:** [Conforme / Observado] — {{Comentario}}
- **Sad Paths / Edge Cases:** [Conforme / Ausente / Insuficiente] — {{Detalle de los flujos de error que faltan}}

---

## 4. DIRECTIVA DE SUBSANACIÓN PARA EL BA
Estimado Business Analyst: procede a editar el archivo `{{NOMBRE_ARCHIVO_HU}}` resolviendo puntualmente las acciones correctivas listadas en la sección 2. Mantén intactos los criterios y secciones lógicas que no fueron observadas. Al finalizar, actualiza el tracker delegando nuevamente la auditoría al QA.
```

---

## OPCIÓN B: Plantilla para Dictamen APROBADO

Se utiliza **exclusivamente** cuando la Historia de Usuario satisface el 100% de las 5 dimensiones.

```markdown
# CERTIFICADO DE AUDITORÍA QA: APROBADO

- **Historia de Usuario Evaluada:** {{TITULO_HU}}
- **Archivo Fuente Evaluado:** {{NOMBRE_ARCHIVO_HU}}
- **Fecha de Auditoría:** {{FECHA_AUDITORIA}}
- **Dictamen:** ✅ APROBADO (Certificación Concedida para Fase de Arquitectura y UX)

---

## 1. DECLARACIÓN FORMAL DE CONFORMIDAD
La especificación de requerimientos contenida en el archivo `{{NOMBRE_ARCHIVO_HU}}` ha sido auditada exhaustivamente contra el Product Brief original. Se certifica que la historia cumple con el estándar INVEST, respeta rigurosamente las fronteras de alcance del producto y cuenta con Criterios de Aceptación Gherkin testeables que cubren tanto los flujos ideales como los escenarios de contingencia y error.

---

## 2. MATRIZ DE CUMPLIMIENTO DOCUMENTAL

| Dimensión Auditada | Estado | Observación de Conformidad |
|---|:---:|---|
| **1. Trazabilidad y Alcance** | ✅ CUMPLE | Coincidencia plena con el Product Brief. Supuestos debidamente tipificados. |
| **2. Atomicidad e INVEST** | ✅ CUMPLE | Resuelve una única transacción de negocio indivisible. |
| **3. Cobertura BDD / Gherkin** | ✅ CUMPLE | Happy Path y Sad Paths verificados y testeables. |
| **4. Consistencia Lógica** | ✅ CUMPLE | Sin contradicciones internas ni colisiones con reglas globales. |
| **5. Separación Negocio/Técnica** | ✅ CUMPLE | Enfoque de comportamiento puro sin detalles de implementación. |

---

## 3. AUTORIZACIÓN DE TRANSICIÓN Y ORDEN DE DELEGACIÓN (TRACKER)
*(Analiza la naturaleza del proyecto leyendo el Product Brief y elige ÚNICAMENTE la instrucción que corresponda anexar al tracker_bmad.md)*

- **SI EL PROYECTO TIENE INTERFAZ GRÁFICA (Web, App, Dashboard):**
  Se autoriza formalmente el traspaso del requerimiento al **Diseñador UX**.
  **Instrucción para el Tracker:** `@UX: La Historia de Usuario [NOMBRE_HU] ha sido aprobada por QA. Por favor, procede a diseñar los wireframes y estados visuales.`

- **SI EL PROYECTO ES HEADLESS (APIs, ETL, SSIS, Procesos de Backend sin UI):**
  Se autoriza formalmente el traspaso directo a la **Fase de Arquitectura**.
  **Instrucción para el Tracker:** `@SA: La Historia de Usuario [NOMBRE_HU] ha sido aprobada por QA. Al ser un proyecto Headless, el diseño UX se omite. Por favor, formula tus preguntas para definir el stack tecnológico y la gobernanza.`
```
