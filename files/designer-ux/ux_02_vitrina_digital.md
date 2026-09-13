# ESPECIFICACIÓN DE DISEÑO UX Y WIREFRAMES ESTRUCTURALES

## 1. RESUMEN DE DISEÑO

- **Historia Base:** Visualización del catálogo de servicios podológicos y presentación del equipo de podólogos (`hu_02_vitrina_digital.md`)
- **Enfoque de Usabilidad:** Vitrina digital moderna y responsiva de alta confianza clínica (Design System *Clinical Sanctuary*), organizada en componentes modulables para explorar el catálogo de tratamientos podológicos con transparencia total de precios y duraciones estimadas, conocer las credenciales del equipo de podólogos colegiados (COP), permitir la pre-selección directa hacia el Motor de Reservas y gestionar la degradación fluida en dispositivos móviles así como el manejo de servicios/podólogos no disponibles temporalmente.

---

## 2. MAPA DE ESTADOS VISUALES

### Estado 1: Vitrina Digital Principal - Catálogo de Servicios y Equipo Médico (Desktop Happy Path)

**Escenario cubierto:** Escenario 1 (Visualización completa de catálogo con nombre, descripción, precio explícito ej. S/. 85.00 y duración estimada ej. 30 min), Escenario 2 (Fichas del equipo de podólogos colegiados con nombre y especialidad) y Escenario 3 (Transición directa al Motor de Reservas con servicio pre-seleccionado mediante CTA "Reservar Cita").

- **Stitch Project ID:** `projects/10202567855470565841`
- **Stitch Screen ID:** `projects/10202567855470565841/screens/c991b7c5250a47a18efe24f671a893fe`
- **Artefacto Visual:** Link/ID de Stitch: `c991b7c5250a47a18efe24f671a893fe`

**Nota de Interfaz:** Cada tarjeta de tratamiento incluye la badge de duración `⏱ 30 min` o `⏱ 45 min`, el precio explícito visible y el botón CTA "Reservar Cita". Al hacer clic en un servicio o podólogo, el sistema redirige al Motor Inteligente de Reservas manteniendo la pre-selección en la URL/estado global.

---

### Estado 2: Adaptabilidad Responsiva Móvil en Pantallas Reducidas (Mobile Happy Path / Escenario 4)

**Escenario cubierto:** Escenario 4 (Adaptabilidad responsiva en 1 columna fluida para smartphones sin recortar ni ocultar precios, duraciones ni botones).

- **Stitch Project ID:** `projects/10202567855470565841`
- **Stitch Screen ID:** `projects/10202567855470565841/screens/66b53cfa676c4a9dac5afc4b6a184108`
- **Artefacto Visual:** Link/ID de Stitch: `66b53cfa676c4a9dac5afc4b6a184108`

**Nota de Interfaz:** En viewports móviles (< 768px), la maquetación se transforma en una sola columna con barra de navegación comprimida (menú hamburguesa), scroll horizontal de filtros por categoría y botones CTA a ancho completo (`width: 100%`) para facilitar el toque táctil.

---

### Estado 3: Manejo de Servicios o Podólogos No Disponibles / Inactivos (Sad Path / Escenario 5)

**Escenario cubierto:** Escenario 5 (Servicio o podólogo deshabilitado temporalmente no disponible para agendamiento).

**Artefacto Visual:**

```text
+-----------------------------------------------------------------------------------+
| TARJETA DE SERVICIO PODOLÓGICO (ESTADO: INACTIVO / TEMPORALMENTE NO DISPONIBLE)  |
+-----------------------------------------------------------------------------------+
| [ Badge: ⚠️ TEMPORARIAMENTE NO DISPONIBLE ] [ Categ: Láser & Uñeros ]            |
|                                                                                   |
| Tratamiento Láser Avanzado de Onicomicosis                                         |
| Duración estimada: ⏱ 40 min  |  Precio: S/. 120.00                                |
|                                                                                   |
| Tratamiento especializado mediante tecnología láser para la eliminación gradual |
| de hongos ungueales.                                                              |
|                                                                                   |
| ℹ️ Caja Informativa: "En mantenimiento de calibración técnica. Este servicio    |
|    reanudarán cupos el próximo mes."                                              |
|                                                                                   |
| [ BOTÓN DESHABILITADO: No Disponible para Agendamiento ]                          |
| ( Enlace sutil: "Avisarme cuando esté disponible" )                               |
+-----------------------------------------------------------------------------------+
```

**Nota de Interfaz:** Los servicios o especialistas inactivos se muestran con opacidad reducida (`opacity: 0.7`), una insignia distintiva de indisponibilidad y su botón de reserva deshabilitado (`disabled: true`), previniendo cualquier redirección errónea hacia el agendamiento.

---

## 3. DECISIONES DE DISEÑO Y PUNTOS PENDIENTES

- **Heurísticas aplicadas:**
  - **Reconocimiento antes que recuerdo:** Exposición clara y directa de la duración estimada y el precio en Nuevos Soles en cada tarjeta.
  - **Consistencia y estándares:** Maquetación limpia en 12 columnas (desktop) y 1 columna (móvil) con jerarquía clara entre tratamientos clínicos y bienestar.
  - **Flexibilidad y eficiencia de uso:** Filtros rápidos por tipo de tratamiento (Podología Quirúrgica, Prevención, Láser, Masajes y Pie Diabético) y CTAs directos por servicio o podólogo.
- **Bloqueos o Consultas (Si aplican):**
  - No existen bloqueos UX que impidan el pase a Arquitectura. Se recomienda a Producto coordinar con el equipo clínico la provisión de fotografías reales de los profesionales y la confirmación final del catálogo de precios para producción.

---

## 4. ORDEN DE DELEGACIÓN PARA EL TRACKER

@ARQ: Los wireframes funcionales para la Historia de Usuario Visualización del catálogo de servicios podológicos y presentación del equipo de podólogos están listos. Puedes encontrar la estructura de UI y los IDs de Stitch en el archivo ux_02_vitrina_digital.md. El requerimiento está listo para el diseño de arquitectura y base de datos.
