# Reporte de Auditoría BMAD - Meta-Arquitectura y QA

## 📊 Estado de Salud Global
🟡 **CON ADVERTENCIAS:** El ecosistema de agentes, las plantillas y el orquestador (`watcher_bmad.py`) están estructuralmente alineados con los pilares de GitOps y SDD. Sin embargo, se identificó un cuello de botella lógico en el handoff entre la Fase de QA Documental y el SDD Auto-Runner que podría romper la autonomía del enjambre.

---

## 🏗️ Hallazgos por Pilar

### 1. Auditoría del Orquestador (`watcher_bmad.py`)
- [x] **Intercepción de Macros GitOps:** El loop principal captura e interpreta correctamente `@WATCHER: GITOPS-BRANCH-CREATE` y `@WATCHER: GITOPS-MERGE-CLOSE` utilizando expresiones regulares.
- [x] **Mecanismos de Seguridad Git:** Se valida exitosamente la limpieza del directorio (`git status --porcelain`) mediante `check_working_directory_clean()` y se realizan auto-commits profilácticos con `auto_commit_security()` antes de saltar de rama.
- [x] **Degradación Elegante:** El proceso de fusión `git merge --no-ff` está envuelto en un bloque `try/except` que dispara `git merge --abort` si existen conflictos, emitiendo un token de detención `@HUMANO:` para salvaguardar el código.

### 2. Auditoría de Coherencia de Agentes (Instrucciones)
- [x] **Creación Transaccional (@PM):** Se verificó en `product-manager/instructions/mvp-template.instructions.md` la obligatoriedad de inyectar la macro de creación de rama antes de delegar al `@BA`.
- [x] **Cierre de Ciclo (@QT):** Se verificó en `qa-tech/instructions/tech-design-template.instructions.md` la orden de inyectar la macro de fusión antes del disparador `@SPEC-KIT:`.
- [x] **Lectura Brownfield (@BA y @SA):** Ambos agentes (`business-analyst.agent.md` y `solutions-architect.agent.md`) contienen directivas estrictas de lectura inicial (`specs/README.md`) antes de emitir cualquier propuesta.
- 🔴 **ANOMALÍA (Dead-end en QA Documental):** En `qa-documental/instructions/qa-report-template.instructions.md`, la instrucción a imprimir en el tracker dice:
  `@UX: La Historia de Usuario [NOMBRE_HU] ha sido aprobada por QA.`
  El orquestador (`watcher_bmad.py`) usa la expresión regular `r'(?:files[/\\]business-analyst[/\\])?(hu_[a-zA-Z0-9_-]+\.md)'` para buscar el archivo. Si el QA inyecta el título en lenguaje natural en lugar de `{{NOMBRE_ARCHIVO_HU}}` (ej. `hu_01_login.md`), la regex fallará, el *SDD Auto-Runner* no podrá iniciarse automáticamente y el enjambre se pausará exigiendo la ejecución manual de Spec Kit.

### 3. Auditoría de SSOT y Documentación
- [x] **Product State Ledger:** La plantilla `.specify/templates/spec-template.md` ha sido purgada de su estado interno y ahora redirige explícitamente a `🔗 Consolidado en specs/README.md`.
- [x] **Constitución Técnica:** `.specify/memory/constitution.md` incorpora la sección "ESTÁNDAR GITOPS Y CICLO DE VIDA (FEATURE BRANCHING)", rigiendo las reglas de aislamiento y control de versiones.
- [x] **Skill de Logging:** `skills/tracker-logger/SKILL.md` incluye a las macros de Watcher como directivas autorizadas, permitiendo a los agentes emitirlas sin depender de la interacción del humano (salto a `@HUMANO:`).

---

## 🚨 Vulnerabilidades y Propuestas de Resolución

1. **Fallo en Handoff QA Documental -> SDD Auto-Runner (Mencionada arriba)**
   - **Riesgo:** Pérdida de autonomía; intervención humana forzosa en cada transición de etapa de análisis a etapa técnica.
   - **Solución Propuesta:** Modificar el archivo `qa-report-template.instructions.md` y cambiar `[NOMBRE_HU]` por `{{NOMBRE_ARCHIVO_HU}}` en las instrucciones para el tracker (opciones web y headless).
2. **State Hydration Tras Conflicto de Merge**
   - **Riesgo:** Si un `GITOPS-MERGE-CLOSE` falla por conflicto (ej. la rama `dev` avanzó), el Watcher aborta el merge y se apaga solicitando resolución manual. Al estar escrita ya la macro `CLOSE` en el tracker por el `@QT`, cuando el humano reinicie el Watcher, la función `hydration_gitops()` verá un match pareado (CREATE - CLOSE) asumiendo que la rama finalizó, no reanudando en la rama `feat`.
   - **Resolución:** No requiere arreglo de código, pero sí educación al usuario. El humano debe saber que, si hay conflicto de merge, **debe completarlo manualmente** y hacer push a `dev` antes de reanudar el tracker (o simplemente aceptar la continuación porque la feature branch ya perdió relevancia aislada).
