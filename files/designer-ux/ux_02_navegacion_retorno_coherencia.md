# ESPECIFICACIÓN DE DISEÑO UX: Integración de Navegación de Retorno y Coherencia Multirruta

- **Historia de Usuario Fuente:** `hu_02_navegacion_retorno_coherencia.md`
- **Fecha de Diseño:** 25-09-2026
- **Diseñador UX:** Agente UX Senior BMAD
- **Modo de Operación:** Brownfield (Subordinado a `legacy_ecosystem.md`)

---

## 1. RESUMEN DE DISEÑO
- **Historia Base:** Integración de Navegación de Retorno y Coherencia Multirruta (HU-02).
- **Enfoque de Usabilidad:** Estandarización de la experiencia de navegación bidireccional entre la vista de Experiencia (`/experiencia`) y la tarjeta de identidad principal (`/`). El diseño incorpora un control de retorno intuitivo (`[← Volver al Perfil]`) en la cabecera superior y reutiliza el layout base compartido (`Layout.astro`), garantizando que la transición entre páginas sea inmediata (< 1.0s) y preserve rigurosamente la preferencia de tema (Light/Dark Mode) almacenada en `localStorage` con cero parpadeo visual (Zero FOUT/FOUC).

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Navegación de Retorno desde Vista de Experiencia (Happy Path)
- **Escenario Cubierto:** CA-01 — Retorno Intuitivo a la Tarjeta Principal
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|  [ ← Volver al Perfil ]                                     [ (☀️) 🌙 ]|
|  ( Enlace interactivo con foco accesible y hover )                    |
|                                                                       |
|  ===================================================================  |
|  TRAYECTORIA & EXPERIENCIA PROFESIONAL                                |
|  ===================================================================  |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  | [ Tech Corp Inc. ]                          [ 2022 - Presente ] |  |
|  | Senior Frontend Specialist                                      |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|             +-------------------------------------------+             |
|             |   [ [• Experiencia] ]     [ Estudios ⤓ ]  |             |
|             +-------------------------------------------+             |
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz (Brownfield / Tailwind CSS):** 
  - **Disparador:** Clic o pulsación sobre `[← Volver al Perfil]` (`href="/"`) o la opción de retorno.
  - **Comportamiento y Componente:** Enlace semántico `<a href="/" class="inline-flex items-center text-sm font-medium text-neutral-600 hover:text-neutral-900 dark:text-neutral-400 dark:hover:text-white transition-colors duration-150">`. Redirige fluidamente a la raíz `/` en menos de 1 segundo mediante enrutamiento estático nativo sin recargas pesadas.

---

### Estado 2: Coherencia Multirruta y Preservación de Dark/Light Mode (Happy Path Complementario)
- **Escenario Cubierto:** CA-02 — Preservación de Estado de Tema y Cero Parpadeo (Zero FOUT)
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|  [ MODO OSCURO PERSISTENTE EN AMBAS RUTAS ( / y /experiencia ) ]      |
|  Cabecera Global: [ ← Volver al Perfil ]                    [ ☀️ (🌙) ]|
|                                                                       |
|                     +---------------------------+                     |
|                     |        ( FOTOGRAFÍA       |                     |
|                     |          DE PERFIL )      |                     |
|                     +---------------------------+                     |
|                                                                       |
|                      ===========================                      |
|                      NOMBRE COMPLETO PROFESIONAL                      |
|                      ===========================                      |
|                                                                       |
|             +-------------------------------------------+             |
|             |   [ Experiencia ]     [ Estudios ⤓ ]      |             |
|             +-------------------------------------------+             |
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz (Brownfield / Script Anti-FOUT):**
  - **Disparador:** Navegación bidireccional entre `/` y `/experiencia` habiendo seleccionado Dark Mode.
  - **Comportamiento y Estado:** El script inline síncrono ubicado en el `<head>` de `Layout.astro` inyecta la clase `dark` en el elemento `<html>` antes del primer pintado (First Contentful Paint), garantizando que los fondos oscuros (`#121212`) y tipografías claras no sufran destellos blancos ni reinicios de estado.

---

### Estado 3: Resiliencia ante Refresco Forzado o Historial del Navegador (Sad Path / Fallback)
- **Escenario Cubierto:** CA-03 — Resiliencia de Enrutamiento y Coherencia Multirruta
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|  [ NAVEGACIÓN HISTORIAL / HARD REFRESH F5 ]                 [ (☀️) 🌙 ]|
|                                                                       |
|  ===================================================================  |
|  TRAYECTORIA & EXPERIENCIA PROFESIONAL                                |
|  ===================================================================  |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  | [ Módulo de Experiencia Renderizado Estáticamente ]             |  |
|  | Disposición tipográfica intacta y sin estados inconsistentes.   |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|             +-------------------------------------------+             |
|             |   [ [• Experiencia] ]     [ Estudios ⤓ ]  |             |
|             +-------------------------------------------+             |
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz (Brownfield / Resiliencia SSG):**
  - **Disparador:** Refresco directo en el navegador (F5), navegación hacia atrás/adelante (`history.back()`) o entrada directa por URL.
  - **Comportamiento de Resiliencia:** Al estar pre-renderizada en Astro como página estática independiente (`src/pages/experiencia.astro`), la vista se hidrata instantáneamente sin depender de APIs externas ni routers complejos de cliente, garantizando estabilidad total del layout.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES
- **Heurísticas Aplicadas:**
  - *Heurística de Consistencia Global:* Ubicación uniforme del conmutador de tema en la esquina superior derecha y del control de retorno en la superior izquierda en todas las vistas complementarias.
  - *Heurística de Cero Fricción Cognitiva:* La barra de navegación inferior permanece fija y visible en ambas rutas para permitir acceso directo a la descarga de estudios o cambio de sección.
- **Bloqueos de UX / Consultas para BA:** Ninguno. Se ha completado el diseño visual del 100% de las épicas del MVP.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Auditoría de Alcance: Épicas diseñadas = 2 / Épicas del backlog = 2. Conclusión del alcance del MVP en la Fase de Diseño UX).*

@SA: El diseño visual del MVP ha concluido exitosamente. Por favor, lee el Product Brief y el MVP, y define el stack tecnológico y las reglas arquitectónicas del proyecto.
