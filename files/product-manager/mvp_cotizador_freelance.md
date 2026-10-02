# PLAN ESTRATÉGICO Y BACKLOG DEL MVP: Cotizador Freelance para Desarrollador de Software

- **Documento Fuente:** files/product-analyst/pb_cotizador_freelance.md
- **Fecha de Elaboración:** 02-10-2026
- **Product Manager:** Agente Orquestador BMAD (Fase M)

---

## 1. VISIÓN ESTRATÉGICA DEL MVP

- **Foco de Gestión:** Automatizar y estandarizar la creación de propuestas comerciales mediante una aplicación web liviana que gestione un catálogo parametrizable de servicios, calcule precios en tiempo real y exporte documentos PDF profesionales e inmutables.
- **Criterio de Éxito Rector:** Reducción del tiempo promedio de elaboración y envío de cotizaciones a menos de 10 minutos por propuesta comercial.

---

## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)

Organización del alcance en bloques de valor estructurados bajo el estándar de Ruta Crítica (P1 a P4):

### [P1] Épica: Catálogo de Servicios y Tarifario Parametrizable
- **Descripción de Negocio:** Registro y gestión centralizada de un listado reutilizable de servicios, componentes y tarifas base para desarrollo web y móvil (horas, complejidad o módulos).
- **Justificación de Prioridad:** Constituye el cimiento de datos maestros indispensable sobre el cual opera el motor de cálculo y la personalización de propuestas.
- **Trazabilidad PRD:** Sección 4 - Alcance Inicial (Catálogo de Servicios y Tarifario Parametrizable) y Sección 7 - Supuestos.

### [P2] Épica: Motor de Configuración y Cálculo de Cotizaciones
- **Descripción de Negocio:** Selección interactiva de servicios/módulos para un cliente específico, ajuste dinámico de cantidades/parámetros y cálculo automático del precio total de la propuesta.
- **Justificación de Prioridad:** Representa la transacción core que elimina el cálculo manual y acelera el tiempo de elaboración.
- **Trazabilidad PRD:** Sección 3 - Objetivo Central y Sección 4 - Alcance Inicial (Motor de Configuración y Cálculo).

### [P3] Épica: Gestor de Datos de Clientes y Cotizaciones
- **Descripción de Negocio:** Almacenamiento de datos de contacto de clientes potenciales e historial centralizado de cotizaciones generadas.
- **Justificación de Prioridad:** Ocupa el tercer nivel al permitir la trazabilidad, reutilización y consulta de propuestas previas para cada cliente.
- **Trazabilidad PRD:** Sección 4 - Alcance Inicial (Gestor de Datos de Clientes y Propuestas).

### [P4] Épica: Generador de Documentos PDF Profesionales
- **Descripción de Negocio:** Exportación inmutable y con formato profesional de la cotización detallada con desglose de costos (breakdown), términos, condiciones y datos del cliente.
- **Justificación de Prioridad:** Es el entregable final visible para el cliente receptor, requiriendo la previa selección y cálculo de servicios (P1/P2/P3).
- **Trazabilidad PRD:** Sección 4 - Alcance Inicial (Generador de Documentos PDF) y Sección 5 - Restricciones (Exportabilidad Inmutable).

---

## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

### Bloqueantes Potenciales
- Estrutura de tarifas heterogénea: Si los componentes web/móvil no se logran estandarizar en unidades base reutilizables, se requerirá un esfuerzo adicional en la parametrización del catálogo.
- Dependencia de arquitectura BMAD: Mantener la separación estricta entre `app/backend/` y `app/frontend/`.

### Ambigüedades de Negocio (Para Control del BA)
- ❓ No documentado: Definición de moneda base (PEN / USD) y desglose de régimen tributario/impuestos (IGV, Retención 4ta Categoría).
- ❓ No documentado: Requerimiento de plantilla o identidad visual corporativa (logo, colores) para la generación del PDF.
- ❓ No documentado: Ciclo de vida y gestión de estados de las cotizaciones (Borrador, Enviada, Aprobada, Vencida).

---

## 4. ORDEN DE DELEGACIÓN PARA EL BA Y GITOPS

⚠️ **IDENTIFICADOR UNIVERSAL ESTRICTO ASIGNADO:** `002-HU_motor_configuracion_calculo_cotizaciones`

@WATCHER: GITOPS-BRANCH-CREATE feat/002-HU_motor_configuracion_calculo_cotizaciones
@BA: El Product Manager delega formalmente la especificación de la siguiente Historia de Usuario de la Ruta Crítica ([P2] Motor de Configuración y Cálculo de Cotizaciones). Utiliza obligatoriamente el identificador universal estricto `002-HU_motor_configuracion_calculo_cotizaciones` para crear el archivo físico `files/business-analyst/002-HU_motor_configuracion_calculo_cotizaciones.md` e iniciar la redacción de las Historias de Usuario y Criterios de Aceptación.

