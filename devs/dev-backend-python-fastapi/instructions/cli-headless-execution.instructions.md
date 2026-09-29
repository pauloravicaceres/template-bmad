---
description: 'Reglas estrictas para la ejecución de comandos de terminal (CLI) en modo automatizado y prevención de bloqueos por interactividad.'
applyTo: '**'
---

# ⚠️ PROTOCOLO ESTRICTO DE EJECUCIÓN CLI (NON-INTERACTIVE MODE)

Como desarrollador Backend automatizado, estás equipado con la herramienta `execute_command`. Toda ejecución en la terminal debe ser **100% silenciosa y no interactiva (Headless)**. Tienes estrictamente prohibido ejecutar comandos que disparen *prompts* que requieran interacción humana o flujos bloqueantes, ya que esto congelará permanentemente el framework BMAD.

## REGLAS DE ENTORNO Y EJECUCIÓN DE PYTHON
1. **Gestión de Paquetes (`pip` / `uv`):** 
   Utiliza siempre la versión exacta y los flags que suprimen logs innecesarios o preguntas.
   - ❌ INcorrecto: `pip install fastapi`
   - ✅ CORRECTO: `pip install fastapi==0.103.1 uvicorn==0.23.2 -q`
2. **Eficiencia en Compilación (Build/Run):**
   No ejecutes `uvicorn main:app --reload` que deje el proceso vivo colgando tu terminal, a menos que el usuario lo autorice como tarea de fondo. Para comprobar si tu código tiene errores sintácticos rápidos, compílalo explícitamente:
   - ✅ CORRECTO: `python -m py_compile backend/main.py`
3. **Manejo de Dependencias (requirements.txt):**
   - ✅ CORRECTO: `pip install -r requirements.txt -q`


## REGLAS DE CONTROL DE VERSIONES (GIT HEADLESS)

Tras implementar el código de cada tarea, debes ejecutar un **commit atómico** local. Git es tu herramienta de trazabilidad, pero operas bajo restricciones estrictas de seguridad.

### Patrón Obligatorio de Commit
```bash
# 1. Agregar SOLO los archivos específicos generados por la tarea
git add backend/routers/hitl.py
git add backend/models/hitl_models.py

# 2. Commit con mensaje inline siguiendo Conventional Commits + TASK-ID
git commit -m "feat(hitl): implementar endpoint REST de aprobación [TASK-042-BE-01]"
```

### Comandos PROHIBIDOS (Lista Negra)
```bash
# ❌ PROHIBIDO — abre vim/nano y congela el agente permanentemente
git commit

# ❌ PROHIBIDO — puede incluir archivos del tracker o de otro agente
git add .

# ❌ PROHIBIDO — operación remota, rompe la restricción de seguridad
git push
git push origin feat/HU-042-registro

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