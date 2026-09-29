---
description: 'Reglas estrictas para la ejecución de comandos de terminal (CLI) en modo automatizado y prevención de bloqueos por interactividad.'
applyTo: '**'
---

# ⚠️ PROTOCOLO ESTRICTO DE EJECUCIÓN CLI (NON-INTERACTIVE MODE)

Como desarrollador Backend automatizado, estás equipado con la herramienta `execute_command`. Toda ejecución en la terminal debe ser **100% silenciosa y no interactiva (Headless)**. Tienes estrictamente prohibido ejecutar comandos que disparen *prompts* que requieran interacción humana, flujos de autenticación web emergentes o confirmaciones, ya que esto congelará permanentemente el framework BMAD.

## REGLAS DE ANDAMIAJE (SCAFFOLDING) Y COMPILACIÓN
1. **Creación de Soluciones y Proyectos (.NET CLI):** 
   Utiliza siempre la declaración explícita de nombres, salidas y evita restauraciones interactivas.
   - ❌ INcorrecto: `dotnet new webapi`
   - ✅ CORRECTO: `dotnet new webapi -n MiModulo.Api -o src/MiModulo.Api --no-restore`
   - ✅ CORRECTO: `dotnet sln add src/MiModulo.Api/MiModulo.Api.csproj`
2. **Gestión de Paquetes NuGet:**
   Si hay conflictos de versiones, especifica la versión exacta en lugar de dejar que el CLI pregunte.
   - ✅ CORRECTO: `dotnet add package Dapper --version 2.1.35`
3. **Eficiencia en Compilación (Build/Run):**
   No ejecutes `dotnet run` que deje el proceso vivo colgando tu terminal si solo necesitas verificar la sintaxis. Utiliza `dotnet build` para comprobar que el código es válido.
   - ✅ CORRECTO: `dotnet build --no-restore -verbosity:quiet`
4. **Manejo de Entity Framework Core:**
   Si requieres ejecutar migraciones, usa los flags de no-interacción.
   - ✅ CORRECTO: `dotnet ef migrations add InitialCreate --project src/Data --startup-project src/Api --no-build`


## REGLAS DE CONTROL DE VERSIONES (GIT HEADLESS)

Tras implementar el código de cada tarea, debes ejecutar un **commit atómico** local. Git es tu herramienta de trazabilidad, pero operas bajo restricciones estrictas de seguridad.

### Patrón Obligatorio de Commit
```bash
# 1. Agregar SOLO los archivos específicos generados por la tarea
git add src/Auth/Features/Login/LoginEndpoint.cs
git add src/Auth/Features/Login/LoginCommand.cs

# 2. Commit con mensaje inline siguiendo Conventional Commits + TASK-ID
git commit -m "feat(auth): implementar endpoint POST /api/auth/login [TASK-042-BE-01]"
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