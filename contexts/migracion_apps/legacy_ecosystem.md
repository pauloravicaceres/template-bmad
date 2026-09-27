# 🏛️ Contexto de Modernización: Strangler Fig Pattern (WebForms 4.8 a .NET 10 / Angular 22)

Este proyecto se encuentra en una fase de **Modernización Progresiva**. El sistema central es un monolito legacy en ASP.NET Framework 4.8 (WebForms). Las nuevas funcionalidades y refactorizaciones DEBEN regirse por el patrón **Strangler Fig**, aislando el código nuevo del viejo sin romper la base de datos compartida.

Las siguientes reglas representan la *Lex Superior* del proyecto. Queda ESTRICTAMENTE PROHIBIDO para cualquier agente (SA, DA, API, UX, QT) proponer o aceptar stacks que violen estas directrices.

---

## 1. 📂 Ubicación e Interoperabilidad del Proyecto Legacy
* **Ruta del Repositorio Legacy:** `./src/legacy-webforms/` (o la ruta absoluta configurada en el entorno).
* **Directiva de Exploración:** Los agentes pueden usar `list_dir` o `read_file` en esta ruta únicamente para auditar reglas de negocio antiguas o revisar esquemas, pero tienen **PROHIBIDO modificar** cualquier archivo `.aspx`, `.cs` o `Web.config` preexistente.
* **Interoperabilidad:** El tráfico entre el frontend moderno y el legacy se gestionará externamente (ej. mediante YARP o un API Gateway). Las nuevas APIs no deben acoplarse a las sesiones de WebForms.

---

## 2. 🖥️ Stack Frontend Objetivo (Nueva Ley de UI)
* **Framework:** Angular 22.
* **Paradigma Reactivo:** Arquitectura 100% **Zoneless** utilizando **Signals** para el manejo de estado y reactividad.
* **Librería de Componentes UI:** PrimeNG v22.1.1. Queda PROHIBIDO generar código ASPX, WebForms, jQuery o invocar *Postbacks*.

### 📐 Directiva Estricta de Maquetación UX (Skeleton vs. Theme)
El agente `@UX` DEBE calcar la **distribución estructural (Skeleton)** del sistema legacy para mantener la familiaridad del usuario, pero tiene ESTRICTAMENTE PROHIBIDO heredar su **capa visual corporativa (Theme)**.
* **✅ ESTRUCTURA (Calcar):** Layout con Topbar, Sidebar izquierdo colapsable, Breadcrumbs, y formularios de filtros densos en grillas sobre tablas de datos paginadas.
* **🚫 ESTILOS (Omitir):** Ignorar colores antiguos, tipografías y CSS custom. Usar 100% el tema neutral de PrimeNG (`<p-table>`, `<p-sidebar>`).

---

## 3. ⚙️ Stack Backend Objetivo (Nueva Ley de APIs)
El nuevo código backend debe ser completamente independiente del framework 4.8.
* **Arquitectura:** Modular Monolith (Modulith) en .NET 10 utilizando Minimal APIs y C# 14. Queda PROHIBIDO generar servicios WCF o ASMX.
* **Patrones Core:** Domain-Driven Design (DDD), Vertical Slice Architecture (VSA) por módulos funcionales, y CQRS puro utilizando la librería **MediatR**.
* **Infraestructura Transversal:** Pipeline Behaviors de MediatR para validaciones (FluentValidation) y Serilog para trazabilidad.

---

## 4. 🗄️ Persistencia y Base de Datos (Brownfield Estricto)
* **Base de Datos Compartida:** Microsoft SQL Server (Dialecto T-SQL). La base de datos es compartida en tiempo real con el sistema legacy en producción.
* **🚫 REGLA DE INMUTABILIDAD PARA EL @DA:** El Data Architect tiene ESTRICTAMENTE PROHIBIDO alterar, borrar o renombrar tablas, columnas o constraints existentes.
* **ORM Obligatorio:** Entity Framework Core. El mapeo debe hacerse utilizando el enfoque *Code-First* con atributos de data annotations (`[Table("NombreTablaLegacy")]` y `[Column("NombreColumnaLegacy")]`) o Fluent API, adaptando las clases limpias de C# a la estructura cruda y preexistente de SQL Server.