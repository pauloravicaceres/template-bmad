# PRODUCT BRIEF: Menú de Navegación del Perfil Digital

- **Documento Fuente:** idea_menu_navegacion_perfil.md
- **Fecha de Elaboración:** 25-09-2026
- **Product Analyst:** Agente PA Senior BMAD (Fase Discovery)
- **Modo de Operación:** Brownfield (Subordinado a `legacy_ecosystem.md`)

---

## 1. PROBLEMA
*(Diferenciar hechos comprobables de inferencias lógicas)*

- **Hechos Comprobables:** La tarjeta de identidad digital actual centraliza el nombre y la fotografía pero carece de accesos directos estructurados para profundizar en la trayectoria laboral o formación académica del titular, limitando la capacidad de proyectar credenciales completas desde este punto único de contacto.
- **Inferencias Lógicas:** `⚠️ SUPUESTO:` Los reclutadores, clientes y contactos profesionales requieren validar rápidamente antecedentes laborales y certificados descargables sin abandonar la estética concisa y minimalista de la plataforma.

---

## 2. USUARIOS
*(Actores que experimentan el problema y usuarios que operarán la solución)*

- **Usuario Principal / Beneficiario:** Titular de la página (profesional que requiere ofrecer accesos ordenados a su trayectoria y certificaciones sin saturar el diseño minimalista de su tarjeta de presentación).
- **Usuarios Secundarios / Operativos:** Visitante o contacto profesional (persona que utiliza el menú para consultar la trayectoria laboral o descargar el documento de estudios/certificaciones de forma rápida).

---

## 3. OBJETIVO (OUTCOME)
*(Resultado de negocio deseado o cambio de comportamiento observable; no una lista de features)*

- **Propósito Central:** Habilitar un canal estructurado y ligero de exploración de credenciales profesionales dentro de la tarjeta de identidad, permitiendo a los visitantes acceder a la trayectoria y obtener documentos académicos sin sobrecargar la experiencia visual ni degradar el rendimiento del sitio.

---

## 4. ALCANCE INICIAL (MVP)
*(Límites y módulos funcionales prioritarios para la primera versión en Modo Brownfield)*

- **Módulos Incluidos:**
  - **Componente Menú de Navegación:** Integración de barra o grupo de navegación visualmente armónico con el diseño preexistente y adaptado a ambos modos (Light/Dark Mode).
  - **Opción de Navegación "Experiencia":** Elemento interactivo que conduce a una vista complementaria inicial (página estática base en blanco, preparada estructuralmente para futura carga de contenido).
  - **Opción de Descarga "Estudios":** Elemento interactivo que dispara la descarga directa de un asset documental PDF (archivo inicial representativo para futura vinculación de certificados).
- **Integración con Ecosistema Heredado:**
  - Consumo directo del layout base y estilos globales preexistentes (Astro 4.x + Tailwind CSS 3.x).
  - Respeto total al mecanismo de persistencia y conmutación de tema (`theme_preference` en `localStorage` con script inline anti-FOUT).
- **Exclusiones Explícitas (Fuera de Alcance):**
  - Redacción o maquetación del contenido curricular detallado dentro de la vista de "Experiencia" en esta iteración.
  - Generación dinámica de PDFs en servidor o APIs de conversión de documentos.
  - Secciones adicionales de menú (e.g., Blog, Portafolio, Contacto) no especificadas en la narrativa de entrada.

---

## 5. RESTRICCIONES
*(Limitaciones duras de negocio, arquitectura y ecosistema heredado)*

- **Invariante Arquitectónica SSG:** La extensión debe respetar estrictamente la arquitectura estática ("Zero JavaScript by default") del framework Astro preexistente, sin introducir llamadas a backend ni APIs dinámicas de servidor.
- **Coherencia de Estilos y Temas:** El menú debe soportar de forma nativa la estrategia de clases `darkMode: 'class'` de Tailwind CSS y no generar parpadeos visuales (FOUT/FOUC).
- **Sobrecarga Cero:** El componente de navegación debe mantener la estética ultra-minimalista sin saturar visualmente el viewport en dispositivos móviles ni escritorios.
- **Distribución Estática de Assets:** El documento PDF descargable debe servirse como asset estático optimizado desde el directorio público del proyecto.

---

## 6. CRITERIOS DE ÉXITO
*(Métricas o evidencias para determinar si la solución resolvió el problema)*

- **Indicador Primario:** `⚠️ [PROPUESTO]` 100% de éxito en la activación del enlace hacia la vista de Experiencia y descarga inmediata del archivo PDF de Estudios en menos de 1 segundo en entornos web locales y CDN.
- **Evidencia Cualitativa:** `⚠️ [PROPUESTO]` Integración estética impecable con los modos claro y oscuro, manteniendo la jerarquía tipográfica y accesibilidad (contraste WCAG AA).

---

## 7. SUPUESTOS
*(Hipótesis asumidas como verdaderas que condicionan la viabilidad de la solución y requieren validación)*

- `⚠️ SUPUESTO:` La vista complementaria de "Experiencia" utilizará la misma plantilla base (`Layout.astro`) para conservar el selector de tema y la cabecera.
- `⚠️ SUPUESTO:` El archivo PDF asociado a "Estudios" se almacenará localmente en la carpeta de assets públicos del sitio estático (`public/`).
- `⚠️ SUPUESTO:` La navegación entre la tarjeta principal y la vista de experiencia se resolverá mediante enrutamiento estático nativo de Astro.

---

## 8. PREGUNTAS ABIERTAS
*(Vacíos críticos de información que deben resolverse antes o durante la fase de Management)*

1. `❓ No documentado` ¿La opción "Experiencia" debe abrir la vista complementaria en la misma pestaña del navegador o en una pestaña nueva con enlace de retorno?
2. `❓ No documentado` ¿El asset PDF de "Estudios" requiere un nombre de archivo estándar específico (e.g., `cv_estudios.pdf` o `certificados.pdf`) para la descarga?

---

## 9. ORDEN DE DELEGACIÓN PARA EL TRACKER (PAUSA OBLIGATORIA HITL)

@HUMANO: El Product Brief pb_menu_navegacion_perfil.md está listo para revisión en files/product-analyst/. Por favor, valida el alcance y ejecuta `python utils/approve_step.py` para autorizar formalmente la transición hacia el product-manager.
