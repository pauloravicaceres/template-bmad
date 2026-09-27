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