---
description: 'Reglas estrictas para la ejecución de comandos de terminal (CLI) en modo automatizado y prevención de bloqueos por interactividad. Aplica al agente QA Automation.'
applyTo: '**'
---

# 🛡️ PROTOCOLO ESTRICTO DE EJECUCIÓN CLI (NON-INTERACTIVE MODE) — QA AUTOMATION

Como agente QA Automation automatizado, estás equipado con la herramienta `execute_command`. Toda ejecución en la terminal debe ser **100% silenciosa y no interactiva (Headless)**. Tienes estrictamente prohibido ejecutar comandos que disparen *prompts* que requieran interacción humana, flujos de autenticación web emergentes o confirmaciones, ya que esto congelará permanentemente el framework BMAD.

## REGLAS DE EJECUCIÓN DE PRUEBAS (ZERO-INTERACTIVE)

### 1. Ejecución de Suites de Prueba
Siempre usa flags que supriman interactividad y fuerzan salida determinista.
- ❌ INCORRECTO: `dotnet test` (puede pedir confirmaciones en fallos)
- ✅ CORRECTO: `dotnet test --no-build --logger "console;verbosity=normal" -- xunit.parallelizeAssembly=false`
- ✅ CORRECTO (Node/Vitest): `npx vitest run --reporter=verbose --no-color 2>&1`
- ✅ CORRECTO (Jest): `npx jest --ci --runInBand --forceExit --no-coverage 2>&1`
- ✅ CORRECTO (Playwright): `npx playwright test --reporter=list 2>&1`

### 2. Instalación de Dependencias de Test
Nunca ejecutes instaladores que requieran confirmación.
- ❌ INCORRECTO: `npm install` (puede preguntar sobre peer deps)
- ✅ CORRECTO: `npm ci --silent` (usa lockfile, silencioso)
- ✅ CORRECTO: `dotnet restore --no-interactive --locked-mode`

### 3. Generación de Reportes de Cobertura
Genera reportes a archivo, nunca abrir browser interactivo.
- ✅ CORRECTO: `dotnet test /p:CollectCoverage=true /p:CoverletOutputFormat=lcov /p:CoverletOutput=./coverage/lcov.info`
- ✅ CORRECTO: `npx vitest run --coverage --coverage.reporter=lcov 2>&1`
- ❌ INCORRECTO: Cualquier comando con `--open` o `--watch`

### 4. Playwright / E2E — Modo Headless Estricto
- ✅ CORRECTO: `npx playwright test --headed=false --workers=2 2>&1`
- ❌ INCORRECTO: `npx playwright test --ui` (lanza interfaz gráfica interactiva)

### 5. Reglas de Timeout y Salida
- Todos los procesos deben terminar con un código de salida. Si un test suite cuelga más de 5 minutos, mata el proceso y documenta el timeout como fallo.
- Usa `--timeout` explícito cuando la herramienta lo soporte.

### 6. Política Anti-Tautología (Zero-Trust en Tests)
- **NUNCA** escribas aserciones que siempre pasen (`assert true == true`).
- Cada test debe poder fallar de forma realista. Documenta el "Happy Path" y el "Sad Path" para cada Criterio de Aceptación.
- Si un test falla, **NO lo comentes ni lo desactivas** — documenta el fallo en el tracker y escala al `@CODE-REVIEW:`.

## CONTROL DE VERSIONES (GIT HEADLESS)

Tras generar cada suite de pruebas, debes ejecutar un **commit atómico** local. Git es tu herramienta de trazabilidad, pero operas bajo restricciones estrictas de seguridad.

### Patrón Obligatorio de Commit
```bash
# 1. Agregar SOLO los archivos de test específicos de la suite generada
git add tests/Auth.UnitTests/LoginCommandHandlerTests.cs
git add tests/Auth.IntegrationTests/LoginEndpointTests.cs

# 2. Commit con mensaje inline usando tipo 'test' + scope + TASK-ID
git commit -m "test(auth): pruebas unitarias LoginCommandHandler con xUnit [TASK-042-QA-01]"
git commit -m "test(login): pruebas E2E Playwright flujo de login [TASK-042-QA-02]"
```

### Comandos PROHIBIDOS (Lista Negra)
```bash
# ❌ PROHIBIDO — abre editor y congela el agente permanentemente
git commit

# ❌ PROHIBIDO — puede incluir archivos del tracker o de otro agente
git add .

# ❌ PROHIBIDO — operación remota, rompe la restricción de seguridad
git push

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
