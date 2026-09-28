---
description: 'Reglas estrictas para la ejecución de comandos de terminal (CLI) en modo automatizado y prevención de bloqueos por interactividad. Aplica al agente DevOps.'
applyTo: '**'
---

# 🛡️ PROTOCOLO ESTRICTO DE EJECUCIÓN CLI (NON-INTERACTIVE MODE) — DEVOPS

Como agente DevOps automatizado, estás equipado con la herramienta `execute_command`. Toda ejecución en la terminal debe ser **100% silenciosa y no interactiva (Headless)**. Tienes estrictamente prohibido ejecutar comandos que disparen *prompts* que requieran interacción humana, flujos de autenticación web emergentes o confirmaciones, ya que esto congelará permanentemente el framework BMAD.

## REGLAS DE INFRAESTRUCTURA Y CI/CD (ZERO-INTERACTIVE)

### 1. Docker y Contenedores
Siempre usa flags no interactivos. Nunca lances contenedores en modo foreground que bloqueen la terminal.
- ❌ INCORRECTO: `docker run -it imagen` (modo interactivo)
- ✅ CORRECTO: `docker build -t nombre:tag . --no-cache --quiet`
- ✅ CORRECTO: `docker compose up -d --build 2>&1` (modo daemon/detached)
- ✅ CORRECTO: `docker compose down --remove-orphans 2>&1`

### 2. Gestión de Paquetes / Dependencias
- ❌ INCORRECTO: `npm install` (puede interactuar con peer deps)
- ✅ CORRECTO: `npm ci --silent`
- ✅ CORRECTO: `pip install -r requirements.txt --quiet --no-input`
- ✅ CORRECTO: `apt-get install -y paquete` (flag `-y` suprime confirmaciones)

### 3. Herramientas de Infraestructura como Código (IaC)
- ✅ CORRECTO: `terraform init -input=false -no-color 2>&1`
- ✅ CORRECTO: `terraform plan -input=false -no-color -out=tfplan 2>&1`
- ✅ CORRECTO: `terraform apply -input=false -auto-approve tfplan 2>&1`
- ❌ INCORRECTO: `terraform apply` sin `-auto-approve` (espera confirmación manual)

### 4. CI/CD Pipelines y Scripts
- Todos los scripts de pipeline deben tener `set -e` (bash) o `$ErrorActionPreference = "Stop"` (PowerShell) para fallar rápido.
- ✅ CORRECTO: `pwsh -NonInteractive -Command "..."`
- ✅ CORRECTO: `bash -c "set -e; comando1 && comando2"`
- ❌ INCORRECTO: Cualquier script con `read -p` o `Prompt` interactivo.

### 5. Git y Control de Versiones (REGLAS BMAD)

Tras generar cada archivo de infraestructura, debes ejecutar un **commit atómico** local. Operas bajo las mismas restricciones de seguridad Git que todos los agentes constructores del framework BMAD.

**Patrón Obligatorio de Commit:**
```bash
# 1. Agregar SOLO los archivos específicos generados por la tarea
git add docker-compose.yml
git add src/Auth.Api/Dockerfile

# 2. Commit con mensaje inline siguiendo Conventional Commits + TASK-ID
git commit -m "infra(docker): agregar servicio auth-api al docker-compose.yml [TASK-042-OPS-01]"
git commit -m "chore(docker): configurar multi-stage build para Auth.Api [TASK-042-OPS-02]"
```

**Clonación de repositorios (lectura):**
- ✅ CORRECTO: `git clone --depth=1 --quiet https://repo.git`

**Comandos PROHIBIDOS (Lista Negra):**
```bash
# ❌ PROHIBIDO — abre editor y congela el agente permanentemente
git commit

# ❌ PROHIBIDO — puede incluir archivos del tracker o de otro agente
git add .

# ❌ PROHIBIDO — operación remota, rompe la restricción de seguridad BMAD
git push
git push origin main
git push --no-verify origin main

# ❌ PROHIBIDO — interactivo, congela la terminal
git commit --amend
git rebase -i HEAD~3

# ❌ PROHIBIDO — resolución autónoma de conflictos no autorizada
git merge
git rebase
git pull
```

**Protocolo de Error Git:**
Si `git add` o `git commit` retorna un error o detecta un conflicto:
1. **ABORTA** inmediatamente la ejecución de la tarea.
2. **REPORTA** el error exacto (`stderr`) en el `tracker_bmad.md` con la etiqueta `@HUMANO:`.
3. **DEVUELVE** el turno — no continúes con las siguientes tareas.
4. **NUNCA** intentes resolver conflictos de Git de forma autónoma.

### 6. Verificación de Salud (Health Checks)
- Usa `curl` o `wget` con timeouts explícitos para verificar servicios.
- ✅ CORRECTO: `curl --fail --silent --max-time 10 http://localhost:8080/health`
- ✅ CORRECTO: `docker compose ps 2>&1` para verificar estado de contenedores

### 7. Política de Manejo de Errores
- Si un comando falla (exit code != 0), **documenta el error completo** en el tracker con `⚠️ FALLO:` y la salida del stderr.
- **NUNCA** silencies errores críticos con `2>/dev/null` sin documentarlos.
- Ante un fallo de infraestructura, emite `@HUMANO:` con el diagnóstico. No intentes recuperación autónoma destructiva.
