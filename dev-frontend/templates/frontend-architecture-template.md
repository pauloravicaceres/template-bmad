---
description: 'Plantilla maestra para la generación y mantenimiento de la documentación de arquitectura viva del Frontend.'
---

# 🏗️ PLANTILLA MAESTRA: ARQUITECTURA FRONTEND VIVA (`frontend-architecture.md`)

## 🎯 OBJETIVO Y REGLA CRÍTICA DE RENDERIZADO SELECTIVO
Este documento dicta la estructura obligatoria del archivo `frontend-architecture.md` que debes mantener en el directorio `docs/dev-frontend/frontend-architecture.md`. 

**🚨 REGLA CRÍTICA DE RENDERIZADO SELECTIVO:** 
NO debes regenerar todos los diagramas o secciones desde cero en cada iteración. Al implementar una nueva Historia de Usuario (HU), debes mantener la estructura de este documento intacta y **SOLO modificar, expandir o detallar con código Mermaid aquellas secciones (rutas, estado, componentes, flujos, etc.) que hayan sido creadas o alteradas por la HU actual**. Lo que no se tocó, se mantiene exactamente igual.

---

## 📄 ESTRUCTURA OBLIGATORIA DEL DOCUMENTO CONSOLIDADO

Tu archivo `frontend-architecture.md` debe contener las siguientes secciones. Completa y actualiza cada una utilizando la sintaxis de Markdown y diagramas de Mermaid correspondientes:

### 1. Información General y Objetivo
- Nombre del sistema, versión, fecha de última actualización, equipo.
- Descripción breve del problema que resuelve, usuarios objetivo y principales funcionalidades.

### 2. Contexto y Arquitectura General (Diagramas C4)
- **Diagrama de Contexto:** Diagrama `flowchart` de Mermaid (Nivel 1 C4) mostrando los actores y sistemas externos.
- **Diagrama de Arquitectura/Contenedores:** Diagrama `flowchart` de Mermaid (Nivel 2/3 C4) mostrando los grandes bloques del frontend (UI, Pages, Layouts, State, Services, API Client, etc.) y su comunicación.

### 3. Estructura del Proyecto (Módulos) y Enrutamiento
- **Módulos:** Tabla o lista descriptiva de la estructura de carpetas (`pages/`, `components/`, `stores/`, etc.) y sus responsabilidades.
- **Diagrama de Enrutamiento (Routing):** Diagrama `flowchart` de Mermaid que refleje las rutas públicas, privadas y de layout. *(Actualiza esto cuando agregues nuevas páginas).*

### 4. Gestión de Estado, Autenticación y Autorización
- **Flujo de Autenticación/Autorización:** Diagrama de secuencia (`sequenceDiagram`) o flujo documentando el login, validación de sesión y guards.
- **Diagrama de Estado (ej. Pinia/Redux):** Diagrama que explique cómo fluye el estado desde la UI hacia los stores y hacia la API. *(Añade aquí los flujos de estado críticos nuevos).*

### 5. Comunicación con Backend y Manejo de Errores
- **Interacción API:** Diagramas de secuencia que expliquen la interacción principal entre UI -> Store/Service -> Backend para las funcionalidades más importantes.
- **Manejo de Errores:** Explicación o diagrama de cómo se manejan y muestran los errores HTTP (401, 404, 500, etc.) a lo largo de la app.

### 6. Registros de Decisiones de Arquitectura (ADRs)
- Un listado de las decisiones arquitectónicas importantes tomadas durante el desarrollo de las HUs.
- Cada ADR debe documentar: **Contexto**, **Decisión Tomada**, **Consecuencias** (positivas y negativas). *(Añade nuevos ADRs cuando tomes decisiones técnicas clave durante tu iteración).*
