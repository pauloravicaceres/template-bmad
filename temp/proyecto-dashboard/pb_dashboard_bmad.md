# PRODUCT BRIEF: BMAD Control Center

- **Documento Fuente:** tech-design-dashboard.md
- **Fecha de Elaboración:** 2026-09-28
- **Product Analyst:** Agente PA Senior BMAD (Fase Discovery)

---

## 1. PROBLEMA
*(Diferenciar hechos comprobables de inferencias lógicas)*

- **Hechos Comprobables:** Actualmente, la observabilidad en tiempo real y la intervención humana (HITL) en el flujo de los agentes del ecosistema BMAD dependen de iteraciones con terminal y lectura de archivos físicos de manera aislada.
- **Inferencias Lógicas:** `⚠️ SUPUESTO:` Operar exclusivamente mediante terminal incrementa el costo cognitivo del Tech Lead, ralentiza la revisión de entregables (como diagramas o logs) y prolonga el tiempo necesario para liberar las compuertas operativas.

---

## 2. USUARIOS
*(Actores que experimentan el problema y usuarios que operarán la solución)*

- **Usuario Principal / Beneficiario:** Operador o Tech Lead del ecosistema BMAD (encargado de monitorear, validar entregables y ejecutar la aprobación HITL).
- **Usuarios Secundarios / Operativos:** `❓ No documentado` explícitamente en la idea fuente.

---

## 3. OBJETIVO (OUTCOME)
*(Resultado de negocio deseado o cambio de comportamiento observable; no una lista de features)*

- **Propósito Central:** Reducir la fricción y el tiempo de respuesta en la toma de decisiones humanas (HITL) proporcionando una ventana de gobernanza visual unificada y en tiempo real sobre las operaciones autónomas del enjambre.

---

## 4. ALCANCE INICIAL (MVP)
*(Límites y módulos funcionales prioritarios para la primera versión)*

- **Módulos Incluidos:**
  - **Live Workflow Monitor & File Explorer:** Visualización en vivo del flujo de los agentes y renderizado automático de artefactos Markdown y diagramas.
  - **HITL Command Center:** Interfaz central accionable para aprobar, rechazar o inyectar feedback en el proceso de los agentes.
  - **Observability de Eventos:** Emisión en tiempo real de los cambios del sistema de archivos (`tracker_bmad.md`, `/documents/`, `/.specify/`).
  - **Panel de Telemetría Git:** Visualización de cambios en el control de versiones (commits y stage).
  - **Integración con Sistema Heredado:** Lectura pasiva sobre el `tracker_bmad.md`, la carpeta `documents/` y el directorio `.specify/` existentes en el proyecto.
- **Exclusiones Explícitas (Fuera de Alcance):**
  - Modificar la lógica de negocio ni la arquitectura del Portafolio SSG descrito en el repositorio; la herramienta actúa como observador y controlador del proceso, no del dominio funcional externo.
  - Despliegue en la nube (el entorno debe operar de forma estrictamente local).

---

## 5. RESTRICCIONES
*(Limitaciones de negocio, legales, regulatorias u operativas inquebrantables)*

- El sistema deberá operar sobre el principio de "File-System as a Database", sin incluir bases de datos externas adicionales.
- **Restricciones Tecnológicas del Sistema Heredado (Lex Superior según constitution.md):**
  - **Runtime:** Node.js 20.x LTS obligatorio.
  - **Frameworks:** Astro 4.x para el frontend, Tailwind CSS 3.x para estilos. Tipado estricto con TypeScript 5.x y validación con Zod.
  - **Arquitectura:** Zero External APIs y pre-renderizado total SSG.

---

## 6. CRITERIOS DE ÉXITO
*(Métricas o evidencias para determinar si la solución resolvió el problema)*

- **Indicador Primario:** `⚠️ [PROPUESTO]:` Disminución porcentual del tiempo de ciclo en las aprobaciones y revisiones del Tech Lead.
- **Evidencia Cualitativa:** La interfaz de usuario refleja los cambios y mutaciones del ecosistema sin necesidad de recargar la vista, habilitando flujos de trabajo sin interrupciones.

---

## 7. SUPUESTOS
*(Hipótesis asumidas como verdaderas que condicionan la viabilidad de la solución y requieren validación)*

- `⚠️ SUPUESTO:` A pesar de la propuesta del Documento Fuente (FastAPI y Vue/Nuxt), los requerimientos deberán adaptar su propuesta tecnológica para cumplir con las invariantes estrictas del stack (`Astro`, `Node.js 20.x`) establecidas en el archivo `.specify/memory/constitution.md` para evitar ser rechazados por el Quality Gate.
- `⚠️ SUPUESTO:` La interfaz local habilitará canales asíncronos para simular el comportamiento reactivo (ej. WebSockets) que podría entrar en conflicto parcial con la política de Zero JavaScript en cliente, a menos que se tramite una excepción.

---

## 8. PREGUNTAS ABIERTAS
*(Vacíos críticos de información que deben resolverse antes o durante la fase de Management)*

1. `❓ No documentado:` ¿Contempla la Constitución del repositorio una "Cláusula de Excepción Arquitectónica" para admitir un backend en Python o un frontend en Vue para herramientas de observabilidad local de uso exclusivo del desarrollador?
2. `❓ No documentado:` ¿Existen requisitos de seguridad, manejo de múltiples flujos BMAD paralelos o soporte de autenticación local?

---

## 9. ORDEN DE DELEGACIÓN PARA EL TRACKER (PAUSA OBLIGATORIA HITL)

@HUMANO: El Product Brief pb_dashboard_bmad.md está listo para revisión en documents/product-analyst/. Por favor, valida el alcance y ejecuta `python utils/approve_step.py` para autorizar formalmente la transición hacia el product-manager.
