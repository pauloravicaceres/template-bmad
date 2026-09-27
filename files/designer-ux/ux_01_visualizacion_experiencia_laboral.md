# ESPECIFICACIÓN DE DISEÑO UX: Componente y Visualización Estructurada de Experiencia Laboral

- **Historia de Usuario Fuente:** `hu_01_visualizacion_experiencia_laboral.md`
- **Fecha de Diseño:** 25-09-2026
- **Diseñador UX:** Agente UX Senior BMAD
- **Modo de Operación:** Brownfield (Subordinado a `constitution.md`)

---

## 1. RESUMEN DE DISEÑO
- **Historia Base:** Componente y Visualización Estructurada de Experiencia Laboral (HU-01).
- **Enfoque de Usabilidad:** Arquitectura de información estructurada para la vista `/experiencia`, basada en tarjetas/bloques de alta legibilidad que presentan cada posición laboral (Empresa, Cargo/Rol, Período cronológico y Lista de logros/responsabilidades concisos). La maquetación utiliza clases utilitarias de Tailwind CSS compatibles con Light Mode (`bg-white`, `border-neutral-200`, `text-neutral-900`) y Dark Mode (`dark:bg-neutral-900`, `dark:border-neutral-800`, `dark:text-neutral-100`), garantizando renderizado estático inmediato (< 1.0s) y adaptabilidad móvil mediante apilamiento vertical fluido.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Visualización Estructurada en Escritorio (Happy Path)
- **Escenario Cubierto:** CA-01 — Visualización Estructurada y Jerárquica de la Experiencia Laboral
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
|  | [ Tech Corp Inc. ]                          [ 2022 - Presente ] |  |
|  | Senior Frontend & Architecture Specialist                       |  |
|  | --------------------------------------------------------------- |  |
|  | • Liderazgo en diseño de interfaces SSG y accesibilidad WCAG AA.|  |
|  | • Optimización de Core Web Vitals alcanzando LCP < 1.0s.        |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|  +-----------------------------------------------------------------+  |
|  | [ Global Solutions Ltd. ]                       [ 2020 - 2022 ] |  |
|  | Software Developer & UI Specialist                              |  |
|  | --------------------------------------------------------------- |  |
|  | • Implementación de componentes de diseño y contratos Zod.     |  |
|  | • Integración de sistemas de conmutación de temas (Dark/Light). |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|             +-------------------------------------------+             |
|             |   [ [• Experiencia] ]     [ Estudios ⤓ ]  |             |
|             +-------------------------------------------+             |
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz (Brownfield / Tailwind CSS):** 
  - **Disparador:** Carga completa de la vista `/experiencia` en pantallas >= 768px.
  - **Comportamiento y Componente:** Cada posición se renderiza dentro de una tarjeta con borde sutil (`rounded-xl border border-neutral-200 dark:border-neutral-800 p-5 mb-4 shadow-sm`). El nombre de la empresa utiliza `font-semibold text-lg`, el cargo `text-neutral-700 dark:text-neutral-300`, el período se presenta como una píldora/badge (`px-2.5 py-0.5 text-xs font-medium rounded-full bg-neutral-100 dark:bg-neutral-800`) y las viñetas de logros usan espaciado compacto (`space-y-1 text-sm list-disc list-inside`).

---

### Estado 2: Adaptabilidad Responsiva en Móviles (Happy Path Complementario)
- **Escenario Cubierto:** CA-02 — Adaptabilidad Responsiva y Fluidez Móvil
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------+
| [← Inicio]              [ ☀️/🌙 ] |
|                                   |
| ================================= |
| EXPERIENCIA PROFESIONAL           |
| ================================= |
|                                   |
| +-------------------------------+ |
| | Tech Corp Inc.                | |
| | [ 2022 - Presente ]           | |
| | Senior Frontend Specialist    | |
| | - - - - - - - - - - - - - - - | |
| | • Liderazgo en diseño SSG.    | |
| | • Optimización de LCP < 1.0s. | |
| +-------------------------------+ |
|                                   |
| +-------------------------------+ |
| | Global Solutions Ltd.         | |
| | [ 2020 - 2022 ]               | |
| | UI & Software Specialist      | |
| | - - - - - - - - - - - - - - - | |
| | • Componentes y contratos Zod.| |
| +-------------------------------+ |
|                                   |
|     +-----------------------+     |
|     | [• Exp]  [Estudios ⤓] |     |
|     +-----------------------+     |
+-----------------------------------+
```
- **Nota de Interfaz (Brownfield / Viewport Móvil):**
  - **Disparador:** Acceso desde dispositivos móviles con pantallas estrechas (<= 480px).
  - **Comportamiento Dinámico:** Disposición vertical apilada (`flex flex-col`). El badge de período se reposiciona bajo el nombre de la empresa para evitar cualquier desbordamiento horizontal (`overflow-x-hidden`). El contenedor general utiliza márgenes laterales reducidos (`px-4`) y padding ajustado en las tarjetas para maximizar el área de lectura.

---

### Estado 3: Estado Vacío / Sin Registros Laborales (Sad Path / Fallback)
- **Escenario Cubierto:** CA-03 — Resiliencia ante Ausencia de Registros Laborales
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
|  |                                                                 |  |
|  |                     [ 📋 ]                                      |  |
|  |      No hay registros de experiencia disponibles actualmente.    |  |
|  |                                                                 |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|             +-------------------------------------------+             |
|             |   [ [• Experiencia] ]     [ Estudios ⤓ ]  |             |
|             +-------------------------------------------+             |
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz (Brownfield / Fallback Vacío):**
  - **Disparador:** Arreglo `experience` vacío (`[]`) o no definido en el modelo estático.
  - **Comportamiento de Resiliencia:** Se despliega un contenedor neutro de altura mínima con texto atenuado (`text-neutral-500 dark:text-neutral-400 text-center py-10`). El layout de página, el botón de retorno y la barra inferior de navegación se mantienen 100% operativos y estables.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES
- **Heurísticas Aplicadas:**
  - *Heurística de Jerarquía Tipográfica y Escaneabilidad:* Uso de pesos visuales diferenciados (empresa > cargo > período > logros) para facilitar el escaneo visual rápido por reclutadores en menos de 5 segundos.
  - *Heurística de Rendimiento y Cero Fricción:* Maquetación estática pura en Astro con clases Tailwind, sin dependencias dinámicas de cliente para sostener el tiempo de carga < 1.0s.
- **Bloqueos de UX / Consultas para BA:** Ninguno. La especificación cubre la totalidad de los criterios funcionales aprobados para la HU-01.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Auditoría de Alcance: Épicas diseñadas = 1 / Épicas del backlog = 2 en el ciclo actual. El MVP continúa hacia la siguiente épica).*

@PM: Los wireframes para la HU Componente y Visualización Estructurada de Experiencia Laboral están listos en files/designer-ux/ux_01_visualizacion_experiencia_laboral.md. Por favor, lee el historial, identifica la siguiente Épica pendiente en el backlog y asígnala al BA.
