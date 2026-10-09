# Entradas y entregables por rol

Los perfiles compartidos `<rol>/AGENTS.md` contienen las directivas; sus fuentes están en `agents/`, `instructions/` y skills. [config.py](bmad_runtime/config.py) asigna fases y [GUIDE.md](GUIDE.md) describe el flujo ejecutado.

Cada rol lee la configuración efectiva (`BMAD_CONFIG`), el tracker (`BMAD_TRACKER`), la constitución del workspace y los artefactos relacionados con su tarea. `documents/`, `specs/`, `app/` y `.specify/` son relativos al workspace. Skills, perfiles y plantillas compartidos se leen desde `ENGINE_ROOT`; no se copian al proyecto.

| Rol / token | Fase | Entradas principales | Salidas y siguiente paso |
|---|---|---|---|
| Business Storyteller / BS | B | Idea del humano | `documents/business-storyteller/idea_*.md`; PA |
| Product Analyst / PA | B | Idea estructurada | `documents/product-analyst/pb_*.md`; aprobación humana |
| Product Manager / PM | M | PB aprobado, ledger y backlog | `documents/product-manager/mvp_*.md`; priorización y BA |
| Business Analyst / BA | M | PB, MVP, HU y feedback si hay rechazo | HU técnica en `documents/business-analyst/` y narrativa en `HUs-stakeholders/`; QA |
| QA Documental / QA | M | HU y PB | Aprobación o feedback en `documents/qa-documental/`; compuerta specify/clarify o BA |
| Designer UX / UX | A | HU, spec, tareas y PB | `documents/designer-ux/ux_*.md`; SA cuando corresponde |
| Solutions Architect / SA | A | PB, MVP, spec, UX y constitución | `documents/solutions-architect/tech_guidelines.md`; compuerta SDD-FREEZE |
| Data Architect / DA | A | Guidelines, HU y spec | `documents/data-architect/db_*.md`; API o QT según necesidad |
| API Architect / API | A | Guidelines, datos y HU | `documents/api-architect/api_*.md`; QT |
| QA Tech / QT | A | Spec, guidelines, datos y contratos | `documents/qa-tech/tech-design_*.md`; implementación |
| Dev Backend / DEV-BACK | D | Spec, plan, tareas, contratos y perfil | Código en `code_dirs.backend`, arquitectura de capa y README; operación headless |
| Dev Frontend / DEV-FRONT | D | Spec, plan, tareas, UX y contratos | Código en `code_dirs.frontend`, arquitectura de capa y README; operación headless |
| QA Automation / QA-AUTO | D | Código, criterios de aceptación y tareas | Pruebas y `documents/qa-auto/qa-report.md`; Code Review o retrabajo |
| Code Review / CODE-REVIEW | D | Código, pruebas, diseño y constitución | Dictamen en tracker y artefactos de `documents/code-review/`; cierre o retrabajo |
| DevOps / DEVOPS | D | Diseño y aplicación aprobados | Infraestructura y documentación en el workspace |

Los nombres de HU conservan el identificador universal `XXX-HU_nombre`. Las operaciones headless no emiten handoffs independientes: el watcher registra su resultado y deriva a revisión. En un workspace explícito, los handoffs y el tracker viven en `handoffs/`; el contrato del runtime sustituye las rutas implícitas de los perfiles.
