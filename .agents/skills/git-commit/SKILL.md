---
name: 'git-commit'
description: 'Skill global para la ejecución segura y estandarizada de commits atómicos en modo Headless, aplicando Conventional Commits v1.0 y previniendo bloqueos del framework.'
---

# 🌿 SKILL: GIT COMMIT HEADLESS Y CONVENTIONAL COMMITS

Como agente constructor en el ecosistema BMAD, estás restringido a un entorno **Headless (No interactivo)**. Debes registrar tu progreso mediante Commits Atómicos locales por cada tarea que completes, asegurando la trazabilidad sin bloquear la terminal.

## 1. ALGORITMO DE COMMIT ATÓMICO

Sigue estrictamente este flujo después de generar los archivos de una tarea:

1. **`git add {archivos_especificos}`**: Añade explícitamente los archivos creados o modificados. **PROHIBIDO USAR `git add .`**.
2. **`git commit -m "{tipo}({scope}): {descripcion} [{TASK-ID}]"`**: Crea el commit con el mensaje en línea, previniendo que se abra el editor de texto.
3. Si el comando falla o da conflicto, **ABORTA** la tarea, reporta el error exacto (stderr) en el `tracker_bmad.md` delegando a `@HUMANO:` y detén tu ejecución.

## 2. CONVENTIONAL COMMITS PERMITIDOS

La nomenclatura es estricta: `<tipo>(<scope>): <descripción imperativa en minúsculas> [TASK-{ID}]`

| Agente | Tipos Permitidos | Ejemplos de Uso |
|:---|:---|:---|
| `@DEV-BACK` | `feat`, `fix`, `refactor`, `chore` | `feat(auth): implementar LoginCommandHandler [TASK-042-BE-01]` |
| `@DEV-FRONT` | `feat`, `fix`, `refactor`, `chore` | `feat(login): generar LoginFormComponent standalone [TASK-042-FE-01]` |
| `@DEVOPS` | `infra`, `chore` | `infra(docker): agregar auth-api a docker-compose.yml [TASK-042-OPS-01]` |
| `@QA-AUTO` | `test` | `test(auth): pruebas xUnit para LoginCommandHandler [TASK-042-QA-01]` |

**Reglas de Formato:**
- **Descripción:** Siempre en imperativo y minúsculas (ej. "implementar", "agregar", no "Implementa" ni "agregado").
- **TASK-ID:** Obligatorio al final de la línea. Vincula el código con el Spec Kit.

## 3. LISTA NEGRA: COMANDOS ESTRICTAMENTE PROHIBIDOS ❌

Si ejecutas alguno de estos comandos, congelarás el framework BMAD y causarás un fallo crítico en el sistema:

- ❌ `git commit` (Sin el flag `-m`, abrirá Vim/Nano esperando input que no puedes dar).
- ❌ `git add .` (Podría incluir archivos del tracker en ejecución u otros artefactos).
- ❌ `git push` o `git push origin {rama}` (El push es privilegio EXCLUSIVO del Humano).
- ❌ `git commit --amend`
- ❌ `git rebase -i`
- ❌ `git merge`
- ❌ `git pull`
