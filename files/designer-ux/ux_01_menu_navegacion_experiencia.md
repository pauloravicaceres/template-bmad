# ESPECIFICACIÓN DE DISEÑO UX: Componente Menú de Navegación y Enrutamiento a Vista de Experiencia

- **Historia de Usuario Fuente:** `hu_01_menu_navegacion_experiencia.md`
- **Fecha de Diseño:** 25-09-2026
- **Diseñador UX:** Agente UX Senior BMAD
- **Modo de Operación:** Brownfield (Subordinado a `legacy_ecosystem.md`)

---

## 1. RESUMEN DE DISEÑO
- **Historia Base:** Componente Menú de Navegación y Enrutamiento a Vista de Experiencia (HU-01).
- **Enfoque de Usabilidad:** Integración no invasiva de una barra de navegación horizontal ultra-minimalista directamente bajo el bloque de identidad (fotografía y nombre), preservando la jerarquía central y la estética limpia del ecosistema Astro + Tailwind CSS. En la vista de "Experiencia", se mantiene el mismo layout global con cabecera y conmutador de tema, incorporando un contenedor estructurado para la trayectoria profesional y un botón/enlace de retorno intuitivo hacia el perfil principal con cero parpadeo (Zero FOUT).

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Vista Principal con Menú de Navegación Integrado (Happy Path)
- **Escenario Cubierto:** CA-01 — Visualización e Integración Armónica del Menú de Navegación
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|  [ MODO ACTIVO: Light / Dark ]                              [ (☀️) 🌙 ]|
|                                                                       |
|                     +---------------------------+                     |
|                     |                           |                     |
|                     |        ( FOTOGRAFÍA       |                     |
|                     |          DE PERFIL        |                     |
|                     |          EN ALTA          |                     |
|                     |        RESOLUCIÓN )       |                     |
|                     |                           |                     |
|                     +---------------------------+                     |
|                                                                       |
|                      ===========================                      |
|                      NOMBRE COMPLETO PROFESIONAL                      |
|                      ===========================                      |
|                                                                       |
|             +-------------------------------------------+             |
|             |   [ [ Experiencia ] ]     [ Estudios ⤓ ]  |             |
|             +-------------------------------------------+             |
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz (Brownfield / Tailwind CSS):** 
  - **Disparador:** Renderizado de la página principal (`/`).
  - **Comportamiento y Componente:** El componente de navegación se ubica con un margen superior balanceado (`mt-6`). Cada opción se representa como un enlace interactivo o píldora accesible con estados `hover:opacity-80`, `focus:ring-2 focus:ring-offset-2` y colores subordinados al tema activo (`text-neutral-800 dark:text-neutral-200`, `border border-neutral-300 dark:border-neutral-700`). No añade sobrepeso de JavaScript, operando como enlaces `<a>` nativos semánticos.

---

### Estado 2: Vista Complementaria Base de Experiencia (Happy Path)
- **Escenario Cubierto:** CA-02 — Enrutamiento y Navegación Exitosa a la Vista de Experiencia
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|  [ ← Volver al Perfil ]                                     [ (☀️) 🌙 ]|
|                                                                       |
|  ===================================================================  |
|  TRAYECTORIA & EXPERIENCIA PROFESIONAL                                |
|  ===================================================================  |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  | [ Módulo Estructural Base de Experiencia ]                       |  |
|  |                                                                 |  |
|  | • Cargo / Rol Principal ............................ Periodo    |  |
|  |   Empresa / Organización | Descripción sintética...              |  |
|  |                                                                 |  |
|  | • Cargo / Rol Previo ............................... Periodo    |  |
|  |   Empresa / Organización | Descripción sintética...              |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|             +-------------------------------------------+             |
|             |   [ [• Experiencia] ]     [ Estudios ⤓ ]  |             |
|             +-------------------------------------------+             |
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz (Brownfield / Tailwind CSS):**
  - **Disparador:** Clic o interacción con el enlace `Experiencia` (`/experiencia`).
  - **Comportamiento y Transición:** Enrutamiento estático SSG con carga instantánea (< 1s). Reutiliza `Layout.astro` garantizando que el script inline en `<head>` mantenga la clase `.dark` activa sin parpadeos visuales. En la barra de navegación inferior, la opción "Experiencia" adopta el estado activo destacado (`bg-neutral-900 text-white dark:bg-neutral-100 dark:text-neutral-900`).

---

### Estado 3: Mecanismo de Retorno y Manejo de Rutas Resiliente (Sad Path / Fallback)
- **Escenario Cubierto:** CA-03 — Mecanismo de Retorno a la Vista Principal y Resiliencia de Enrutamiento
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|  [ ← Inicio / Retorno Seguro ]                              [ (☀️) 🌙 ]|
|                                                                       |
|                                                                       |
|                     +---------------------------+                     |
|                     |        [  ⚠️ 404  ]        |                     |
|                     |    Sección en desarrollo  |                     |
|                     |    o ruta no encontrada   |                     |
|                     +---------------------------+                     |
|                                                                       |
|              La información solicitada no se encuentra disponible.    |
|                                                                       |
|                        +-----------------------+                      |
|                        | [← Regresar al Perfil]|                      |
|                        +-----------------------+                      |
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz (Brownfield / Resiliencia):**
  - **Disparador:** Clic en botón `[← Volver al Perfil]` desde `/experiencia`, o acceso a ruta inválida.
  - **Comportamiento de Resiliencia:** Redirección limpia hacia la raíz `/`. La preferencia de tema permanece intacta en `localStorage` (`theme_preference`), asegurando que tanto la vista de error como la vista de retorno compartan el contraste y la paleta sin pérdida de estado ni recargas forzadas de scripts externos.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES
- **Heurísticas Aplicadas:**
  - *Heurística de Consistencia Brownfield:* Se preserva el diseño del avatar 1:1 y la tipografía base definida en la Épica P1 previa, agregando el menú como una extensión natural en la parte inferior del contenedor central.
  - *Heurística de Accesibilidad y Navegación:* Botón de retorno visible y accesible en la esquina superior izquierda de las vistas secundarias con indicador de foco claro (`focus-visible`).
- **Bloqueos de UX / Consultas para BA:** Ninguno. La especificación se integra 100% con los requerimientos aprobados y las invariantes del ecosistema SSG.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Auditoría de Alcance: Épicas diseñadas = 1 / Épicas del backlog = 2 en el ciclo actual. El MVP continúa hacia la siguiente épica).*

@PM: Los wireframes para la HU Menú de Navegación y Enrutamiento a Vista de Experiencia están listos en files/designer-ux/ux_01_menu_navegacion_experiencia.md. Por favor, lee el historial, identifica la siguiente Épica pendiente en el backlog y asígnala al BA.
