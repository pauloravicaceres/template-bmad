# 🏛️ Contexto Base de Arquitectura: Modulith .NET 10 & Angular 22

Este proyecto es Greenfield a nivel de negocio, pero su arquitectura técnica, stack frontend, backend y patrones de diseño están estrictamente definidos. Los agentes (SA, DA, API, QT) DEBEN subordinarse a este documento y catalogar estas decisiones como `Aceptado (heredado)` en sus respectivos ADRs.

---

## 1. 🖥️ Stack Frontend (Restricciones para UI y UX)
* **Framework:** Angular 22.
* **Paradigma Reactivo:** Arquitectura 100% **Zoneless** utilizando **Signals** para el manejo de estado y reactividad.
* **Internacionalización:** Soporte nativo i18n desde el inicio.
* **Librería de Componentes UI:** PrimeNG v22.1.1 (https://primeng.dev/installation).
* **Directiva UX:** Los wireframes (`ux_*.md`) deben adaptarse a los componentes estándar de PrimeNG (DataTables, Dialogs, Cards) para minimizar el desarrollo de CSS custom.

---

## 2. ⚙️ Stack Backend: Modular Monolith (.NET 10)
El backend no es un monolito tradicional ni un sistema de microservicios distribuido. Es un **Modular Monolith (Modulith)** desarrollado en .NET 10 (con C# 14 / Minimal APIs).

### Patrones Estructurales Obligatorios:
* **Domain-Driven Design (DDD):** Modelado centrado en el dominio para entidades y agregados.
* **Vertical Slice Architecture (VSA):** Implementación mediante carpetas por características (Feature folders), aislando la lógica de cada caso de uso.
* **CQRS:** Separación estricta de Comandos y Consultas utilizando la librería **MediatR**.

### Cross-cutting Concerns (Infraestructura Transversal):
* **Validación y Pipeline:** Uso de *Pipeline Behaviors* de MediatR para inyectar validaciones (FluentValidation) antes de ejecutar los handlers.
* **Manejo de Errores:** Middleware global de excepciones.
* **Logging:** Integración obligatoria con **Serilog**.
* **Paginación:** Estandarizada en las respuestas de los queries CQRS.

---

## 3. 🗄️ Persistencia y Caché (Directivas para el @DA)
* **Base de Datos Principal:** Microsoft SQL Server.
* **Dialecto de Diseño:** T-SQL.
* **ORM:** Entity Framework Core utilizando enfoque *Code-First* y Migrations.
* **Caché Distribuido:** **Redis** operando como capa de acceso rápido sobre la base de datos relacional.
* **Patrones de Caché:** Implementar los patrones *Proxy*, *Decorator* y *Cache-aside* para interceptar consultas pesadas (vía pipelines de MediatR) y consultar Redis antes que impactar a SQL Server.

---

## 4. 🌐 Integración y Mensajería (Directivas para el @API y @SA)
La comunicación entre los módulos internos (ej. Catalog, Basket, Ordering) sigue reglas estrictas para permitir una futura migración a microservicios mediante el **Strangler Fig Pattern**.

* **Comunicación Síncrona (Sync):** Llamadas a métodos en proceso (In-process method calls) simulando APIs públicas para consultar datos entre módulos (ej. Catalog -> Basket).
* **Comunicación Asíncrona (Async):** Basada en eventos de dominio y de integración (Domain & Integration Events) usando **RabbitMQ** y la librería **MassTransit**.
* **Patrón de Confiabilidad:** Uso estricto del **Outbox Pattern** para garantizar la consistencia eventual y la mensajería confiable (ej. Caso de uso `BasketCheckout`).
* **Ejemplos de Eventos Obligatorios:** Publicación de `UpdatePriceChanged` (Catalog) y `BasketCheckoutEvent` (consumido desde Ordering).

---

## 5. 🔐 Seguridad e Identidad
* **Módulo de Identidad:** Desarrollo de un *User Identity Module* integrado con **Keycloak**.
* **Protocolos:** Autenticación y Autorización vía OAuth2 y flujos OpenID Connect.
* **Seguridad de APIs:** Todos los endpoints (Minimal APIs) deben estar protegidos mediante validación de Bearer Tokens.