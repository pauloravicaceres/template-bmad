# Crear START.md — Guía definitiva para iniciar y utilizar el orquestador BMAD/SDD + Spec Kit + Multiworkspace v1.0

## 1. Contexto

Tenemos implementado el framework de orquestación **Herdr + BMAD + SDD + Spec Kit + Multiworkspace v1.0**.

Sin embargo, tengo un problema importante: **no entiendo claramente cómo ponerlo en funcionamiento ni cómo empezar a trabajar con un proyecto nuevo**.

La documentación actual está distribuida entre ARCHITECTURE.md, SETUP.md, README.md, GUIDE.md y otros archivos, y me resulta difícil identificar qué pasos debo seguir realmente.

Necesito una guía única, sencilla, práctica y ordenada.

## 2. Objetivo

Crea un archivo llamado:

`START.md`

En la raíz del repositorio:

`D:\Paulo\Cursos\DMC\template-bmad\START.md`

Este archivo debe ser un **manual de inicio rápido, paso a paso, para una persona que nunca ha utilizado este orquestador**.

Quiero poder abrir START.md y seguir sus instrucciones desde el principio hasta tener:

- El backend funcionando.
- El frontend funcionando.
- El watcher funcionando.
- Herdr funcionando.
- Los agentes disponibles (Claude, Codex y los roles configurados).
- Un proyecto nuevo correctamente inicializado.
- El flujo BMAD/SDD o Spec Kit preparado para comenzar.
- Una primera instrucción enviada y una forma sencilla de verificar que el orquestador está trabajando.

**Muy importante: el proyecto nuevo empieza con una carpeta completamente vacía.**

No presupongas que contiene carpetas, documentos, archivos de configuración, historias de usuario ni una estructura BMAD.

Explícame exactamente qué debe crearse, qué genera automáticamente el framework y qué debo crear manualmente.

## 3. Primero investiga la implementación real

ANTES de escribir START.md:

1. Revisa README.md, GUIDE.md, SETUP.md, ARCHITECTURE.md y la documentación relevante.
2. Revisa el código, CLI, scripts, configuraciones y puntos de entrada reales del proyecto.
3. Identifica cómo se inician realmente:
   - Backend del Control Center.
   - Frontend del Control Center.
   - Watcher.
   - Servidor y sesión Herdr.
   - Agentes Claude y Codex.
   - Dispatcher/orquestador.
4. Identifica cómo se configura y registra un workspace nuevo.
5. Identifica cómo se elige o activa BMAD/SDD y Spec Kit.
6. Identifica los comandos existentes para inicializar, verificar, ejecutar y detener los componentes.
7. Identifica cuáles son los pasos manuales obligatorios, como aceptar la confianza de una carpeta o aprobar una fase BMAD.

**No inventes comandos, parámetros, archivos ni funcionalidades.**

Si algo no está implementado, dilo explícitamente. Si encuentras contradicciones entre documentación y código, utiliza el comportamiento real del código como referencia y señala la discrepancia.

No quiero una guía basada en cómo debería funcionar el framework, sino en **cómo funciona hoy la versión 1.0**.

## 4. Estructura obligatoria de START.md

### 0. ¿Qué voy a conseguir siguiendo esta guía?

Explícalo en términos sencillos.

Incluye un pequeño esquema del orden de arranque:

Backend → Frontend → Watcher → Herdr → Agentes → Proyecto nuevo → Primera tarea

Ajusta ese orden si el código demuestra que debe ser distinto.

Aclara cuáles componentes son obligatorios y cuáles opcionales.

### 1. Antes de comenzar

Explica qué necesito tener instalado y configurado:

- Python.
- Node.js/npm.
- Herdr.
- Claude Code CLI.
- Codex CLI.
- Otras dependencias realmente necesarias.

Incluye comandos para comprobar cada requisito.

No asumas que las dependencias están instaladas.

Indica cómo preparar las dependencias del repositorio utilizando los mecanismos que ya existen.

No incluyas procedimientos de instalación inventados.

### 2. Preparación inicial — SOLO LA PRIMERA VEZ

Detalla todos los pasos que debo ejecutar una sola vez para preparar el framework.

Por ejemplo, cuando realmente corresponda:

- Crear o activar un entorno virtual.
- Instalar dependencias del backend.
- Instalar dependencias del frontend.
- Preparar configuraciones.
- Validar herramientas y proveedores.
- Preparar carpetas necesarias.

Cada paso debe incluir:

- Terminal desde la que debo ejecutarlo.
- Carpeta en la que debo estar.
- Comando exacto.
- Resultado esperado.
- Cómo verificar que salió bien.

### 3. Cómo levantar el orquestador — CADA VEZ QUE QUIERA TRABAJAR

Esta es una de las secciones más importantes.

Explica, en el orden correcto, cómo iniciar TODOS los componentes necesarios.

Para cada componente indica:

**PASO N — Nombre del componente**

- ¿Para qué sirve? (máximo dos frases sencillas).
- ¿Desde qué carpeta se ejecuta?
- ¿Debo abrir una terminal nueva?
- ¿Qué comando exacto ejecuto?
- ¿Debo dejar esa terminal abierta?
- ¿Qué mensaje indica que arrancó correctamente?
- ¿Cómo compruebo que funciona?

Quiero que identifiques claramente las terminales:

- Terminal 1: Backend.
- Terminal 2: Frontend.
- Terminal 3: Watcher.
- Terminal 4: Herdr.
- Otras terminales, solo si son realmente necesarias.

Adapta la cantidad de terminales a la implementación real. No obligues a abrir terminales innecesarias.

Utiliza comandos de **Windows PowerShell**, porque ese es mi entorno.

### 4. Cómo crear un proyecto nuevo DESDE UNA CARPETA VACÍA

Esta es la otra sección más importante.

Supongamos que quiero crear:

`D:\Proyectos\MiNuevoProyecto`

Y esa carpeta está completamente vacía.

Explícame paso a paso:

1. Cómo crear la carpeta, si todavía no existe.
2. Cómo registrar el proyecto en el orquestador.
3. Qué identificador y nombre de workspace debo utilizar.
4. Cómo relacionar el proyecto con Herdr.
5. Qué estructura de carpetas necesita.
6. Qué archivos de configuración necesita.
7. Qué crea automáticamente el framework.
8. Qué archivos debo preparar o copiar manualmente.
9. Si debo incluir una constitución, instrucciones de agentes o alguna plantilla.
10. Cómo habilitar los roles BA, SA, QA y los demás que estén implementados.
11. Cómo verificar que los agentes trabajarán únicamente dentro del nuevo workspace.
12. Cómo confirmar que el proyecto quedó listo para empezar.

**No presupongas que el proyecto ya tiene un README, una carpeta docs, un tracker o historias de usuario.**

Si el framework cuenta con un comando de inicialización automática, enséñame a utilizarlo.

Si no existe, explica el procedimiento manual real, sin implementar un inicializador nuevo.

Incluye un ejemplo concreto, con rutas y comandos completos.

### 5. Cómo iniciar el primer flujo BMAD/SDD

Una vez que todo esté levantado y el workspace configurado:

- Explica cuál es el primer agente que debe intervenir.
- Qué documento o información inicial debo proporcionar.
- Dónde debo escribir la idea del proyecto.
- Cómo doy la primera instrucción.
- Cómo se comunica un agente con el siguiente.
- Qué hace automáticamente el orquestador.
- Cuándo debo aprobar manualmente.
- Cómo veo que una tarea está pendiente, trabajando, bloqueada o completada.
- Cómo sé cuándo corresponde intervenir.

Incluye un ejemplo sencillo con un proyecto ficticio.

Utiliza los roles y comandos realmente implementados.

### 6. ¿Y si quiero utilizar Spec Kit?

Explica si Spec Kit constituye un flujo separado, un modo de trabajo o una integración dentro del flujo principal.

Incluye los pasos concretos para utilizarlo desde un proyecto nuevo.

Aclara si hay comandos, archivos o configuraciones diferentes respecto de BMAD/SDD.

No asumas una integración que no esté implementada.

### 7. Cómo utilizar el Control Center

Explica:

- Qué URL local debo abrir.
- Qué información veré.
- Cómo identificar mi proyecto.
- Cómo ver los agentes.
- Cómo revisar tareas y aprobaciones.
- Cómo consultar errores.
- Qué acciones puedo realizar desde la interfaz y cuáles requieren CLI.

No inventes pantallas ni botones.

### 8. Cómo trabajar con dos o más proyectos

Explica de forma sencilla:

- Cómo registrar un segundo proyecto.
- Cómo elegir el proyecto activo.
- Cómo funcionan las sesiones y los workspaces.
- Cómo evitar que un agente escriba en el proyecto equivocado.
- Qué componentes son compartidos y cuáles pertenecen a cada proyecto.
- Qué debo ejecutar nuevamente al agregar otro proyecto.

Incluye un ejemplo con dos proyectos diferentes.

### 9. Cómo detener todo correctamente

Explica, en orden:

- Cómo detener agentes.
- Cómo detener watcher.
- Cómo detener Herdr.
- Cómo detener backend y frontend.
- Qué datos permanecen guardados.
- Cómo retomar el trabajo al día siguiente.

No propongas terminar procesos indiscriminadamente.

### 10. Problemas comunes

Incluye soluciones concretas a problemas como:

- El backend no arranca.
- El frontend no abre.
- El watcher no detecta cambios.
- Herdr no encuentra una sesión.
- Claude o Codex solicita confiar en una carpeta.
- Un agente aparece bloqueado.
- Una tarea queda esperando aprobación humana.
- El proyecto no aparece en el Control Center.
- El agente trabaja en un workspace incorrecto.
- El tracker no se actualiza.

Para cada caso:

**Síntoma → Causa probable → Qué comprobar → Cómo solucionarlo.**

No presentar soluciones especulativas como si fueran hechos.

### 11. Chuleta de comandos

Al final incluye una tabla breve con los comandos más importantes:

- Preparación inicial.
- Iniciar backend.
- Iniciar frontend.
- Iniciar watcher.
- Iniciar Herdr.
- Crear o registrar proyecto.
- Verificar estado.
- Iniciar flujo.
- Consultar tareas.
- Detener componentes.

Solo incluir comandos que realmente existen.

## 5. Etiquetas visuales obligatorias

Utiliza estas etiquetas de forma consistente en toda la guía:

- 🟢 **SOLO LA PRIMERA VEZ:** configuración que normalmente no debe repetirse.
- 🔵 **CADA VEZ QUE INICIES EL ORQUESTADOR:** pasos recurrentes.
- 🟡 **POR CADA PROYECTO NUEVO:** pasos para preparar otro workspace.
- 🟠 **CUANDO NECESITES INTERVENIR:** aprobaciones o decisiones manuales.
- 🔴 **IMPORTANTE:** advertencias y operaciones que requieren precaución.
- ✅ **VERIFICACIÓN:** cómo confirmar que el paso funcionó.

No uses colores como único medio para transmitir información: conserva siempre el texto de la etiqueta.

## 6. Estilo de redacción

Escribe la guía pensando en alguien que conoce lo básico de Windows y PowerShell, pero que nunca ha utilizado este framework.

Quiero una documentación:

- Muy sencilla.
- Paso a paso.
- Con lenguaje cotidiano.
- Sin explicaciones académicas largas.
- Sin exceso de jerga técnica.
- Con comandos listos para copiar y pegar.
- Con ejemplos concretos.
- Sin saltarse pasos por considerarlos obvios.
- Sin enviar al lector a cinco documentos distintos para completar una tarea.

Evita frases vagas como:

"Configura adecuadamente tu entorno".

En su lugar, indica exactamente qué archivo abrir, qué valor configurar, desde dónde ejecutar el comando y cómo comprobar el resultado.

Distingue claramente cuándo un comando se ejecuta en la carpeta del framework y cuándo en la carpeta del proyecto nuevo.

## 7. Restricciones

El objetivo es DOCUMENTAR, no desarrollar.

Por tanto:

- Crear o editar únicamente START.md.
- No modificar código funcional.
- No modificar configuraciones existentes.
- No modificar README.md, GUIDE.md, SETUP.md ni ARCHITECTURE.md.
- No agregar dependencias.
- No crear scripts auxiliares.
- No crear proyectos de prueba.
- No iniciar agentes ni servidores reales para probar la guía.
- No crear commits.
- No hacer push ni merge.
- No eliminar archivos.
- No volver a ejecutar suites completas de pruebas.
- No crear fases nuevas de desarrollo.

Conservar el estado actual del repositorio y las exclusiones de Git.

## 8. Validación de la documentación

Antes de terminar:

1. Comprueba que todos los comandos documentados existen en el código o herramientas disponibles.
2. Comprueba que las rutas y nombres de archivos sean correctos.
3. Comprueba que el orden de arranque sea coherente.
4. Comprueba que la guía cubre el escenario de carpeta nueva completamente vacía.
5. Comprueba que queda claro qué se hace una sola vez, cada día y por proyecto.
6. Comprueba que el procedimiento no requiere ejecutar comandos destructivos.
7. Comprueba que no se documentan funciones inexistentes.
8. Comprueba que otro usuario podría seguir START.md sin tener que leer primero ARCHITECTURE.md.

Si algún paso no puede verificarse con el código y la documentación actual, señala explícitamente la incertidumbre en START.md. No inventes una solución.

## 9. Entregable

Crear:

`START.md`

Al terminar, informa brevemente:

1. Archivo creado.
2. Secciones incluidas.
3. Componentes cuyo procedimiento de arranque fue verificado.
4. Procedimiento encontrado para inicializar una carpeta vacía.
5. Limitaciones reales identificadas.
6. Confirmación de que no se modificó ningún otro archivo.

No implementes cambios adicionales.

**Resultado esperado: quiero abrir START.md y saber exactamente qué hacer desde que enciendo mi computadora hasta que tengo el orquestador funcionando y un nuevo proyecto listo para trabajar con agentes.**