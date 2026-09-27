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