---
description: 'Reglas estrictas para la ejecución de comandos de terminal (CLI) en modo automatizado y prevención de bloqueos por interactividad.'
applyTo: '**'
---

# ⚠️ PROTOCOLO ESTRICTO DE EJECUCIÓN CLI (NON-INTERACTIVE MODE)

Como desarrollador Frontend automatizado, estás equipado con la herramienta `execute_command`. Toda ejecución en la terminal debe ser **100% silenciosa y no interactiva (Headless)**. Tienes estrictamente prohibido ejecutar comandos que disparen *prompts* (preguntas) que requieran presionar [Enter] o escribir respuestas (Y/n), ya que esto congelará permanentemente el entorno.

## REGLAS DE ANDAMIAJE (SCAFFOLDING) Y DEPENDENCIAS
1. **Creación de Proyectos (Angular CLI):** 
   Debes proveer absolutamente todas las opciones de configuración mediante *flags* explícitos.
   - ❌ INcorrecto: `ng new mi-proyecto`
   - ✅ CORRECTO: `ng new mi-proyecto --defaults --routing --style=scss --skip-git --standalone`
2. **Generación de Componentes/Artefactos:**
   Aplica flags de evasión de confirmación.
   - ✅ CORRECTO: `ng generate component shared/ui/button --skip-tests --inline-style`
3. **Gestión de Paquetes (NPM/Yarn/PNPM):**
   Fuerza siempre la aceptación afirmativa y omite auditorías si es necesario.
   - ✅ CORRECTO: `npm install -y` o `npm init -y`
4. **Manejo de Errores de CLI:**
   Si un comando falla, no intentes ejecutar un "modo interactivo" para debugear. Lee el `stderr`, corrige tu comando añadiendo los flags correspondientes y vuelve a ejecutar.


## REGLAS DE CONTROL DE VERSIONES (GIT HEADLESS)

Tras implementar el código de cada tarea, debes ejecutar un **commit atómico** local. Git es tu herramienta de trazabilidad, pero operas bajo restricciones estrictas de seguridad.

> **Nota:** El flag `--skip-git` en `ng new` es correcto — el agente gestiona Git manualmente, no delega al Angular CLI.

### Patrón Obligatorio de Commit
```bash
# 1. Agregar SOLO los archivos específicos generados por la tarea
git add src/app/features/login/login-form.component.ts
git add src/app/features/login/login-form.component.html
git add src/app/core/services/auth.service.ts

# 2. Commit con mensaje inline siguiendo Conventional Commits + TASK-ID
git commit -m "feat(login): implementar LoginFormComponent standalone con Signals [TASK-042-FE-01]"
```

### Comandos PROHIBIDOS (Lista Negra)
```bash
# ❌ PROHIBIDO — abre vim/nano y congela el agente permanentemente
git commit

# ❌ PROHIBIDO — puede incluir archivos del tracker o de otro agente
git add .

# ❌ PROHIBIDO — operación remota, rompe la restricción de seguridad
git push
git push origin feat/HU-042-registro-usuario

# ❌ PROHIBIDO — interactivo, congela la terminal
git commit --amend
git rebase -i HEAD~3

# ❌ PROHIBIDO — resolución autónoma de conflictos no autorizada
git merge
git rebase
git pull
```

### Protocolo de Error Git
Si `git add` o `git commit` retorna un error o detecta un conflicto:
1. **ABORTA** inmediatamente la ejecución de la tarea.
2. **REPORTA** el error exacto (`stderr`) en el `tracker_bmad.md` con la etiqueta `@HUMANO:`.
3. **DEVUELVE** el turno — no continúes con las siguientes tareas.
4. **NUNCA** intentes resolver conflictos de Git de forma autónoma.