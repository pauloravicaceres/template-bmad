# ESPECIFICACIÓN DE DISEÑO UX: Descarga Directa de Documento de Estudios (Asset PDF)

- **Historia de Usuario Fuente:** `hu_02_descarga_documento_estudios.md`
- **Fecha de Diseño:** 25-09-2026
- **Diseñador UX:** Agente UX Senior BMAD
- **Modo de Operación:** Brownfield (Subordinado a `legacy_ecosystem.md`)

---

## 1. RESUMEN DE DISEÑO
- **Historia Base:** Descarga Directa de Documento de Estudios (HU-02).
- **Enfoque de Usabilidad:** Incorporación del elemento interactivo "Estudios ⤓" dentro de la botonera de navegación compartida. El diseño utiliza un enlace semántico HTML5 `<a href="/estudios.pdf" download>` con micro-feedback visual no bloqueante (icono de descarga / documento). Garantiza que la entrega del archivo PDF opere de forma inmediata mediante distribución estática pura (Zero JavaScript), sin alterar la ruta visual actual, sin recargar la página y preservando la sincronización de tema claro/oscuro.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Interacción de Descarga Exitosa de Documento PDF (Happy Path)
- **Escenario Cubierto:** CA-01 — Descarga Directa e Inmediata & CA-02 — Preservación de Rendimiento
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|  [ MODO ACTIVO: Light / Dark ]                              [ (☀️) 🌙 ]|
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
|             |   [ Experiencia ]     [ [Estudios ⤓] ]    |             |
|             +-------------------------------------------+             |
|                                            |                          |
|                     =================================                 |
|                     Descarga de asset estático (.pdf)                 |
|                     iniciada en navegador (< 1s)                      |
|                     =================================                 |
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz (Brownfield / Tailwind CSS):** 
  - **Disparador:** Clic o pulsación sobre la opción `Estudios ⤓`.
  - **Comportamiento y Componente:** Enlace semántico `<a href="/estudios.pdf" download="certificados_estudios.pdf">` con estilos de botón secundario/píldora (`hover:bg-neutral-200 dark:hover:bg-neutral-800 transition-colors duration-200`). La descarga se ejecuta nativamente en segundo plano sin interrumpir la visualización del perfil ni alterar el tema activo.

---

### Estado 2: Opción Integrada en Vista Complementaria de Experiencia (Happy Path Complementario)
- **Escenario Cubierto:** CA-02 — Preservación de Estética y Coherencia Multirruta
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
|  | [ Módulo de Experiencia ]                                       |  |
|  | • Cargo / Rol Profesional .......................... Periodo    |  |
|  +-----------------------------------------------------------------+  |
|                                                                       |
|             +-------------------------------------------+             |
|             |   [ [• Experiencia] ]     [ Estudios ⤓ ]  |             |
|             +-------------------------------------------+             |
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz (Brownfield / Consistencia):**
  - **Disparador:** Vista activa en `/experiencia`.
  - **Comportamiento:** La opción de descarga permanece accesible en la barra de navegación inferior en todas las vistas, permitiendo al reclutador o visitante descargar el comprobante académico desde cualquier sección con exactamente el mismo comportamiento estático.

---

### Estado 3: Resiliencia ante No Disponibilidad del Recurso (Sad Path / Fallback)
- **Escenario Cubierto:** CA-03 — Resiliencia y Manejo ante No Disponibilidad del Asset
- **Wireframe Estructural (ASCII):**
```text
+-----------------------------------------------------------------------+
|  [ MODO ACTIVO: Light / Dark ]                              [ (☀️) 🌙 ]|
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
|   ( Si el archivo no existe en /public: el navegador notifica HTTP    |
|     404 nativo en pestaña o toast sin romper la UI ni el menú )       |
|                                                                       |
+-----------------------------------------------------------------------+
```
- **Nota de Interfaz (Brownfield / Resiliencia):**
  - **Disparador:** Solicitud de archivo ausente o enlace temporalmente roto.
  - **Comportamiento de Resiliencia:** Al delegarse la descarga a la capa de assets estáticos de Astro (`public/`), la falta del recurso no rompe el DOM ni detiene la reactividad de la interfaz. La aplicación preserva su estado funcional y el menú sigue 100% operativo para navegar a otras secciones.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES
- **Heurísticas Aplicadas:**
  - *Heurística de Cero Fricción:* Descarga directa mediante atributo nativo HTML `download`, evitando modales o confirmaciones intermedias que añadan pasos innecesarios.
  - *Heurística de Claridad y Affordance:* Inclusión de un indicador visual sutil (glifo o flecha descendente `⤓`) para que el usuario distinga instantáneamente una acción de descarga documental de un enrutamiento de página interna.
- **Bloqueos de UX / Consultas para BA:** Ninguno. Se ha completado el diseño visual del 100% de las épicas del MVP.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER
*(Auditoría de Alcance: Épicas diseñadas = 2 / Épicas del backlog = 2. Conclusión del alcance del MVP en la Fase de Diseño UX).*

@SA: El diseño visual del MVP ha concluido exitosamente. Por favor, lee el Product Brief y el MVP, y define el stack tecnológico y las reglas arquitectónicas del proyecto.
