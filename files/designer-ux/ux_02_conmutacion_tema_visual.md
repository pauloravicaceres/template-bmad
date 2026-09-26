# ESPECIFICACIÓN DE DISEÑO UX: Adaptación Visual y Conmutación de Tema (Light / Dark Mode)

- **Historia de Usuario Fuente:** `hu_02_conmutacion_tema_visual.md`
- **Fecha de Diseño:** 24-09-2026
- **Diseñador UX:** Agente UX Senior BMAD

---

## 1. RESUMEN DE DISEÑO
- **Historia Base:** Adaptación Visual y Conmutación de Tema (HU-02).
- **Enfoque de Usabilidad:** Integración de un control conmutador (Toggle Switch) ultra-minimalista, ergonómico y no invasivo, ubicado en la esquina superior de la interfaz para no desviar la atención del perfil central. La especificación define la dualidad cromática de alto contraste (Light Mode: fondo blanco/marfil con tipografía carbón; Dark Mode: fondo negro profundo/grafito con tipografía blanco óptico) garantizando transiciones suaves, persistencia local inmediata y cero parpadeo (Zero FOUC).

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Interfaz en Modo Claro (Light Mode)
- **Escenario Cubierto:** CA-01 — Alternancia Manual Fluida (Vista Claro) & CA-02 — Persistencia
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|  [ MODO CLARO: Fondo Blanco Puro / Tipografía Carbón ]      [ (☀️) 🌙 ]|
|                                                            Toggle     |
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
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz:** 
  - **Disparador:** Selección manual del icono de sol o inicialización bajo preferencia de tema claro.
  - **Paleta y Comportamiento:** Fondo `#FFFFFF` / `#F8F9FA`, tipografía principal `#1A1A1A` (contraste ratio > 7:1 cumpliendo WCAG AAA). El botón conmutador destaca el glifo solar con micro-animación de rotación/desvanecimiento suave (`transition: background-color 0.3s ease, color 0.3s ease`). La fotografía preserva su saturación y gama nativa.

---

### Estado 2: Interfaz en Modo Oscuro (Dark Mode)
- **Escenario Cubierto:** CA-01 — Alternancia Manual Fluida (Vista Oscuro) & CA-02 — Persistencia
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|  [ MODO OSCURO: Fondo Grafito Oscuro / Tipografía Blanco ]  [ ☀️ (🌙) ]|
|                                                            Toggle     |
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
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz:**
  - **Disparador:** Clic o toque en el conmutador de tema hacia la posición lunar o preferencia almacenada 'dark'.
  - **Paleta y Comportamiento:** Fondo `#121212` / `#1E1E1E` (reducción de fatiga visual), tipografía principal `#FFFFFF` / `#E0E0E0`. El conmutador resalta el glifo lunar con tono acento sutil. Almacenamiento sincrónico en `localStorage` bajo la clave `theme_preference` para evitar parpadeos de estilo durante recargas posteriores.

---

### Estado 3: Detección Automática del Sistema / Fallback Resiliente
- **Escenario Cubierto:** CA-03 — Detección Automática de Preferencia de Sistema y Resiliencia
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|  [ DETECCIÓN AUTOMÁTICA: prefers-color-scheme ]             [ ☀️ / 🌙 ]|
|                                                            Auto-Sync  |
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
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz:**
  - **Disparador:** Primera visita del usuario o entorno con `localStorage` deshabilitado/bloqueado (navegación privada estricta).
  - **Comportamiento y Fallback:** El motor evalúa la media query CSS `(prefers-color-scheme: dark)`. Si el sistema operativo reporta preferencia oscura, inicializa en Estado 2; si reporta claro o no está definido, aplica inmediatamente el Estado 1 (Light Mode por defecto) sin lanzar excepciones ni detener la ejecución de JavaScript.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES
- **Heurísticas Aplicadas:**
  - *Heurística de Consistencia y Feedback Visual:* Transición CSS de 300ms para cambios de fondo y color tipográfico, evitando cortes abruptos que incomoden al usuario.
  - *Heurística de Prevención de FOUC (Flash of Unstyled Content):* La lectura de la preferencia de tema se define en un script bloqueante ligero previo al renderizado del DOM principal para garantizar renderizado instantáneo en el tema correcto.
- **Bloqueos de UX / Consultas para BA:** Ninguno. Se han completado todas las especificaciones visuales del MVP.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Auditoría de Alcance: Épicas diseñadas = 2 / Épicas del backlog = 2. Conclusión del alcance del MVP en la Fase de Diseño UX).*

@SA: El diseño visual del MVP ha concluido exitosamente. Por favor, lee el Product Brief y el MVP, y define el stack tecnológico y las reglas arquitectónicas del proyecto.
