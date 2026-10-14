---
description: 'Plantilla maestra para la generación y mantenimiento de la documentación de arquitectura viva del Backend.'
---

# 🏗️ PLANTILLA MAESTRA: ARQUITECTURA BACKEND VIVA (`backend-architecture.md`)

## 🎯 OBJETIVO Y REGLA CRÍTICA DE RENDERIZADO SELECTIVO
Este documento dicta la estructura obligatoria del archivo `backend-architecture.md` que debes mantener en el directorio `docs/dev-backend/backend-architecture.md`.

**🚨 REGLA CRÍTICA DE RENDERIZADO SELECTIVO:** 
NO debes regenerar todos los diagramas o secciones desde cero en cada iteración. Al implementar una nueva Historia de Usuario (HU), debes mantener la estructura de este documento intacta y **SOLO modificar, expandir o detallar con código Mermaid aquellas secciones (rutas, entidades, modelo de datos, flujos asíncronos) que hayan sido creadas o alteradas por la HU actual**. Lo que no se tocó, se mantiene intacto o se marca implícitamente como "Sin cambios en esta iteración".

---

## 📄 ESTRUCTURA OBLIGATORIA DEL DOCUMENTO CONSOLIDADO

Tu archivo `backend-architecture.md` debe contener las siguientes secciones. Completa y actualiza cada una utilizando la sintaxis de Markdown y diagramas de Mermaid correspondientes:

### 1. Contexto y Contenedores (C4)
- **Contexto:** Diagrama `flowchart` de Mermaid mostrando la relación del backend con frontends, bases de datos, Identity Providers y APIs externas.
- **Contenedores:** Diagrama mostrando las grandes piezas del backend (API Layer, Application, Domain, Infrastructure, Database, etc.).

### 2. Arquitectura de Capas y Módulos
- **Arquitectura Clean/Hexagonal:** Diagrama de dependencias entre Presentation, Application, Domain, e Infrastructure.
- **Estructura de Módulos:** Listado o árbol reflejando la estructura física del código base (ej. `api/`, `application/`, `domain/`, `infrastructure/`). *(Actualiza cuando añadas módulos nuevos).*

### 3. Modelo de Datos y Persistencia
- **Diagrama Entidad-Relación (ERD):** Diagrama `erDiagram` de Mermaid con las entidades principales y sus relaciones. *(Actualiza cuando modifiques o añadas tablas/entidades por una HU).*
- **Flujo de Repositorios:** Diagrama que muestre cómo el dominio define las interfaces y la capa de infraestructura implementa el ORM/Driver de DB.

### 4. Flujo de Petición y Secuencias Críticas
- **Flujo General:** Diagrama de cómo atraviesa una petición el sistema (Middleware -> Auth -> Router -> Validator -> Use Case -> DB -> Response).
- **Diagramas de Secuencia (Casos de Uso Críticos):** Diagramas `sequenceDiagram` para los endpoints más importantes o complejos (ej. integraciones asíncronas, creación compleja de entidades). *(Añade diagramas aquí solo para casos de uso complejos nuevos).*

### 5. Seguridad y Manejo de Errores
- **Autenticación/Autorización:** Diagrama documentando el flujo de login, validación de token y chequeo de permisos.
- **Matriz de Manejo Global de Errores:** Explicación o diagrama de cómo se mapean las excepciones de dominio a excepciones HTTP (400, 401, 403, 404, 409, 500) en el Global Exception Handler.

### 6. Registros de Decisiones de Arquitectura (ADRs)
- Un listado de las decisiones arquitectónicas importantes tomadas durante el desarrollo.
- Cada ADR debe documentar: **Contexto**, **Decisión Tomada**, **Consecuencias** (positivas y negativas). *(Añade nuevos ADRs cuando tomes decisiones técnicas clave durante tu iteración, como elección de librerías, estrategias de caché o diseño de base de datos).*
