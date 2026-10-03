# TECHNICAL GUIDELINES & ARCHITECTURE RULES

- **Fecha de Definición:** 02-10-2026
- **Solutions Architect:** Agente SA Senior BMAD
- **Fuente SDD:** `001-HU_configurador_y_calculo_cotizaciones.md`, `ux_001_configurador_y_calculo_cotizaciones.md` y `constitution.md`

---

## 1. Project Overview
- **Qué es el sistema:** Generador de Cotizaciones Web Interactivo para Desarrolladores Freelance.
- **Qué problema resuelve:** Automatiza la configuración de propuestas, selección de servicios y cómputo de subtotales/totales en tiempo real, eliminando inconsistencias manuales.
- **Naturaleza del Proyecto:** Brownfield (Subordinado a las directrices de la Constitución Técnica Global de BMAD en `.specify/memory/constitution.md`).
- **Arquitectura general:** Arquitectura Decoupled Client-Side Engine (SPA React / TypeScript con backend API minimalista en Node.js/Express, empaquetado en contenedores Docker rootless).

## 2. Repository Structure
- **Frontend App (`app/frontend/`):**
  - `src/components/`: Componentes UI modulares (Configurador, Panel de Resumen, Inputs reactivos).
  - `src/engine/`: Motor de Cálculo reactivo puramente funcional (Cómputo de subtotales, totales y reglas de validación).
  - `src/types/`: Definición de interfaces TypeScript (ServiceItem, QuoteState, CalculationResult).
- **Backend App (`app/backend/`):**
  - `src/controllers/`: Controladores API REST.
  - `src/services/`: Servicios de catálogo y procesamiento de cotizaciones.
  - `src/routes/`: Definición de endpoints API.
- **Importante:** Separación limpia de capas de cliente y servidor según las directivas globales del proyecto.
- **Qué NO debe tocar:** Archivos fuera de `app/frontend/` y `app/backend/`, o el orquestador `utils/`.

## 3. Tech Stack
- **Runtime:** Node.js 20 LTS
- **Framework Frontend:** React 18 / TypeScript
- **Framework Backend:** Express / Node.js (con TypeScript)
- **Database:** PostgreSQL 16 (para persistencia de catálogo y cotizaciones)
- **Infrastructure:** Docker rootless, Docker Compose
- **Testing:** Jest + React Testing Library (Pruebas unitarias de motor y pruebas de componentes UI no-tautológicas)

## 4. Development Workflow
- **Cómo levantar el proyecto:** `npm run dev` (dentro de `app/frontend` y `app/backend`) o `docker-compose up --build`
- **Cómo ejecutar tests / lint / build:** `npm test`, `npm run lint`, `npm run build`
- **Cómo ejecutar migraciones:** `npm run migrate` en `app/backend`

## 5. Architecture Rules & Decision Framework
- **Principios que deben respetarse:** Stateless Client Computation, Componentes reactivos UI, Separación de responsabilidades, Validación defensiva.
- **Dependencias permitidas:** Librerías estándar TypeScript/React, UI component libraries ligeras (ej. TailwindCSS / Lucide Icons).
- **Patrones prohibidos:** Queda estrictamente prohibido el uso de variables "hardcodeadas", mutación directa de estados de React fuera de reducers/setters, e inyección de datos de prueba en producción.

### 5.1. State Management Architecture
- **Frontera de Estado:** La verdad del cálculo reside en el Cliente (Motor de Cálculo Reactivo puro en `app/frontend/src/engine/`), mientras que la verdad del catálogo reside en el Servidor/Base de Datos.
- **Estrategia de Sincronización:** Optimistic UI + Eventos de Cambio (`onChange` / `onSelect`). Cada modificación recalculará de inmediato la estructura local del cliente.
- **Consistencia:** Consistencia Fuerte local mediante funciones puras de cómputo inmutables, previniendo condiciones de carrera al procesar cambios síncronos en los inputs.

### 5.2. System Resilience & Error Handling Strategy
- **Manejo de Fallas en Dependencias:** En caso de falla en la sincronización con el servidor de catálogo, el cliente usará una caché local temporal del catálogo base.
- **Patrones de Tolerancia a Fallos:** Validaciones síncronas en tiempo de entrada (input validation), sanitización de entradas numéricas (prevención de cantidades ≤ 0 o `NaN`), y deshabilitación proactiva de la acción principal ("Generar PDF") ante estados inválidos.
- **Proporcionalidad:** Diseño liviano sin sobre-ingeniería; la complejidad de resiliencia está acotada al cómputo y validaciones reactivas en UI.

### 5.3. ARCHITECTURE DECISION RECORDS (ADR - Formato MADR)

#### ADR-001: Adopción de Subordinación a la Constitución Técnica BMAD (Modo Brownfield)
- **Estado:** Aceptado (heredado)
- **Contexto:** Definido según el archivo `.specify/memory/constitution.md` del proyecto activo.
- **Decisión:** Respetar la estructura física `app/frontend/` y `app/backend/` e identificador secuencial universal `001-HU_configurador_y_calculo_cotizaciones`.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Alineación 100% con la gobernanza global y flujo GitOps del ecosistema.
  - ⚠️ **Trade-off / Costo Real:** Restricción de autonomía en la elección de la estructura de carpetas raíz.

#### ADR-002: Motor de Cálculo Puramente Funcional en Cliente (Client-Side Reactive Engine)
- **Estado:** Aceptado
- **Contexto:** Se requiere recálculo en tiempo real e instantáneo de subtotales y total general sin latencia de red al interactuar con el configurador de servicios.
- **Decisión:** Implementar el cálculo en una capa puramente funcional e inmutable en TypeScript dentro de `app/frontend/src/engine/calculationEngine.ts`.
- **Alternativas Consideradas:**
  - **Alternativa A (Cómputo en Servidor vía API REST en cada cambio):** Descartada por introducir latencia de red en cada keystroke/checkbox y degradar la experiencia UX definida en `ux_001_configurador_y_calculo_cotizaciones.md`.
  - **Alternativa B (Cómputo desacoplado con WebSockets):** Descartada por sobre-ingeniería innecesaria para operaciones matemáticas deterministas y locales.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Latencia < 1ms en recálculos, feedback inmediato al usuario, reducción de carga en el backend.
  - ⚠️ **Trade-off / Costo Real:** Requiere re-validación idéntica en backend antes de la persistencia final de la cotización para evitar manipulación en el cliente.

#### ADR-003: Estrategia de Validación Restrictiva de Cantidades y Estados Vacíos
- **Estado:** Aceptado
- **Contexto:** El Escenario 02 (Sad Path) y la Matriz de Casos Borde exigen bloquear cálculos ante cantidades ≤ 0 y desactivar la generación de propuesta si no existen ítems válidos.
- **Decisión:** Diseñar validadores síncronos que marquen el estado de error de la cotización (`isValid: false`), impidan la actualización del total general con valores corruptos y deshabiliten la acción primaria ("Generar PDF").
- **Alternativas Consideradas:**
  - **Alternativa A (Silenciar errores y resetear a 1 por defecto):** Descartada porque altera la intención explícita del usuario sin su consentimiento.
- **Consecuencias:**
  - ✅ **Impacto Positivo:** Garantiza integridad matemática absoluta y previene la emisión de cotizaciones inconsistentes o en cero.
  - ⚠️ **Trade-off / Costo Real:** Bloqueo explícito en la UI hasta que el usuario corrija los datos de entrada.

## 6. Coding Conventions
- **Naming:** CamelCase para variables y funciones (`calculateSubtotal`, `selectedServices`), PascalCase para Componentes React e Interfaces TypeScript (`QuoteSummaryCard`, `ServiceItem`).
- **Organización:** Funciones puras de motor separadas de los componentes UI de React.
- **Error handling:** Validaciones en nivel de motor retornan objetos estructurados `{ isValid: boolean, errors: Record<string, string>, data: CalculationResult }`.
- **Async patterns:** Usar `async/await` para llamadas de API backend.

## 7. Testing
- **Qué debe testearse:** 
  1. Unit Tests del Motor de Cálculo (`calculationEngine.test.ts`): Cobertura del 100% de escenarios BDD (Happy Path, Sad Path con cantidades ≤ 0, eliminación/deselección de ítems).
  2. Integration Tests de Componentes UI: Renderizado del configurador y actualización reactiva de la tarjeta de resumen.
- **Dónde están los tests:** `app/frontend/src/engine/__tests__/` y `app/frontend/src/components/__tests__/`.

## 8. Security
- **Manejo de secretos:** Todas las credenciales e inyecciones de entorno vía `process.env` / `.env`.
- **Datos sensibles:** Ningún dato sensible en almacenamiento local o logs.

## 9. Database
- **Schema:** Relacional PostgreSQL (Tablas `services_catalog`, `quotes`, `quote_items`).
- **Reglas para modificar DB:** Migraciones SQL controladas en `app/backend/migrations/`.

## 10. Git & PR Rules
- **Naming de branches:** `feat/001-HU_configurador_y_calculo_cotizaciones` (Prolongada hasta dictamen final de QA-Tech).
- **Commits:** Mensajes bajo convención Conventional Commits (`feat: ...`, `fix: ...`, `docs: ...`).

## 11. Agent Instructions (Dev Guidelines)
- **Qué debe hacer antes de modificar código:** Verificar la existencia de `001-HU_configurador_y_calculo_cotizaciones.md` y `tech_guidelines.md`.
- **Qué debe validar después:** Ejecutar `npm test` para asegurar que el motor de cálculo cumpla con la precisión matemática y las reglas de validación.

## 12. Definition of Done
- Todo el código nuevo cuenta con patrones de resiliencia y manejo de estado definidos.
- No hay ninguna credencial o variable de entorno hardcodeada.
- El motor de cálculo soporta el 100% de los escenarios BDD de la HU `001-HU_configurador_y_calculo_cotizaciones`.
- Tests unitarios y de integración pasan exitosamente.
