# PLAN ESTRATÉGICO Y BACKLOG DEL MVP: Módulo de Experiencia Profesional

- **Documento Fuente:** pb_modulo_experiencia.md
- **Fecha de Elaboración:** 25-09-2026
- **Product Manager:** Agente Orquestador BMAD (Fase M)
- **Modo de Operación:** Brownfield (Subordinado a `constitution.md`)

---

## 1. VISIÓN ESTRATÉGICA DEL MVP
*(Sección evaluada por el Quality Gate del Watcher)*

- **Foco de Gestión:** Transformar la vista complementaria estática `/experiencia` en un espacio informativo estructurado y de alto impacto, exhibiendo los antecedentes laborales del profesional (empresa, rol, período y responsabilidades) mediante un componente responsivo y datos tipados locales, manteniendo la filosofía Zero JavaScript y cero FOUT del ecosistema heredado.
- **Criterio de Éxito Rector:** Carga y renderizado instantáneo de la vista de Experiencia con LCP < 1.0s, garantizando legibilidad tabular responsiva en móviles/escritorio, contraste WCAG AA en temas claro y oscuro, y navegación bidireccional fluida con la tarjeta principal.

---

## 2. BACKLOG INICIAL (ÉPICAS FUNCIONALES)
*(Sección evaluada por el Quality Gate del Watcher)*

Organización del alcance en bloques de valor estructurados bajo el estándar de Ruta Crítica (P1 a Pn) con tipificación de impacto Brownfield:

### [P1] Épica: Componente y Visualización Estructurada de Experiencia Laboral
- **Descripción de Negocio:** Desplegar de forma estructurada, responsiva y estéticamente balanceada la colección de puestos de trabajo previos (empresa, cargo/rol, período de tiempo y responsabilidades principales) consumiendo datos estáticos tipados de prueba.
- **Impacto Brownfield:** Extensión del modelo de persistencia tipada (`profile.config.json` y `profile.schema.ts` con Zod) e integración en la plantilla de página Astro (`/experiencia`) conservando la arquitectura SSG pura y el diseño Tailwind CSS (`darkMode: 'class'`).
- **Justificación de Prioridad:** Constituye el núcleo rector y el valor central del requerimiento; sin el despliegue ordenado de la trayectoria laboral, la vista carece de propósito.
- **Trazabilidad PRD:** Sección 4 (Componente de Tabla de Experiencia y Fuente de Datos Estática Tipada) y Sección 3 (Propósito Central) de `pb_modulo_experiencia.md`.

### [P2] Épica: Integración de Navegación de Retorno y Coherencia Multirruta
- **Descripción de Negocio:** Proveer un mecanismo intuitivo y visible de retorno hacia la tarjeta de identidad principal (`/`), garantizando la preservación del estado de tema visual (Light/Dark Mode) sin parpadeos visuales ni fricciones de navegación.
- **Impacto Brownfield:** Reutilización del layout base compartido (`Layout.astro`), enrutamiento nativo basado en archivos de Astro y script bloqueante anti-FOUT en `<head>`.
- **Justificación de Prioridad:** Asegura la usabilidad y bidireccionalidad en la exploración del perfil, complementando la visualización del contenido una vez establecido el componente principal P1.
- **Trazabilidad PRD:** Sección 4 (Integración de Navegación y Retorno) y Sección 5 (Invariante SSG y Coherencia Visual) de `pb_modulo_experiencia.md`.

---

## 3. RIESGOS, DEPENDENCIAS Y PUNTOS ABIERTOS

### Riesgos de Regresión y Acoplamiento (Ecosistema Heredado)
- **Ruptura de Esquema en Build-Time:** Modificación o extensión incompatible en `profile.schema.ts` que pudiera invalidar el tipado estricto de Zod y detener el pipeline de CI/CD.
- **Desbordamiento Tabular en Viewports Móviles:** Riesgo de problemas de maquetación en pantallas estrechas si el componente de experiencia no aplica una adaptación responsiva flexible (ej. vista de tarjetas o stacking vertical en móviles).

### Bloqueantes Potenciales
- `⚠️ SUPUESTO:` Los datos de experiencia laboral se integrarán directamente en la colección tipada centralizada dentro de `src/config/profile.config.json` validada en build-time.
- `⚠️ SUPUESTO:` Se mantendrá una muestra representativa de 2 a 4 puestos de trabajo para validar los estados visuales en temas claro y oscuro.

### Ambigüedades de Negocio (Para Control del BA)
- `❓ No documentado` Confirmación de si el orden de los puestos debe ser estrictamente cronológico inverso (del más reciente al más antiguo).
- `❓ No documentado` Definición sobre si los nombres de empresas requerirán enlaces externos en futuras iteraciones.

---

## 4. ORDEN DE DELEGACIÓN PARA EL BA
*(Instrucción que se inyecta en tracker_bmad.md)*

@BA: Se transfiere el plan estratégico del MVP (mvp_modulo_experiencia.md) en Modo Brownfield. Inicia el análisis detallado y especificación de Historias de Usuario para la Épica [P1] Componente y Visualización Estructurada de Experiencia Laboral.
