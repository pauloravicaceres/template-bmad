# ESPECIFICACIÓN DE DISEÑO UX: Presentación Personal e Información de Contacto Directo

- **Historia de Usuario Fuente:** hu_01_presentacion_contacto.md
- **Fecha de Diseño:** 23-09-2026
- **Diseñador UX:** Agente UX Senior BMAD

---

## 1. RESUMEN DE DISEÑO
- **Historia Base:** Presentación Personal e Información de Contacto Directo (HU-01).
- **Enfoque de Usabilidad:** Disposición en cabecera principal auto-contenida con jerarquía visual estructurada: cuadrante de fotografía profesional / avatar de reserva a la izquierda y bloque de datos de identidad (nombre completo, título profesional) junto con datos de contacto directo en texto plano a la derecha, facilitando escaneo ágil y sin navegación redundante.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Visualización Completa de Identidad y Contacto (Happy Path)
- **Escenario Cubierto:** CA-01 — Visualización completa de identidad y contacto (Happy Path)
- **Wireframe Estructural (ASCII):**
```text
+---------------------------------------------------------------------------------+
|  PERFIL PROFESIONAL                                          [ MODO: CLARO/OSC ] |
+---------------------------------------------------------------------------------+
|                                                                                 |
|  +-------------------+  +----------------------------------------------------+  |
|  |                   |  | NOMBRE COMPLETO: [ Juan Pérez Gómez ]              |  |
|  |    [FOTOGRAFÍA    |  | TITULO:          [ Ingeniero de Software Senior ]  |  |
|  |    PROFESIONAL]   |  |----------------------------------------------------|  |
|  |                   |  | DATOS DE CONTACTO DIRECTO (Texto plano):           |  |
|  |     (160x160)     |  | • Correo:    juan.perez@email.com                  |  |
|  |                   |  | • Teléfono:  +51 987 654 321                       |  |
|  |                   |  | • Ubicación: Lima, Perú                            |  |
|  +-------------------+  +----------------------------------------------------+  |
|                                                                                 |
+---------------------------------------------------------------------------------+
```
- **Nota de Interfaz:** Se renderiza de manera inmediata al cargar la vista única del perfil. Todos los campos de contacto se despliegan en texto legible y seleccionable sin requerir clicks adicionales.

---

### Estado 2: Manejo de Indisponibilidad de Fotografía Profesional (Sad Path)
- **Escenario Cubierto:** CA-02 — Manejo de indisponibilidad de fotografía profesional (Sad Path)
- **Wireframe Estructural (ASCII):**
```text
+---------------------------------------------------------------------------------+
|  PERFIL PROFESIONAL                                          [ MODO: CLARO/OSC ] |
+---------------------------------------------------------------------------------+
|                                                                                 |
|  +-------------------+  +----------------------------------------------------+  |
|  |    [ AVATAR /     |  | NOMBRE COMPLETO: [ Juan Pérez Gómez ]              |  |
|  |    PLACEHOLDER    |  | TITULO:          [ Ingeniero de Software Senior ]  |  |
|  |    RESPALDO ]     |  |----------------------------------------------------|  |
|  |                   |  | DATOS DE CONTACTO DIRECTO (Texto plano):           |  |
|  |       ( ? )       |  | • Correo:    juan.perez@email.com                  |  |
|  |    [Sin Imagen]   |  | • Teléfono:  +51 987 654 321                       |  |
|  |                   |  | • Ubicación: Lima, Perú                            |  |
|  +-------------------+  +----------------------------------------------------+  |
|                                                                                 |
+---------------------------------------------------------------------------------+
```
- **Nota de Interfaz:** Si el recurso de imagen no se encuentra disponible o falla durante la carga, el contenedor despliega un marcador visual / avatar neutro manteniendo estrictamente las dimensiones de 160x160 px para prevenir cambios bruscos de diseño (Cumulative Layout Shift) y preservando intactos el nombre, título y datos de contacto.

---

### Estado 3: Auto-contención de Contacto sin Enlaces a Terceros (Sad Path / Restricción)
- **Escenario Cubierto:** CA-03 — Cumplimiento de auto-contención sin enlaces a terceros (Sad Path / Restricción)
- **Wireframe Estructural (ASCII):**
```text
+---------------------------------------------------------------------------------+
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  | SECCIÓN DE CONTACTO DIRECTO (Texto Plano / Sin Enlaces Externos)          |  |
|  |                                                                           |  |
|  |  • Correo Electrónico:  juan.perez@email.com     [ Solo texto copiable ]  |  |
|  |  • Teléfono Directo:    +51 987 654 321          [ Solo texto copiable ]  |  |
|  |  • Ubicación:           Lima, Perú               [ Solo texto copiable ]  |  |
|  |                                                                           |  |
|  |  [X] Sin botones ni enlaces a redes sociales o plataformas de terceros    |  |
|  +---------------------------------------------------------------------------+  |
|                                                                                 |
+---------------------------------------------------------------------------------+
```
- **Nota de Interfaz:** Los elementos de contacto no son hipervínculos externos ni botones de redirección a redes sociales. La interfaz restringe navegación hacia terceros garantizando que la experiencia se mantenga 100% auto-contenida en la vista única.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES
- **Heurísticas Aplicadas:** Se adopta un layout de cabecera horizontal con dimensiones de contenedor de avatar fijas (160x160 px) para asegurar estabilidad visual. Se estructuran los datos de contacto con espaciado vertical ergonómico para permitir un escaneo ágil del reclutador (Ley de Fitts y principio de proximidad).
- **Bloqueos de UX / Consultas para BA:** Ninguno.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Instrucción de una sola línea plana que se anexa a tracker_bmad.md tras realizar la Auditoría de Alcance)*

@PM: Los wireframes para la HU Presentación Personal e Información de Contacto Directo están listos en files/designer-ux/ux_01_presentacion_contacto.md. Por favor, lee el historial, identifica la siguiente Épica pendiente en el backlog y asígnala al BA.
