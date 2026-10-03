# PRODUCT BRIEF: Generador de Cotizaciones Web

- **Documento Fuente:** idea_generador_cotizaciones.md
- **Fecha de Elaboración:** 2026-10-02
- **Product Analyst:** Agente PA Senior BMAD (Fase Discovery)

---

## 1. PROBLEMA
*(Diferenciar hechos comprobables de inferencias lógicas)*

- **Hechos Comprobables:** 
  - Fricción operativa grave en el proceso comercial de un desarrollador independiente en Perú al crear propuestas de páginas y aplicaciones web.
  - El proceso manual exige analizar requerimientos desde cero, redactar/seleccionar servicios, estimar costos manualmente y diagramar documentos.
  - Esto genera consumo excesivo de tiempo productivo, demoras en el envío de propuestas a clientes e inconsistencias/errores en la estimación de precios.
- **Inferencias Lógicas:** 
  - `⚠️ SUPUESTO:` La lentitud en la entrega de cotizaciones disminuye la tasa de conversión de clientes potenciales por falta de respuesta oportuna.
  - `⚠️ SUPUESTO:` La falta de plantillas estandarizadas causa variabilidad no controlada en los márgenes de ganancia por proyecto.

---

## 2. USUARIOS
*(Actores que experimentan el problema y usuarios que operarán la solución)*

- **Usuario Principal / Beneficiario:** Desarrollador de software independiente (freelance) en Perú, responsable de administrar servicios, configurar cotizaciones y emitir propuestas.
- **Usuarios Secundarios / Operativos:** Clientes finales (empresas/personas contratantes) que reciben y revisan las propuestas comerciales en PDF.

---

## 3. OBJETIVO (OUTCOME)
*(Resultado de negocio deseado o cambio de comportamiento observable; no una lista de features)*

- **Propósito Central:** Estandarizar, parametrizar y reducir el tiempo de generación de cotizaciones comerciales a pocos minutos, eliminando inconsistencias en precios y acelerando el ciclo de entrega de propuestas a clientes.

---

## 4. ALCANCE INICIAL (MVP)
*(Límites y módulos funcionales prioritarios para la primera versión)*

- **Módulos Incluidos:**
  - **Catálogo Parametrizable:** Registro y administración de servicios y funcionalidades predefinidas para sitios y aplicaciones web con sus tarifas base.
  - **Configurador Interactivo de Cotizaciones:** Selección de módulos/servicios, ajuste de cantidades y parámetros personalizados según la necesidad del cliente.
  - **Motor de Cálculo Automático:** Cómputo de subtotales, totales y desglose de precios del proyecto.
  - **Módulo de Generación de Documentos PDF:** Consolidación formal de la propuesta en formato PDF profesional, incluyendo detalle de servicios, costos, datos del cliente y condiciones comerciales.
- **Exclusiones Explícitas (Fuera de Alcance):**
  - Módulos de seguimiento post-envío (ej. firma electrónica en línea, tracking de apertura de correos).
  - Integración con pasarelas de pago o facturación electrónica ante SUNAT.
  - Portal de acceso autogestionado interactivo para el cliente final en esta primera versión.
  - Gestión multimoneda con conversión en tiempo real (se opera de entrada bajo moneda local/estándar parametrizada).

---

## 5. RESTRICCIONES
*(Limitaciones de negocio, legales, regulatorias u operativas inquebrantables)*

- **Restricción de Negocio/Contexto:** Diseñado para la operativa de desarrollador independiente en el mercado peruano.
- **Restricción de Arquitectura/Ecosistema:** Integración con la Constitución Técnica BMAD (uso de estructuración web desacoplada en `app/frontend/` y `app/backend/` en fases de implementación).
- **Restricción Operativa:** Salida de documento final obligatoriamente en formato PDF listo para envío directo.

---

## 6. CRITERIOS DE ÉXITO
*(Métricas o evidencias para determinar si la solución resolvió el problema)*

- **Indicador Primario:** `⚠️ [PROPUESTO]:` Reducción del tiempo promedio de elaboración de cotizaciones a menos de 5 minutos por propuesta.
- **Evidencia Cualitativa:** Eliminación total de errores de cálculo manual e inconsistencias de precios en las propuestas emitidas, logrando formatos PDF uniformes y profesionales.

---

## 7. SUPUESTOS
*(Hipótesis asumidas como verdaderas que condicionan la viabilidad de la solución y requieren validación)*

- `⚠️ SUPUESTO:` El catálogo de servicios base puede parametrizarse inicialmente mediante un conjunto predefinido de ítems de desarrollo web comunes.
- `⚠️ SUPUESTO:` Las condiciones comerciales de los proyectos pueden estandarizarse en plantillas de texto dentro del generador.
- `⚠️ SUPUESTO:` El desarrollador independiente opera principalmente desde una computadora de escritorio/laptop para la configuración de propuestas.

---

## 8. PREGUNTAS ABIERTAS
*(Vacíos críticos de información que deben resolverse antes o durante la fase de Management)*

1. ❓ No documentado: ¿Se requiere manejar impuestos locales (ej. IGV / Retención por Recibo por Honorarios) en la estructura de cálculo del PDF?
2. ❓ No documentado: ¿Las condiciones comerciales y plazos de validez de la oferta son fijos o deben ser totalmente editables por cada cotización?

---

## 9. ORDEN DE DELEGACIÓN PARA EL TRACKER (PAUSA OBLIGATORIA HITL)
*(Al finalizar el Product Brief, el flujo entra en pausa obligatoria Human-in-the-Loop para revisión humana. La activación del Product Manager depende de utils/approve_step.py. REGLA ESTRICTA: Usa siempre el nombre en texto plano "product-manager", NUNCA la etiqueta "@PM:" para evitar disparos accidental en el orquestador).*

@HUMANO: El Product Brief pb_generador_cotizaciones.md está listo para revisión en documents/product-analyst/. Por favor, valida el alcance y ejecuta `python utils/approve_step.py` para autorizar formalmente la transición hacia el product-manager.
