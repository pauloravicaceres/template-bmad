# ESPECIFICACIÓN DE DISEÑO UX: Presentación Central de Identidad y Perfil Profesional

- **Historia de Usuario Fuente:** `hu_01_presentacion_identidad_perfil.md`
- **Fecha de Diseño:** 24-09-2026
- **Diseñador UX:** Agente UX Senior BMAD

---

## 1. RESUMEN DE DISEÑO
- **Historia Base:** Presentación Central de Identidad y Perfil Profesional (HU-01).
- **Enfoque de Usabilidad:** Arquitectura de información ultra-minimalista orientada a cero fricción y carga cognitiva mínima. El diseño prioriza un contenedor central simétrico donde la fotografía de perfil de alta resolución actúa como ancla visual inmediata, acompañada de una jerarquía tipográfica limpia y balanceada para el nombre profesional, garantizando adaptabilidad en cualquier resolución sin elementos de distracción.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Presentación Exitosa del Perfil Profesional (Happy Path)
- **Escenario Cubierto:** CA-01 — Visualización Exitosa de Fotografía y Nombre Completo
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|                                                                       |
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
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz:** 
  - **Disparador:** Carga exitosa de la página principal y descarga completa del recurso de imagen.
  - **Comportamiento y Jerarquía:** El contenedor del avatar mantiene una relación de aspecto simétrica (1:1, redondeado u ovalado según el sistema de diseño) con centrado absoluto en el viewport vertical y horizontal. La tipografía del nombre profesional utiliza escala tipográfica primaria (H1 semántico) con alto contraste, asegurando máxima legibilidad instantánea sin distorsiones geométricas en la imagen (`object-fit: cover`).

---

### Estado 2: Degradación Elegante y Placeholder Neutro (Sad Path)
- **Escenario Cubierto:** CA-02 — Control de Carga y Degradación de Imagen de Perfil
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|                                                                       |
|                                                                       |
|                     +---------------------------+                     |
|                     |  . . . . . . . . . . . .  |                     |
|                     |  .       [  👤  ]        .  |                     |
|                     |  .      PLACEHOLDER      .  |                     |
|                     |  .        NEUTRO         .  |                     |
|                     |  . . . . . . . . . . . .  |                     |
|                     +---------------------------+                     |
|                                                                       |
|                      ===========================                      |
|                      NOMBRE COMPLETO PROFESIONAL                      |
|                      ===========================                      |
|                                                                       |
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz:**
  - **Disparador:** Falla en la descarga del recurso fotográfico (HTTP 404/500, timeout o desconexión de red).
  - **Comportamiento y Resiliencia:** Se activa el fallback visual sin causar desplazamiento de diseño acumulativo (Cumulative Layout Shift = 0). El contenedor preserva exactamente las mismas dimensiones físicas del avatar original, renderizando un pictograma/silueta vectorial neutral o fondo con tono atenuado. El nombre completo permanece visible e intacto en su posición jerárquica.

---

### Estado 3: Adaptabilidad Responsiva en Viewport Móvil (Happy Path Complementario)
- **Escenario Cubierto:** CA-03 — Rendimiento y Adaptabilidad Responsiva
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------+
|                                   |
|                                   |
|       +-------------------+       |
|       |                   |       |
|       |    ( FOTO EN      |       |
|       |    ALTA RES. )    |       |
|       |                   |       |
|       +-------------------+       |
|                                   |
|      =======================      |
|      NOMBRE PROFESIONAL           |
|      =======================      |
|                                   |
|                                   |
+-----------------------------------+
```
- **Nota de Interfaz:**
  - **Disparador:** Acceso desde dispositivos móviles con pantallas de ancho reducido (<= 480px).
  - **Comportamiento Dinámico:** Escalado fluido de componentes utilizando unidades relativas (`vw`, `rem`). El avatar y la tipografía se redimensionan proporcionalmente preservando el espaciado y márgenes de seguridad para garantizar renderizado instantáneo (< 2 segundos) y navegación libre de scroll vertical innecesario.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES
- **Heurísticas Aplicadas:**
  - *Heurística de Simplicidad y Foco:* Ausencia deliberada de elementos accesorios (botones de navegación, barras laterales, pie de página invasivo) para centrar la atención en la identidad profesional.
  - *Heurística de Prevención de Errores Visuales:* Dimensionamiento explícito del contenedor de imagen para evitar parpadeos o saltos de layout durante la fase de hidratación o renderizado.
- **Bloqueos de UX / Consultas para BA:** Ninguno. La especificación cubre la totalidad de los criterios funcionales y no funcionales aprobados para la HU-01.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Auditoría de Alcance: Épicas diseñadas = 1 / Épicas del backlog = 2. El MVP continúa hacia la siguiente épica).*

@PM: Los wireframes para la HU Presentación Central de Identidad y Perfil Profesional están listos en files/designer-ux/ux_01_presentacion_identidad_perfil.md. Por favor, lee el historial, identifica la siguiente Épica pendiente en el backlog y asígnala al BA.
