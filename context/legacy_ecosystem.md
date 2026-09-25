# 🏛️ Contexto de Ecosistema Legacy: Sistema de Gestión de Leasing

Este documento define la arquitectura preexistente (Brownfield), la infraestructura operativa y el dominio de negocio del sistema actual. **Cualquier nueva iniciativa, refactorización o integración debe respetar estas directrices y acoplarse a esta infraestructura.**

---

## 1. ⚙️ Stack Tecnológico Actual (Restricciones Duras)

El sistema central está construido sobre una arquitectura monolítica tradicional de Microsoft. No se permite la migración destructiva; las nuevas integraciones deben ser compatibles.

*   **Frontend / Capa de Presentación:** Aplicación web monolítica basada en páginas `.aspx` (WebForms).
*   **Framework Base:** .NET Framework 4.8.
*   **Base de Datos Principal:** Microsoft SQL Server (Relacional).
*   **Componentes Nativos (Legacy):** El sistema depende fuertemente de componentes **COM+** para lógica de negocio crítica y transacciones pesadas a nivel de sistema operativo.
*   **Gestión de Archivos:** El aplicativo cuenta con un módulo de importación y procesamiento masivo de archivos **Excel** (vital para la carga de simulaciones, cronogramas y activos).

## 2. 🖥️ Infraestructura y Despliegue

La topología de producción opera bajo un entorno On-Premise/IaaS altamente acoplado a Windows Server.

*   **Nodos de Cómputo:** Despliegue activo-activo en 2 servidores principales:
    *   Nodo 1: `s511vp06`
    *   Nodo 2: `s511vp07` *(Nota: Se asume topología de doble nodo para el balanceador)*
*   **Balanceo de Carga:** El tráfico HTTP/HTTPS es distribuido entre ambos nodos mediante un balanceador de carga configurado para afinidad de sesión (Sticky Sessions) requerida por el estado de las aplicaciones `.aspx`.
*   **Integraciones de Red (API/Servicios):** El sistema expone y consume de forma síncrona servicios **SOAP** (XML) para la validación de clientes, reportes regulatorios y contabilidad.

---

## 3. 🏢 Dominio de Negocio: Core de Leasing Financiero

Cualquier agente (Business Analyst, Data Architect) que interactúe con este ecosistema debe comprender el modelo de negocio subyacente. El sistema gestiona todo el ciclo de vida del **Leasing**.

### Definición del Producto
El leasing es un contrato mediante el cual nuestra entidad financiera adquiere un bien solicitado por un cliente y se lo cede para su uso durante un periodo determinado, a cambio de pagos periódicos (cuotas). Permite a las empresas operar con activos clave sin afectar su capital de trabajo.

### Flujo Operativo Estándar (Máquina de Estados)
La arquitectura lógica de cualquier nueva historia de usuario debe contemplar este ciclo de vida:
1. **Elección del activo:** El cliente identifica el bien (vehículo, maquinaria, etc.).
2. **Evaluación y aprobación:** Análisis del perfil crediticio.
3. **Compra del bien:** La entidad adquiere el activo al proveedor.
4. **Cesión de uso:** El cliente utiliza el bien (sin ser propietario aún).
5. **Pago de cuotas:** Cronograma de pagos que incluye financiamiento, intereses y condiciones.
6. **Opción de compra final (Valor Residual):** Al término del contrato, el cliente adquiere el activo pagando un valor previamente definido.

### Modalidades de Leasing Soportadas en Base de Datos
El modelo de datos (SQL Server) clasifica los contratos bajo los siguientes tipos:
*   **Leasing Financiero:** Incluye opción de compra final obligatoria.
*   **Leasing Operativo:** Uso temporal sin obligación de compra (enfoque en renovación).
*   **Leasing Vehicular:** Flotas, autos, camiones (preservación de liquidez).
*   **Leasing de Maquinarias:** Sectores construcción, minería, manufactura.
*   **Leasing Inmobiliario:** Oficinas, almacenes, plantas (pagos periódicos con opción de compra).
*   **Leaseback:** La empresa vende su propio activo a la entidad y lo arrienda de vuelta para obtener liquidez inmediata sin perder operatividad.

---

## ⚠️ Directivas para Agentes BMAD

*   **@SA (Solutions Architect):** Al generar los `tech_guidelines.md`, si se requiere una nueva UI o API externa, esta debe poder convivir con el balanceador actual o comunicarse con el sistema vía servicios SOAP/REST empaquetados, sin exigir la reescritura de los componentes COM+.
*   **@DA (Data Architect):** Cualquier extensión al MER debe diseñarse en dialecto T-SQL (SQL Server). No se admiten propuestas en PostgreSQL ni arquitecturas de bases de datos NoSQL para el Core transaccional.
*   **@API (API Architect):** Si se diseña una nueva interfaz, tener en cuenta que las transacciones complejas podrían necesitar invocar los servicios SOAP o procedimientos almacenados existentes en el servidor SQL.