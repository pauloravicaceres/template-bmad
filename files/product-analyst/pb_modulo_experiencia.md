# PRODUCT BRIEF: Módulo de Experiencia Profesional

- **Documento Fuente:** idea_modulo_experiencia.md
- **Fecha de Elaboración:** 25-09-2026
- **Product Analyst:** Agente PA Senior BMAD (Fase Discovery)
- **Modo de Operación:** Brownfield (Subordinado a `legacy_ecosystem.md`)

---

## 1. PROBLEMA
*(Diferenciar hechos comprobables de inferencias lógicas)*

- **Hechos Comprobables:** La opción de experiencia en la plataforma es actualmente una vista base en blanco, lo que impide que visitantes, reclutadores y clientes potenciales conozcan de forma directa la trayectoria laboral, roles desempeñados y logros profesionales del titular.
- **Inferencias Lógicas:** `⚠️ SUPUESTO:` Presentar la trayectoria laboral de forma tabular y estructurada agiliza la toma de decisiones por parte de reclutadores y refuerza el posicionamiento profesional y credibilidad de la marca personal.

---

## 2. USUARIOS
*(Actores que experimentan el problema y usuarios que operarán la solución)*

- **Usuario Principal / Beneficiario:** Titular de la plataforma (profesional independiente que necesita exhibir su historial laboral, responsabilidades y cargos de manera ordenada, estética y fácilmente auditable).
- **Usuarios Secundarios / Operativos:** Visitante, reclutador o contacto profesional (persona que accede a `/experiencia` para examinar el detalle de los puestos previos, empresas y períodos de desempeño).

---

## 3. OBJETIVO (OUTCOME)
*(Resultado de negocio deseado o cambio de comportamiento observable; no una lista de features)*

- **Propósito Central:** Proveer una experiencia de consulta estructurada, rápida y legible de los antecedentes laborales del titular, permitiendo a los interesados auditar su experiencia profesional en segundos sin fricción visual ni sobrecarga técnica.

---

## 4. ALCANCE INICIAL (MVP)
*(Límites y módulos funcionales prioritarios para la primera versión en Modo Brownfield)*

- **Módulos Incluidos:**
  - **Componente de Tabla de Experiencia:** Componente estructurado y responsivo para el despliegue de registros laborales (incluyendo campos de empresa/institución, posición/rol, período de tiempo y responsabilidades principales).
  - **Fuente de Datos Estática Tipada:** Ingestión de datos de experiencia a partir de un modelo JSON tipado local con información representativa de prueba.
  - **Integración de Navegación y Retorno:** Conservación del layout base compartido (`Layout.astro`), navegación armoniosa y botón/enlace de retorno a la página principal.
- **Integración con Ecosistema Heredado:**
  - Uso estricto del framework SSG Astro 4.x + Tailwind CSS 3.x preexistente.
  - Integración nativa con la estrategia de conmutación de temas (Light/Dark Mode) y script inline anti-FOUT en `Layout.astro`.
  - Extensión coherente del modelo de datos estático tipado con TypeScript y Zod.
- **Exclusiones Explícitas (Fuera de Alcance):**
  - Mecanismos complejos de filtrado interactivo en cliente, paginación o búsqueda en tiempo real.
  - Panel administrativo para edición o carga dinámica de experiencia (CRUD/base de datos).
  - Integración de APIs de terceros (LinkedIn, portales de reclutamiento o endpoints dinámicos).

---

## 5. RESTRICCIONES
*(Limitaciones duras de negocio, arquitectura y ecosistema heredado)*

- **Invariante SSG "Zero JS":** El componente de tabla debe pre-renderizarse completamente en el servidor/compilador sin dependencias de JavaScript pesado en el cliente.
- **Responsividad y Legibilidad Tabular:** La estructura tabular debe adaptarse a pantallas móviles mediante un diseño fluido que evite rupturas visuales o desbordamientos incontrolados.
- **Coherencia Visual y Accesibilidad:** Mantener las directrices de contraste WCAG AA en temas claro y oscuro, respetando la jerarquía tipográfica global del proyecto.
- **Cero Dependencias de Red en Ejecución:** Todos los datos deben suministrarse en build-time desde los archivos estáticos tipados del repositorio.

---

## 6. CRITERIOS DE ÉXITO
*(Métricas o evidencias para determinar si la solución resolvió el problema)*

- **Indicador Primario:** `⚠️ [PROPUESTO]` Carga y renderizado instantáneo de la vista de Experiencia con LCP < 1.0s en entornos locales y perimetrales (CDN).
- **Evidencia Cualitativa:** `⚠️ [PROPUESTO]` Despliegue estructurado y visualmente balanceado de la trayectoria profesional con perfecta alternancia entre modos claro y oscuro y retorno intuitivo al perfil principal.

---

## 7. SUPUESTOS
*(Hipótesis asumidas como verdaderas que condicionan la viabilidad de la solución y requieren validación)*

- `⚠️ SUPUESTO:` Los registros de experiencia laboral se incorporarán como una colección estructurada dentro del archivo de configuración centralizado (`profile.config.json`) o un archivo JSON complementario validado con Zod.
- `⚠️ SUPUESTO:` Los datos representativos de prueba incluirán entre 2 y 4 cargos laborales relevantes para validar el diseño visual y la adaptabilidad responsiva.
- `⚠️ SUPUESTO:` La navegación entre la vista principal y `/experiencia` conservará el estado del tema visual sin parpadeos gracias al script inline preexistente.

---

## 8. PREGUNTAS ABIERTAS
*(Vacíos críticos de información que deben resolverse antes o durante la fase de Management)*

1. `❓ No documentado` ¿El ordenamiento de los puestos de trabajo debe estructurarse cronológicamente de forma inversa (del más reciente al más antiguo) de manera estricta?
2. `❓ No documentado` ¿Se requerirá a futuro que los nombres de las empresas contengan hipervínculos externos hacia sus sitios web corporativos?

---

## 9. ORDEN DE DELEGACIÓN PARA EL TRACKER (PAUSA OBLIGATORIA HITL)

@HUMANO: El Product Brief pb_modulo_experiencia.md está listo para revisión en files/product-analyst/. Por favor, valida el alcance y ejecuta `python utils/approve_step.py` para autorizar formalmente la transición hacia el product-manager.
