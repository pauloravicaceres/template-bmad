# Preguntas Técnicas y Arquitectónicas para el Autor del Proyecto (BMAD + Herdr)

Este documento recopila las 20 preguntas técnicas de arquitectura, concurrencia, ingeniería de modelos (LLMOps), seguridad, observabilidad y resiliencia planteadas al autor del ecosistema multi-agente BMAD, junto con sus respuestas detalladas.

---

### 1. Arquitectura y Gestión de Estado

**Pregunta:** ¿Por qué decidiste utilizar un archivo Markdown (`tracker_bmad.md`) como gestor de estado y orquestación en lugar de una base de datos transaccional (como PostgreSQL) o un gestor de colas (como RabbitMQ)?

**Respuesta:**
Decidí usar un archivo Markdown porque mi prioridad era mantener la compatibilidad nativa con el Model Context Protocol (MCP) y asegurar la observabilidad humana. Un archivo de texto actúa como un *Event Sourcing* de solo adición (append-only log). Los agentes LLM son excelentes leyendo y analizando texto plano para extraer contexto; al usar Markdown, no necesito construir APIs intermedias para que consulten una base de datos. Además, al forzar la regla estricta de "leer, concatenar salto de línea y escribir", evito la sobrescritura del historial. Es una solución altamente desacoplada, ligera y auditable en tiempo real.

---

### 2. Concurrencia y Control de Tráfico

**Pregunta:** Al inyectar comandos directamente en las terminales (TTY), ¿cómo evitas las colisiones de búfer o *race conditions* si el orquestador envía una instrucción mientras el agente aún está procesando la anterior?

**Respuesta:**
Implementé un mecanismo de contrapresión (*backpressure*) directamente en el Watcher. El script no dispara las instrucciones a ciegas; primero consulta el panel de Herdr dinámicamente para leer el estado del agente (`idle` o `working`). Si el agente destinatario está ocupado, el Watcher retiene la instrucción en una variable de memoria RAM como "línea pendiente" y aborta la inyección. En el siguiente ciclo de sondeo, vuelve a intentarlo. Esto crea una cola asíncrona implícita que previene las colisiones en la terminal y permite que múltiples agentes (como el UX y el BA) trabajen en paralelo a distintos ritmos.

---

### 3. Ingeniería de IA y Comportamiento de Modelos

**Pregunta:** ¿Cómo lograste estabilizar el uso de herramientas (Tool Use) de los agentes? Es común que los LLMs rompan los formatos JSON o de texto cuando se les imponen reglas muy estrictas.

**Respuesta:**
Me enfrenté a un fenómeno que bauticé como "sangrado de instrucciones" (*instruction bleed*). Al principio, amenazaba a los agentes en el prompt diciéndoles que "la automatización fallaría" si usaban saltos de línea en sus entregables. El modelo entraba en un modo de sobre-precaución tan alto que eliminaba incluso el salto de línea (`\n`) que le pedía usar mecánicamente con la herramienta MCP, destruyendo el historial. Lo solucioné aplicando aislamiento de contexto: separé explícitamente las "reglas de redacción de texto" de las "instrucciones mecánicas de guardado". Al suavizar la amenaza técnica y delimitar las responsabilidades, los modelos empezaron a usar el `read_file` y `write_file` con precisión quirúrgica.

---

### 4. Tolerancia a Fallos y Sistemas Distribuidos

**Pregunta:** En una arquitectura distribuida sin estado (*stateless*), ¿cómo se recupera tu sistema de una "muerte silenciosa", por ejemplo, si el servidor se reinicia o si un agente se queda sin tokens en medio de una Épica?

**Respuesta:**
Resolví la "amnesia de tránsito" centralizando la lógica de reconciliación de estado en el Product Manager mediante una *Boot Sequence* (Secuencia de Arranque). Cuando el sistema se reinicia, el PM no se fía de su memoria volátil. Primero verifica si el archivo del Producto Mínimo Viable (`mvp.md`) ya existe. Si es así, lee el tracker completo y busca cuál fue la última Épica que recibió un estado de APROBADO por el QA Documental. Si el PM nota que envió la Épica 4 pero nunca hubo respuesta del QA, deduce que el proceso murió en tránsito y vuelve a disparar la instrucción para la Épica 4. Es un orquestador auto-reparable.

---

### 5. Ruteo y Desacoplamiento

**Pregunta:** ¿Cómo manejas el *Handoff* cuando un agente necesita detonar procesos en múltiples agentes a la vez sin que se contaminen los contextos?

**Respuesta:**
Desarrollé un ruteo dinámico de mensajes parcelados en el orquestador de Python. Cuando el QA Documental aprueba una Historia de Usuario, emite una sola línea en el tracker que contiene dos etiquetas, por ejemplo: `@UX: haz los wireframes. @PM: asigna la siguiente épica`. El Watcher parsea esa línea, identifica todas las etiquetas presentes y fragmenta el string. Al agente UX solo le inyecta su porción del texto, y al PM la suya. Esto evita que los agentes lean instrucciones que no les corresponden, reduciendo el consumo de tokens y evitando alucinaciones por contexto cruzado.

---

### 6. Escalabilidad (Scalability & Cuellos de Botella)

**Pregunta:** Tu sistema actual usa un script `watcher.py` leyendo un archivo de texto (`tracker_bmad.md`) en un bucle local. ¿Cómo escalarías esta arquitectura si necesitaras gestionar 50 agentes o procesar múltiples proyectos simultáneamente sin que la lectura/escritura del disco se convierta en un cuello de botella?

**Respuesta:**
Es cierto que usar el *file system* tiene un límite físico de IOPS. Concebí el `tracker_bmad.md` para la fase inicial porque me da visibilidad y trazabilidad inmediata. Para escalar horizontalmente, abstraería el tracker y lo reemplazaría por un *Message Broker* o un sistema *Pub/Sub* (como Redis Streams o Apache Kafka), manteniendo exactamente el mismo patrón de "append-only log" (registro de solo adición). Como mis agentes son agnósticos al sistema y solo usan herramientas de MCP (Model Context Protocol), bastaría con crear un servidor MCP personalizado que, en lugar de ejecutar `read/write` en el disco local, publique y consuma mensajes del broker. La lógica de contrapresión (*backpressure*) que ahora tengo en el Watcher pasaría a ser gestionada de forma natural por los *consumer groups* del broker.

---

### 7. Seguridad y Sandboxing

**Pregunta:** Mencionaste que tuviste que inyectar el flag `--add-dir` en la raíz del proyecto para que los agentes pudieran usar MCP y pasarse archivos entre sí. ¿No supone esto un riesgo de seguridad masivo, permitiendo que un agente modifique configuraciones del sistema o borre el trabajo de los demás?

**Respuesta:**
Completamente, es el trade-off clásico entre interoperabilidad y seguridad. Lo resolví aplicando el principio de mínimo privilegio (*Least Privilege*) a nivel de la ingeniería del prompt y de variables de entorno, delimitando qué carpetas (ej. `CARPETA_ENTRADA` y `CARPETA_SALIDA`) puede tocar cada agente. Sin embargo, a nivel de arquitectura dura, la solución para llevar esto a producción es implementar un "Proxy MCP". En lugar de darles acceso directo al sistema de archivos local, los agentes se conectarían a un servidor MCP intermedio configurado por mí. Este proxy interceptaría los comandos y aplicaría un Control de Acceso Basado en Roles (RBAC), validando, por ejemplo, que el "QA Documental" tenga permisos de solo lectura (`R`) sobre la carpeta del "Product Manager" y escritura (`W`) únicamente en su propia carpeta de reportes.

---

### 8. Observabilidad y Debugging Silencioso

**Pregunta:** Depurar pipelines de LLMs asíncronos suele ser una pesadilla porque fallan de manera impredecible. Si la cadena se rompe o un modelo empieza a alucinar datos, ¿cómo auditas la ejecución paso a paso sin un motor de *traces* tradicional (como LangSmith o Datadog)?

**Respuesta:**
Esa fue una de las razones principales para usar un enfoque basado en archivos e integrarlo con Git. Mi observabilidad se basa en dos pilares nativos. Primero, el `tracker_bmad.md` actúa como un log de eventos de negocio legible por humanos; con abrirlo sé al instante en qué fase estamos. Segundo, le inyecté al Watcher un mecanismo de *auto-commits*. Cada vez que un agente finaliza un entregable y el Watcher entrega la instrucción exitosamente, se dispara un `git commit` silencioso. Si descubro que un archivo tiene alucinaciones, simplemente hago un `git log` o `git diff` para aislar el momento exacto y el agente (autor del commit) que introdujo la falla, restauro el repositorio al estado previo, y obligo a ese agente a reprocesar. Es un control de estado nativo, sin *overhead* de plataformas externas.

---

### 9. Justificación del Model Context Protocol (MCP)

**Pregunta:** ¿Por qué utilizaste el estándar MCP para las acciones del sistema en lugar de usar flujos basados en llamadas a funciones (*Function Calling*) nativas de la API, o frameworks pesados como LangChain, AutoGen o CrewAI?

**Respuesta:**
Decidí usar MCP porque priorizo el desacoplamiento absoluto y evitar el *vendor lock-in* (dependencia del proveedor). Frameworks como CrewAI o LangChain introducen capas de abstracción muy pesadas que te atan a sus propias lógicas de ruteo. Al mantener a mis agentes como procesos puros en la CLI (Herdr) y utilizar MCP para sus "sentidos" (leer/escribir), traté al sistema de archivos como una API estandarizada. La ventaja es que si mañana quiero cambiar el "cerebro" del agente QA de un modelo de OpenAI a un modelo de Anthropic o Llama, solo cambio una variable de entorno. La forma en la que el agente interactúa con el mundo (MCP) se mantiene idéntica, sin tener que reescribir ni una sola línea del código de integración.

---

### 10. Mecánica del Human-in-the-Loop (HITL)

**Pregunta:** Has mencionado que el agente Business Storyteller (BS) tiene la capacidad de detener la automatización para realizar un *Discovery* interactivo contigo. ¿Cómo logras que esta pausa humana no bloquee el hilo principal del orquestador asíncrono y colapse el Watcher?

**Respuesta:**
Lo logro porque mi asincronía está basada en el sondeo pasivo de eventos (*polling*), no en hilos bloqueados (*blocking threads*). El Watcher reacciona única y exclusivamente cuando se detecta una nueva línea en el tracker. Cuando el BS identifica ambigüedad en mis ideas, no escribe la instrucción de delegación (`@PA:`) en el tracker; en su lugar, se queda interactuando conmigo directamente en su panel de la terminal. Durante ese tiempo, su estado en el sistema es `idle` o `working` procesando mis respuestas, pero como no ha inyectado el disparador en el archivo central, el Watcher lo ignora y sigue verificando si hay tráfico para el resto del equipo. Es un bloqueo lógico a nivel de negocio, no un bloqueo de recursos computacionales. Solo cuando le doy mi aprobación, el BS redacta el requerimiento, usa MCP para guardarlo y notifica al tracker, despertando al siguiente eslabón.

---

### 11. Condición de Carrera en el Gestor de Estado (Race Condition)

**Pregunta:** ¿Qué pasaría si, por ejemplo, el BA termina de escribir los Criterios de Aceptación y, exactamente en el mismo milisegundo, el BS termina de dialogar con el usuario y ambos intentan actualizar el `tracker_bmad.md` usando sus herramientas MCP? ¿No se sobrescribiría el archivo o se corrompería el historial al no tener un bloqueo de base de datos?

**Respuesta:**
Es un escenario clásico de condición de carrera. Como dependo del sistema de archivos local y el estándar MCP no implementa un bloqueo de escritura nativo (file lock) a nivel de SO, existe un riesgo marginal de colisión si la acción es literalmente simultánea. Sin embargo, mitigo este riesgo en la capa de orquestación. Los agentes de Agy no se ejecutan en paralelo absoluto frente al Watcher, sino que están desacoplados. Si llegara a ocurrir una colisión física que corrompa el formato del texto, mi mecanismo de trazabilidad continua actúa como red de seguridad. Como el Watcher hace un `git commit` silencioso por cada instrucción exitosa, si noto una corrupción visual en el tracker, simplemente detengo el script, hago un `git restore` al commit anterior (que ocurrió segundos antes) y dejo que el PM ejecute su secuencia de recuperación para reasignar las tareas faltantes. Para escalar a un entorno empresarial, reemplazaría el archivo físico por un motor Pub/Sub (como Redis o Kafka) que serialice los eventos de forma nativa.

---

### 12. El Bucle Infinito por Alucinación (Ping-Pong de Agentes)

**Pregunta:** Imagina que el BA y el QA entran en un bucle infinito. El BA genera una historia con una inconsistencia lógica, el QA la audita, la rechaza y le pide corregirla. Pero el LLM del BA "alucina", no logra procesar bien el feedback y vuelve a guardar la misma historia errónea. El QA la vuelve a rechazar, y así eternamente. ¿Cómo evitas que este bucle consuma todos tus tokens en cuestión de minutos?

**Respuesta:**
Me anticipé a los bucles infinitos por alucinación diseñando el sistema para soportar intervención humana en caliente (Human-in-the-Loop dinámico). Si mi orquestador estuviera "hardcodeado" con LangChain o CrewAI, detener un bucle interno sería un dolor de cabeza. Pero como mis agentes operan directamente en terminales independientes de Herdr, yo tengo control total sobre la TTY. Si veo en el tracker un patrón repetitivo de "Rechazado -> Corregido -> Rechazado", simplemente cancelo el Watcher temporalmente, entro a la terminal del BA y le inyecto contexto manualmente: *"Detente. El error que no logras corregir es X. Modifica la regla de negocio de esta forma exacta"*. Una vez que el BA procesa mi *prompt* y guarda el archivo correctamente con MCP, reactivo el Watcher y la automatización sigue su curso natural.

---

### 13. Falla de Herramientas y Corrupción de Entorno

**Pregunta:** Digamos que por error humano modificas el `config_bmad.json` para cambiar una carpeta y rompes la sintaxis (olvidas una coma). El agente PM es invocado, intenta usar `read_file` sobre el JSON, pero la herramienta falla o devuelve un string corrupto. ¿Qué impide que el LLM intente "adivinar" las rutas, se invente un alcance de producto y rompa la cadena enviándole basura al BA?

**Respuesta:**
La prevención de fallas en cascada la manejo directamente mediante lo que llamo el "Protocolo de Seguridad (Fallback)" en la ingeniería del prompt principal (System Prompt) de cada agente. Les he inyectado una regla restrictiva explícita: si la herramienta MCP falla, no pueden acceder al directorio, o el archivo no existe, tienen **absolutamente prohibido** intentar deducir variables, inventar alcance o continuar con el flujo lógico. Su única vía de acción permitida es detener el análisis inmediatamente e imprimir un reporte de error en su panel, pidiendo al humano que introduzca los datos crudos en el chat. Esto garantiza que un error técnico de infraestructura resulte en un *fail-safe* (parada segura) y nunca en una alucinación que propague datos inválidos hacia el resto del pipeline.

---

### 14. Falsos Positivos en el Ruteo Dinámico

**Pregunta:** Ahora que tu Watcher puede fragmentar mensajes múltiples (ej. el QA despertando al UX y al PM), ¿qué pasaría si un agente decide ser "conversacional" en el tracker? Por ejemplo, si el PM escribe: *"@BA: Empieza la Épica 2. Y por cierto, avísale al @UX: que los colores los defina después"*. Tu función `extraer_instruccion` parsearía el `@UX` y le inyectaría un fragmento roto al diseñador. ¿Cómo previenes esto?

**Respuesta:**
Esa es una vulnerabilidad lógica real del parseo de texto plano, y la resolví controlando el comportamiento determinista de las salidas (Prompting de Formato Estricto). No le permito a los agentes ser conversacionales al momento de usar la herramienta de escritura en el tracker. Las instrucciones de "ORDEN DE DELEGACIÓN" en sus prompts no son sugerencias, son plantillas de texto rígidas. Les indico exactamente que deben copiar y pegar el texto de la plantilla reemplazando solo los corchetes, prohibiéndoles agregar saludos, notas extra o referencias a etiquetas de otros agentes fuera del guion. Al forzar este comportamiento mecánico en el uso del MCP, el *payload* de texto que el Watcher lee y fragmenta siempre viene limpio y predecible, erradicando los falsos positivos en el enrutamiento.

---

### 15. Pruebas de Estrés en un Entorno TTY

**Pregunta:** ¿Cómo realizas pruebas de estrés en este ecosistema? Las herramientas tradicionales como JMeter o Gatling están diseñadas para inundar endpoints HTTP, pero tu arquitectura funciona inyectando comandos en terminales y leyendo un archivo Markdown.

**Respuesta:**
Exacto, no puedo usar un *load tester* HTTP tradicional. Mi estrategia de estrés se enfoca en saturar la cola asíncrona del Watcher y llevar al límite las cuotas de la API del LLM. Para lograrlo, creé un script de automatización que inyecta artificialmente ráfagas de líneas en el `tracker_bmad.md` de forma simultánea. Por ejemplo, simulo que 20 agentes QA acaban de aprobar 20 Historias de Usuario al mismo tiempo, escribiendo 20 líneas con doble etiqueta (`@UX:` y `@PM:`).

Lo que mido aquí no es el tiempo de respuesta del servidor (latencia de red), sino cómo la lista `cola_tareas` de mi `watcher_bmad.py` crece y retiene las 40 tareas pendientes aplicando *backpressure*. Monitoreo que el Watcher no colapse por operaciones de lectura/escritura en el disco, y observo cómo los agentes despachan el trabajo a medida que pasan de `working` a `idle`. El verdadero cuello de botella que busco estresar no es mi hardware local, sino el límite de Tokens por Minuto (TPM) y Peticiones por Minuto (RPM) del proveedor del LLM.

---

### 16. Ingeniería de Pruebas Negativas (Chaos Engineering para QA)

**Pregunta:** ¿Cómo creas casos de prueba efectivos para garantizar que tu agente QA Documental realmente cumpla su función y rechace una Historia de Usuario (HU), en lugar de aprobar todo ciegamente por sesgo de complacencia (sycophancy)?

**Respuesta:**
Para asegurar que el QA es una barrera implacable y no un simple sello de goma, aplico técnicas de inyección de fallos o *prompt poisoning* en los entregables intermedios. Genero archivos `hu_*.md` corrompidos intencionalmente antes de despertar al QA, atacando los tres vectores exactos que le programé para auditar:

1. **Alucinación de Alcance (Scope Creep):** Modifico la HU para incluir un requerimiento que jamás existió en el Product Brief original. Por ejemplo, si el producto era solo una pasarela web, le agrego al BA un criterio de aceptación sobre "notificaciones push en iOS".
2. **Amputación de Casos Límite (Sad Paths):** Tomo una historia perfecta y le borro deliberadamente los escenarios Gherkin que manejan errores (como fallos de red, timeouts o tarjetas rechazadas), dejando solo el *Happy Path*.
3. **Contradicción Lógica:** Introduzco una regla de negocio que choca matemáticamente con los Criterios de Aceptación (ej. Regla: "El monto máximo es $50", Gherkin: "Dado que el usuario intenta transferir $100... el sistema lo permite").

Una vez que guardo estos archivos trampa, inyecto manualmente la etiqueta `@QA:` en el tracker. Mi prueba es exitosa únicamente si el QA detecta la trampa específica, genera la ramificación `[ESTADO: RECHAZADO]`, elabora el reporte de observaciones precisas y devuelve la tarea al `@BA:` para su corrección. Es la única forma de calibrar la severidad de su auditoría.

---

### 17. Prevención de Pérdida de Tareas (El "Asesinato" de la Memoria)

**Pregunta:** El problema de pérdida de tareas en tránsito al que se llama "asesinato de la memoria". ¿Por qué ocurría exactamente esta fuga de información en el orquestador y cómo lograste controlarla para garantizar la entrega?

**Respuesta:**
Ocurría por una limitación en el diseño inicial del ciclo de lectura de mi orquestador. Al principio, el Watcher solo memorizaba la "última línea" del tracker en una única variable (`linea_pendiente`). Cuando el QA detonaba un Handoff múltiple (ej. una tarea para el UX y otra para el PM), el Watcher veía que el UX estaba ocupado y retenía su tarea, pero le entregaba la orden al PM (que estaba libre). El problema era que el PM procesaba su orden tan rápido que escribía una nueva línea en el tracker casi de inmediato. Mi script leía esa nueva línea y sobrescribía la variable en memoria, "asesinando" para siempre la tarea que el UX tenía pendiente, deteniendo toda la producción.

Lo controlé refactorizando el motor del Watcher: migré de una variable de estado simple a una Cola de Tareas asíncrona (FIFO Queue). Ahora, el orquestador lee todas las líneas nuevas desde su última revisión, extrae cada instrucción por separado, les asigna un hash único (para evitar duplicados) y las apila en una lista (`cola_tareas`). Durante el ciclo de *backpressure*, las tareas solo se eliminan de esta lista si la inyección al panel del agente es exitosa. Si el UX está trabajando durante horas, su tarea sobrevivirá intacta en la memoria RAM del Watcher, sin importar cuántas decenas de líneas nuevas escriban los demás agentes en el archivo.

---

### 18. Condición de Carrera de Doble Despacho (Double Dispatch Race Condition)

**Pregunta:** ¿Tuviste el caso de Condición de Carrera de Doble Despacho (Double Dispatch Race Condition) y cómo lo resolviste?

**Respuesta:**
¡Sí, fue uno de los bugs de concurrencia más fascinantes que enfrenté! Me ocurrió cuando había un cuello de botella y la cola de tareas acumulaba múltiples requerimientos para un mismo agente. Por ejemplo, el equipo avanzó tan rápido que las Épicas 4 y 5 ya estaban aprobadas por el QA y encoladas en el Watcher, esperando a que el UX terminara de diseñar la Épica 3.

El problema estalló en el milisegundo exacto en que el UX terminó su tarea y pasó a estado `idle`. Mi orquestador iteró sobre la cola: vio la Épica 4, verificó que el UX estaba libre, y se la inyectó. Pero como el bucle `for` de Python se ejecuta en microsegundos, inmediatamente evaluó la Épica 5. El fallo ocurrió porque el backend del panel (Herdr) tarda alrededor de 1 o 2 segundos en refrescar el estado del agente de `idle` a `working`. Al consultarlo tan rápido, el sistema le devolvió al Watcher un falso positivo de `idle`, provocando que inyectara la Épica 5 aplastando a la Épica 4 en la misma terminal. Como el orquestador creyó que entregó ambas con éxito, las borró de la RAM y ambas se perdieron en el limbo.

Lo resolví implementando un "Candado de Ciclo" (*Cycle Lock*). Modifiqué el Watcher para que, en cada ciclo de revisión, lleve un registro temporal de a quién le ha disparado (un set llamado `agentes_despachados_hoy`). Ahora, si el Watcher le entrega la Épica 4 al UX, lo añade a esa lista de exclusión inmediata. Cuando el bucle evalúa la Épica 5 una fracción de segundo después, el candado se activa y obliga a retener esa tarea en la cola, saltándose la inyección. Esto le da al entorno el "respiro" necesario para que el agente cambie su estado a `working` de manera oficial, garantizando que los mensajes se procesen estrictamente de uno en uno sin saturar el búfer de entrada.

---

### 19. Latencia de Transición y Parpadeo de Estado (State Flapping)

**Pregunta:** ¿Por qué un agente no empieza a procesar inmediatamente después de que su agente predecesor termina su tarea?

**Respuesta:**
La razón principal es la gestión de la asincronía y el fenómeno conocido como **Parpadeo de Estado** (*State Flapping*). Cuando un agente (por ejemplo, el Diseñador UX) está trabajando intensamente, realiza pausas breves entre el uso de diferentes herramientas (como leer o escribir archivos con MCP). En esos microsegundos de pausa analítica, la API del entorno (Herdr) puede reportar erróneamente al orquestador que el agente se encuentra libre (`idle`) cuando en realidad sigue ocupado procesando la tarea.

Si el Watcher disparara una nueva instrucción en ese exacto instante de "parpadeo", interceptaría al agente a mitad de su trabajo, rompiendo su contexto y sobrescribiendo su búfer de terminal. Para prevenirlo, el orquestador desacopla la velocidad: aunque la tarea predecesora termine y se encole de inmediato, el Watcher actúa con contrapresión, esperando a que el agente demuestre un estado `idle` real y sostenido antes de inyectarle el siguiente requerimiento, garantizando una transición limpia y segura sin colisiones de búfer.

---

### 20. Autonomía y Orquestación Descentralizada

**Pregunta:** ¿Cómo hiciste para que todos los agentes trabajen de manera autónoma y orquestada?

**Respuesta:**
Construí un modelo de orquestación asíncrona basado en eventos, fusionando un archivo de texto plano (`tracker_bmad.md`) como nuestro "bus de mensajes" central y un script demonio en Python (`watcher_bmad.py`) como director de orquesta.

El diseño se basa en la reactividad. Cada agente opera aislado en su propio panel de terminal (Herdr) enfocado en una tarea atómica. Cuando un agente termina su trabajo, utiliza el Model Context Protocol (MCP) para guardar su entregable en disco y anexa una orden de delegación estructurada (por ejemplo, `@UX: procede con los wireframes`) al final del tracker.

La autonomía real ocurre gracias al Watcher. Este orquestador lee las nuevas líneas del tracker, fragmenta las órdenes y las apila en una cola interna (FIFO Queue). Luego, sondea en tiempo real el estado de cada agente; si el destinatario está libre (`idle`), inyecta la instrucción directamente en el búfer de su terminal usando comandos TTY (`herdr pane run`), despertándolo. De esta manera, el cierre documentado de un agente se convierte automática e instantáneamente en el *prompt* de inicio del siguiente, logrando una cadena de producción de software paralela, desatendida y capaz de regular su propio tráfico sin colisionar.
