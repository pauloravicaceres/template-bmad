# PRODUCT BRIEF: Cotizador Freelance para Desarrollador de Software

- **Documento Fuente:** files/business-storyteller/idea_cotizador_freelance.md
- **Fecha de Elaboración:** 02-10-2026
- **Product Analyst:** Agente PA Senior BMAD (Fase Discovery)

---

## 1. PROBLEMA
*(Diferenciar hechos comprobables de inferencias lógicas)*

- **Hechos Comprobables:** Desarrollador freelance de software radicado en Perú (especializado en páginas web, aplicaciones web y desarrollo móvil) enfrenta una fuerte fricción operativa debido a que la elaboración de cotizaciones comerciales se realiza de manera totalmente manual. En cada propuesta debe analizar requerimientos desde cero, listar servicios/funcionalidades, calcular costos estimados y diagramar el documento final. Esta repetición constante limita la capacidad de respuesta comercial y descuida horas valiosas de desarrollo y atención a clientes.
- **Inferencias Lógicas:**
  - `⚠️ SUPUESTO:` La demora en la entrega de propuestas manuales podría ocasionar la pérdida de clientes potenciales ante competidores con mayor velocidad de respuesta.
  - `⚠️ SUPUESTO:` La falta de un tarifario estandarizado y automatizado genera riesgo de inconsistencias o errores en el cálculo de costos para proyectos de alcance similar.

---

## 2. USUARIOS
*(Actores que experimentan el problema y usuarios que operarán la solución)*

- **Usuario Principal / Beneficiario:** Desarrollador freelance de software (administrador de propuestas comerciales), quien opera el sistema para registrar su tarifario, configurar cotizaciones a la medida y emitir propuestas en tiempo reducido.
- **Usuarios Secundarios / Operativos:** Clientes potenciales (empresas o profesionales que requieren soluciones digitales web/móvil), quienes son los receptores finales de las propuestas comerciales detalladas y profesionales.

---

## 3. OBJETIVO (OUTCOME)
*(Resultado de negocio deseado o cambio de comportamiento observable; no una lista de features)*

- **Propósito Central:** Transformar el proceso manual de cotización en un flujo rápido, parametrizable y automatizado, reduciendo significativamente el tiempo de elaboración y respuesta comercial, mientras se garantiza la consistencia de precios y una presentación profesional de las propuestas en formato PDF.

---

## 4. ALCANCE INICIAL (MVP)
*(Límites y módulos funcionales prioritarios para la primera versión)*

- **Módulos Incluidos:**
  - **Catálogo de Servicios y Tarifario Parametrizable:** Registro y mantenimiento de un listado reutilizable de servicios, componentes y tarifas base para desarrollo web y móvil.
  - **Motor de Configuración y Cálculo de Cotizaciones:** Selección ágil de módulos/funcionalidades para un cliente específico, ajuste de cantidades o parámetros y cálculo automático del precio total.
  - **Gestor de Datos de Clientes y Propuestas:** Almacenamiento de la información básica de clientes e historial de cotizaciones emitidas.
  - **Generador de Documentos PDF Profesionales:** Exportación instantánea de la propuesta detallada con los servicios seleccionados, desglose de costos (breakdown), términos, condiciones y datos del cliente.
- **Exclusiones Explícitas (Fuera de Alcance):**
  - Pasarelas de pago o cobro en línea integrado (Stripe, PayPal, Culqi, etc.) para el MVP.
  - Firma digital avanzada o contratos legales auto-ejecutables.
  - Portal web autoservicio para que los clientes coticen de manera autónoma sin intervención del desarrollador.
  - Tracking automatizado de correo / CRM analítico avanzado de seguimiento de lectura.

---

## 5. RESTRICCIONES
*(Limitaciones de negocio, legales, regulatorias u operativas inquebrantables)*

- **Exportabilidad Inmutable:** La propuesta final debe exportarse obligatoriamente en formato PDF estandarizado e inmutable.
- **Operación Individual:** La solución debe ser una aplicación web liviana y de rápida navegación adaptada a la operativa de un desarrollador independiente.
- **Arquitectura BMAD (Constitución):** Toda implementación futura debe mantener la partición física estricta entre `app/backend/` y `app/frontend/`.

---

## 6. CRITERIOS DE ÉXITO
*(Métricas o evidencias para determinar si la solución resolvió el problema)*

- **Indicador Primario:** `⚠️ [PROPUESTO]:` Reducción del tiempo promedio de elaboración y envío de cotizaciones a menos de 10 minutos por propuesta.
- **Evidencia Cualitativa:** Emisión de propuestas comerciales claras, detalladas, con desglose transparente de costos y términos en PDF profesional, sin errores de cálculo manuales.

---

## 7. SUPUESTOS
*(Hipótesis asumidas como verdaderas que condicionan la viabilidad de la solución y requieren validación)*

- `⚠️ SUPUESTO:` Las actividades y componentes de desarrollo web y móvil se pueden estructurar en tarifas base o unidades estándar reutilizables (ej. por horas, por complejidad o por módulo).
- `⚠️ SUPUESTO:` Los clientes potenciales aceptan y prefieren recibir propuestas digitales en formato PDF enviadas por vías electrónicas.
- `⚠️ SUPUESTO:` La aplicación utilizará una moneda base configurable (ej. Soles - PEN o Dólares - USD) para el cálculo de presupuestos.

---

## 8. PREGUNTAS ABIERTAS
*(Vacíos críticos de información que deben resolverse antes o durante la fase de Management)*

1. ❓ No documentado: ¿Qué moneda(s) principal(es) (ej. PEN, USD) y régimen tributario/impuestos (ej. IGV, Retención de 4ta Categoría) deben contemplarse en el desglose de la cotización?
2. ❓ No documentado: ¿Existe una plantilla o identidad visual corporativa previa (logo, paleta de colores) que deba ser incorporada por defecto en el generador de PDF?
3. ❓ No documentado: ¿Se requiere gestionar estados de validez para las cotizaciones (ej. Borrador, Enviada, Aprobada, Vencida)?

---

## 9. ORDEN DE DELEGACIÓN PARA EL TRACKER (PAUSA OBLIGATORIA HITL)
*(Al finalizar el Product Brief, el flujo entra en pausa obligatoria Human-in-the-Loop para revisión humana. La activación del Product Manager depende de utils/approve_step.py. REGLA ESTRICTA: Usa siempre el nombre en texto plano "product-manager", NUNCA la etiqueta "@PM:" para evitar disparos accidentales en el orquestador).*

@HUMANO: El Product Brief pb_cotizador_freelance.md está listo para revisión en files/product-analyst/. Por favor, valida el alcance y ejecuta `python utils/approve_step.py` para autorizar formalmente la transición hacia el product-manager.
