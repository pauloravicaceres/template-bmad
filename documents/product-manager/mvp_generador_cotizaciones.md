# PLAN ESTRATÉGICO Y BACKLOG DEL MVP: Generador de Cotizaciones Web

- **Documento Fuente:** pb_generador_cotizaciones.md
- **Fecha de Elaboración:** 2026-10-02
- **Product Manager:** Agente Orquestador BMAD (Fase M)

---

## 1. VISIÓN ESTRATÉGICA DEL MVP

- **Foco de Gestión:** Estandarizar y parametrizar el proceso de estimación comercial para desarrolladores independientes en Perú, construyendo un flujo ágil que permita seleccionar servicios, ajustar parámetros, calcular subtotales/totales automáticamente y emitir una propuesta formal en PDF en menos de 5 minutos.
- **Criterio de Éxito Rector:** Reducción del tiempo promedio de elaboración de cotizaciones a menos de 5 minutos por propuesta y eliminación total de errores de cálculo manual e inconsistencias de precios en las propuestas emitidas en PDF.

---

## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)

Organización del alcance en bloques de valor estructurados bajo el estándar de Ruta Crítica (P1 a P3):

### [P1] Épica: Motor de Cálculo y Configuración Interactiva de Cotizaciones
- **Descripción de Negocio:** Permite la selección de servicios/módulos web, ajuste de cantidades, personalización de parámetros según la necesidad del cliente y cómputo automático en tiempo real de subtotales, totales y desglose de precios del proyecto.
- **Justificación de Prioridad:** Constituye la transacción nuclear (Core Transaccional) del producto; sin el cálculo automático y la configuración interactiva de costos, el sistema carece de valor operativo.
- **Trazabilidad PRD:** Sección 4 - Alcance Inicial (Configurador Interactivo de Cotizaciones y Motor de Cálculo Automático).

### [P2] Épica: Catálogo Parametrizable de Servicios y Tarifas Base
- **Descripción de Negocio:** Registro y administración de servicios, ítems y funcionalidades predefinidas para sitios y aplicaciones web con sus tarifas base parametrizadas.
- **Justificación de Prioridad:** Ocupa el segundo nivel de prelación como componente de datos maestros que alimenta y sustenta las opciones seleccionables dentro del configurador P1.
- **Trazabilidad PRD:** Sección 4 - Alcance Inicial (Catálogo Parametrizable).

### [P3] Épica: Módulo de Generación y Emisión de Documentos PDF
- **Descripción de Negocio:** Consolidación formal y exportación de la propuesta comercial en formato PDF profesional estructurado (incluyendo detalle de servicios, costos, datos del cliente y condiciones comerciales).
- **Justificación de Prioridad:** Ocupa el tercer nivel como mecanismo de entrega y consolidación final de la propuesta transaccionada para el cliente.
- **Trazabilidad PRD:** Sección 4 - Alcance Inicial (Módulo de Generación de Documentos PDF).

---

## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

### Bloqueantes Potenciales
- `⚠️ SUPUESTO:` El catálogo de servicios base puede parametrizarse inicialmente mediante un conjunto predefinido de ítems de desarrollo web comunes.
- `⚠️ SUPUESTO:` Las condiciones comerciales de los proyectos pueden estandarizarse en plantillas de texto dentro del generador.
- `⚠️ SUPUESTO:` El desarrollador independiente opera principalmente desde una computadora de escritorio/laptop para la configuración de propuestas.

### Ambigüedades de Negocio (Para Control del BA)
- `❓ No documentado:` Definición sobre si se requiere manejar impuestos locales (ej. IGV / Retención por Recibo por Honorarios) en la estructura de cálculo del PDF.
- `❓ No documentado:` Definición sobre si las condiciones comerciales y plazos de validez de la oferta son fijos o deben ser totalmente editables por cada cotización.

---

## 4. ORDEN DE DELEGACIÓN PARA EL BA Y GITOPS

Identificador Universal Estricto para la primera Historia de Usuario (P1):
`001-HU_configurador_y_calculo_cotizaciones`

@WATCHER: GITOPS-BRANCH-CREATE feat/001-HU_configurador_y_calculo_cotizaciones
@BA: Procede con el análisis detallado y la redacción de la Historia de Usuario `001-HU_configurador_y_calculo_cotizaciones.md` basada en la Épica P1 (Motor de Cálculo y Configuración Interactiva de Cotizaciones).
