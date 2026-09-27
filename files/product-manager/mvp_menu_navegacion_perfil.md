# PLAN ESTRATÉGICO Y BACKLOG DEL MVP: Menú de Navegación del Perfil Digital

- **Documento Fuente:** pb_menu_navegacion_perfil.md
- **Fecha de Elaboración:** 25-09-2026
- **Product Manager:** Agente Orquestador BMAD (Fase M)
- **Modo de Operación:** Brownfield (Subordinado a `constitution.md`)

---

## 1. VISIÓN ESTRATÉGICA DEL MVP
*(Sección evaluada por el Quality Gate del Watcher)*

- **Foco de Gestión:** Extender la tarjeta de identidad digital consolidada incorporando una barra de navegación ultra-minimalista y no invasiva que permita a los visitantes explorar la trayectoria profesional mediante una vista complementaria estática y descargar credenciales académicas en formato PDF, sin alterar el rendimiento ni la estética base del sistema heredado.
- **Criterio de Éxito Rector:** 100% de efectividad en la activación del enrutamiento hacia la vista de "Experiencia" y descarga inmediata del archivo PDF de "Estudios" en menos de 1 segundo, conservando la sincronización de tema claro/oscuro (cero parpadeo visual FOUT) y el estándar estático SSG con cero sobrepeso de JavaScript.

---

## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)
*(Sección evaluada por el Quality Gate del Watcher)*

Organización del alcance en bloques de valor estructurados bajo el estándar de Ruta Crítica (P1 a Pn) con tipificación de impacto Brownfield:

### [P1] Épica: Componente Menú de Navegación y Enrutamiento a Vista de Experiencia
- **Descripción de Negocio:** Integrar un componente visual de navegación armónico con el diseño preexistente y habilitar el enlace interactivo hacia una vista complementaria inicial de "Experiencia" (página estática base preparada estructuralmente para futura carga curricular).
- **Impacto Brownfield:** Extensión de componente y layout preexistentes (`Layout.astro` y Tailwind CSS 3.x), aprovechando el enrutamiento estático nativo de Astro y la sincronización de clases de tema (`darkMode: 'class'`).
- **Justificación de Prioridad:** Constituye el núcleo rector y contenedor estructural de la nueva funcionalidad; sin el menú y su navegación base, no es posible articular el acceso a las credenciales ni sostener la experiencia de usuario.
- **Trazabilidad PRD:** Sección 4 (Componente Menú de Navegación y Opción de Navegación "Experiencia") y Sección 3 (Propósito Central) de `pb_menu_navegacion_perfil.md`.

### [P2] Épica: Descarga Directa de Documento de Estudios (Asset PDF)
- **Descripción de Negocio:** Habilitar el elemento interactivo dentro del menú de navegación que dispare la descarga directa e inmediata de un asset documental representativo en formato PDF para la acreditación de estudios y certificados.
- **Impacto Brownfield:** Integración con la distribución estática de assets públicos (`public/`) sin requerir backend ni APIs dinámicas de servidor, alineado a la arquitectura Zero JavaScript.
- **Justificación de Prioridad:** Actúa como la segunda capacidad de valor complementaria del menú, resolviendo la entrega de soporte documental una vez establecida la estructura de navegación P1.
- **Trazabilidad PRD:** Sección 4 (Opción de Descarga "Estudios") y Sección 5 (Distribución Estática de Assets) de `pb_menu_navegacion_perfil.md`.

---

## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

### Riesgos de Regresión y Acoplamiento (Ecosistema Heredado)
- **Regresión Visual / FOUT:** Riesgo de parpadeo o pérdida de sincronización de tema (Light/Dark Mode) al navegar entre la tarjeta principal y la vista de Experiencia si no se reutiliza el script inline del `<head>` definido en `Layout.astro`.
- **Ruptura de la Filosofía SSG:** Introducción inadvertida de dependencias de cliente o llamadas dinámicas que rompan la premisa "Zero JavaScript by default" establecida en el ecosistema consolidado.

### Bloqueantes Potenciales
- `⚠️ SUPUESTO:` Disponibilidad y presencia física del archivo PDF inicial en la carpeta de assets estáticos públicos (`public/`).
- `⚠️ SUPUESTO:` Reutilización directa del layout base compartido para garantizar consistencia en la botonera de conmutación de tema y cabecera en ambas rutas.

### Ambigüedades de Negocio (Para Control del BA)
- `❓ No documentado` Definición sobre si la opción "Experiencia" debe navegar en la misma ventana con botón/mecanismo de retorno a la tarjeta principal o si se abre en una pestaña independiente.
- `❓ No documentado` Confirmación del identificador y nombre canónico del asset PDF a servir para "Estudios" (e.g., `certificados_estudios.pdf`).

---

## 4. ORDEN DE DELEGACIÓN PARA EL BA
*(Instrucción que se inyecta en tracker_bmad.md)*

@BA: Se transfiere el plan estratégico del MVP (mvp_menu_navegacion_perfil.md) en Modo Brownfield. Inicia el análisis detallado y especificación de Historias de Usuario para la Épica [P1] Componente Menú de Navegación y Enrutamiento a Vista de Experiencia.
