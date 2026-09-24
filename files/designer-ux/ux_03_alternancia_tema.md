# ESPECIFICACIÓN DE DISEÑO UX: Accesibilidad Visual y Alternancia de Tema

- **Historia de Usuario Fuente:** hu_03_alternancia_tema.md
- **Fecha de Diseño:** 23-09-2026
- **Diseñador UX:** Agente UX Senior BMAD

---

## 1. RESUMEN DE DISEÑO
- **Historia Base:** Accesibilidad Visual y Alternancia de Tema (Modo Claro / Modo Oscuro) (HU-03).
- **Enfoque de Usabilidad:** Control toggle/switch de alta visibilidad ubicado en la esquina superior de la vista única (cabecera flotante o fija). Permite la conmutación instantánea entre paleta clara (fondo blanco/gris claro con texto oscuro) y paleta oscura (fondo oscuro con texto claro), preservando contraste WCAG AA, sin parpadeos ni recargas de página.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Alternancia Fluida entre Modo Claro y Oscuro (Happy Path)
- **Escenario Cubierto:** CA-01 — Alternancia fluida entre modo claro y oscuro (Happy Path)
- **Wireframe Estructural (ASCII):**
```text
======================== VISTA 1: MODO CLARO (LIGHT) ========================
+---------------------------------------------------------------------------+
|  PERFIL PROFESIONAL                          [ (o) TEMA: CLARO | Oscuro ] |
|  (Fondo: Blanco #FFFFFF / Tipografía: Gris Carbón #1F2937)               |
+---------------------------------------------------------------------------+
|  [FOTO]  Juan Pérez Gómez - Ingeniero de Software Senior                  |
|          Correo: juan.perez@email.com | Tel: +51 987 654 321              |
+---------------------------------------------------------------------------+
|  == TRAYECTORIA ==                                                        |
|  • [2022-Pres] Tech Lead @ Innovatech  [Python] [React] [Docker]          |
+---------------------------------------------------------------------------+

                                 ||  (Click / Toggle)
                                 \/

======================== VISTA 2: MODO OSCURO (DARK) ========================
+---------------------------------------------------------------------------+
|  PERFIL PROFESIONAL                          [ Claro | TEMA: OSCURO (•) ] |
|  (Fondo: Gris Profundo #121826 / Tipografía: Blanco Nieve #F9FAFB)       |
+---------------------------------------------------------------------------+
|  [FOTO]  Juan Pérez Gómez - Ingeniero de Software Senior                  |
|          Correo: juan.perez@email.com | Tel: +51 987 654 321              |
+---------------------------------------------------------------------------+
|  == TRAYECTORIA ==                                                        |
|  • [2022-Pres] Tech Lead @ Innovatech  [Python] [React] [Docker]          |
+---------------------------------------------------------------------------+
```
- **Nota de Interfaz:** Al accionar el botón de alternancia, se aplica la clase de tema respectiva en el contenedor raíz (`root`), cambiando de inmediato las variables CSS de color de fondo, texto, tarjetas y bordes, garantizando un ratio de contraste superior a 4.5:1.

---

### Estado 2: Preservación de Estabilidad ante Cambios Sucesivos (Sad Path)
- **Escenario Cubierto:** CA-02 — Preservación de legibilidad y consistencia ante cambios sucesivos (Sad Path)
- **Wireframe Estructural (ASCII):**
```text
+---------------------------------------------------------------------------+
|  PERFIL PROFESIONAL                         [ [☼ / ☾] Toggle Interactivo ]|
+---------------------------------------------------------------------------+
|                                                                           |
|   ESTADO DE TRANSICIÓN RÁPIDA (Ráfaga de clicks / debounce visual):       |
|                                                                           |
|   +-------------------------------------------------------------------+   |
|   |  * Transición fluida CSS (0.2s cubic-bezier) sin flickering *     |   |
|   |  * Estado bloqueado ante colisión de renderizado *                |   |
|   |  * Paleta cromática final consistente con el último estado *     |   |
|   +-------------------------------------------------------------------+   |
|                                                                           |
+---------------------------------------------------------------------------+
```
- **Nota de Interfaz:** La interfaz implementa transiciones CSS homogéneas y atómicas para prevenir parpadeos (*flickering*), artefactos visuales o desfases cromáticos durante pulsaciones rápidas consecutivas.

---

### Estado 3: Mantenimiento de Contexto y Posición de Lectura (Sad Path / Restricción)
- **Escenario Cubierto:** CA-03 — Mantenimiento de contexto y posición de lectura al conmutar tema (Sad Path / Restricción)
- **Wireframe Estructural (ASCII):**
```text
+---------------------------------------------------------------------------+
|  [Barra Superior Fija / Sticky Header]       [ Switch Modo: Claro/Oscuro ]|
+---------------------------------------------------------------------------+
|  ... (Sección Superior fuera de viewport) ...                             |
|                                                                           |
|  == TRAYECTORIA PROFESIONAL (Posición de Scroll: 65% de la página) ==     |
|                                                                           |
|  +-------------------------------------------------------------------+    |
|  | [2019 - 2022] Desarrollador Backend Senior                        |    |
|  | Empresa: DataFlow Systems                                         |    |
|  | Stack: [ Python ] [ Django ] [ Redis ] [ AWS ] [ MySQL ]          |    |
|  +-------------------------------------------------------------------+    |
|                                                                           |
|  (i) El cambio de color ocurre en caliente sobre el DOM activo:           |
|      - Sin recargar la página (F5 prevenido).                             |
|      - ScrollY se mantiene exactamente en la posición del usuario.        |
+---------------------------------------------------------------------------+
```
- **Nota de Interfaz:** La conmutación de tema es reactiva y puramente en cliente; no dispara recargas de página (`window.location.reload`), no reinicia el scroll del navegador ni reinicializa componentes.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES
- **Heurísticas Aplicadas:** Ubicación del control de accesibilidad en la cabecera superior derecha (convención estándar de UI/UX) con indicación gráfica clara del modo activo. Uso de paleta de colores neutrales (fondos oscuros no 100% negros puros, ej. `#121826`, para evitar fatiga visual severa).
- **Bloqueos de UX / Consultas para BA:** Ninguno.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Instrucción de una sola línea plana que se anexa a tracker_bmad.md tras realizar la Auditoría de Alcance)*

@SA: El diseño visual del MVP ha concluido exitosamente. Por favor, lee el Product Brief y el MVP, y define el stack tecnológico y las reglas arquitectónicas del proyecto.
