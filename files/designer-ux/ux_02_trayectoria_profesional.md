# ESPECIFICACIÓN DE DISEÑO UX: Trayectoria Profesional Cronológica y Stack Tecnológico

- **Historia de Usuario Fuente:** hu_02_trayectoria_profesional.md
- **Fecha de Diseño:** 23-09-2026
- **Diseñador UX:** Agente UX Senior BMAD

---

## 1. RESUMEN DE DISEÑO
- **Historia Base:** Trayectoria Profesional Cronológica y Stack Tecnológico (HU-02).
- **Enfoque de Usabilidad:** Disposición en línea de tiempo vertical o tarjetas cronológicas secuenciales (cronología inversa) en el cuerpo central de la vista única. Cada experiencia destaca puesto, periodo y etiquetas visuales de tecnologías clave (*tech badges*) de lectura rápida y sin enlaces de distracción.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Presentación Cronológica de Experiencia y Tecnologías (Happy Path)
- **Escenario Cubierto:** CA-01 — Presentación cronológica de experiencia y tecnologías (Happy Path)
- **Wireframe Estructural (ASCII):**
```text
+---------------------------------------------------------------------------------+
|                                                                                 |
|  == TRAYECTORIA PROFESIONAL ==                                                  |
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  | [2022 - Presente]  Líder Técnico / Senior Fullstack Developer             |  |
|  | Empresa: Innovatech Solutions                                             |  |
|  | Stack:   [ Python ] [ FastAPI ] [ React ] [ Docker ] [ PostgreSQL ]        |  |
|  +---------------------------------------------------------------------------+  |
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  | [2019 - 2022]      Desarrollador Backend Senior                           |  |
|  | Empresa: DataFlow Systems                                                 |  |
|  | Stack:   [ Python ] [ Django ] [ Redis ] [ AWS ] [ MySQL ]                 |  |
|  +---------------------------------------------------------------------------+  |
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  | [2017 - 2019]      Desarrollador de Software Junior / Mid                 |  |
|  | Empresa: WebCore Agency                                                   |  |
|  | Stack:   [ JavaScript ] [ Node.js ] [ Express ] [ MongoDB ]               |  |
|  +---------------------------------------------------------------------------+  |
|                                                                                 |
+---------------------------------------------------------------------------------+
```
- **Nota de Interfaz:** Se renderiza en el cuerpo central de la vista. Las experiencias se ordenan de la más reciente a la más antigua. Las tecnologías se despliegan como píldoras/chips visuales (*badges*) de texto de alto contraste.

---

### Estado 2: Manejo de Sección sin Registros de Experiencia (Sad Path / Empty State)
- **Escenario Cubierto:** CA-02 — Manejo de sección sin registros de experiencia (Sad Path)
- **Wireframe Estructural (ASCII):**
```text
+---------------------------------------------------------------------------------+
|                                                                                 |
|  == TRAYECTORIA PROFESIONAL ==                                                  |
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  |                                                                           |  |
|  |                            [ Ícono Informativo (i) ]                      |  |
|  |                                                                           |  |
|  |                "Trayectoria profesional en proceso de actualización"      |  |
|  |                 La información de experiencia estará disponible pronto.   |  |
|  |                                                                           |  |
|  +---------------------------------------------------------------------------+  |
|                                                                                 |
+---------------------------------------------------------------------------------+
```
- **Nota de Interfaz:** Si el conjunto de datos de experiencia está vacío o no se encuentran registros, se despliega un contenedor neutro de estado vacío (*Empty State*) informando la actualización del perfil sin romper la cuadrícula ni desplazar las demás secciones.

---

### Estado 3: Auto-contención de Etiquetas Tecnológicas sin Enlaces Externos (Sad Path / Restricción)
- **Escenario Cubierto:** CA-03 — Auto-contención de etiquetas tecnológicas sin enlaces externos (Sad Path / Restricción)
- **Wireframe Estructural (ASCII):**
```text
+---------------------------------------------------------------------------------+
|                                                                                 |
|  +---------------------------------------------------------------------------+  |
|  | DETALLE DE STACK TECNOLÓGICO (Badges Estáticos / Sin Hipervínculos)        |  |
|  |                                                                           |  |
|  |  Tecnologías:  [ Python ]  [ React ]  [ Docker ]  [ PostgreSQL ]          |  |
|  |                                                                           |  |
|  |  (i) Nota: Las etiquetas son chips visuales estáticos y texto copiable.   |  |
|  |  [X] Sin punteros interactivos que abran pestañas hacia sitios de terceros |  |
|  +---------------------------------------------------------------------------+  |
|                                                                                 |
+---------------------------------------------------------------------------------+
```
- **Nota de Interfaz:** Los chips de tecnologías no implementan selectores `cursor: pointer` con redirecciones a sitios oficiales o redes de terceros. Son elementos visuales semánticos de información estática y texto seleccionable.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES
- **Heurísticas Aplicadas:** Se opta por tarjetas de experiencia con diferenciación tipográfica entre el rol principal y el periodo de tiempo para guiar el escaneo visual en F. Los badges de tecnología cuentan con relleno sutil y bordes redondeados para fácil diferenciación visual respecto al texto de cuerpo.
- **Bloqueos de UX / Consultas para BA:** Ninguno.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Instrucción de una sola línea plana que se anexa a tracker_bmad.md tras realizar la Auditoría de Alcance)*

@PM: Los wireframes para la HU Trayectoria Profesional Cronológica y Stack Tecnológico están listos en files/designer-ux/ux_02_trayectoria_profesional.md. Por favor, lee el historial, identifica la siguiente Épica pendiente en el backlog y asígnala al BA.
