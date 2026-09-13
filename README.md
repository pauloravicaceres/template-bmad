
# Manual de Uso: Ecosistema Multi-Agente BMAD con Herdr

Este repositorio contiene la configuración y la guía detallada para ejecutar un flujo de desarrollo de software totalmente autónomo basado en la metodología **BMAD (Business, Management, Architecture, Development)**. El ecosistema integra orquestación en terminal mediante **Herdr**, automatización mediante un _Watcher_ en Python y gestión de archivos físicos distribuidos vía herramientas MCP.

## 📁 1. Estructura del Proyecto

El ecosistema requiere una jerarquía de carpetas estandarizada en la raíz de tu proyecto para separar la configuración, la memoria de los agentes y los archivos físicos. Asegúrate de contar con la siguiente estructura base:

Plaintext

```
/tu-proyecto-raiz/
├── agents/               # Directorios de entorno virtual para los paneles de Herdr
├── files/                # Sistema de almacenamiento de salidas y estado
│   ├── business-storyteller/ # Salida de Idea de Usuario Refinada
│   ├── product-analyst/  # Salida de Products Briefs
│   ├── product-manager/  # Salida de Backlogs y MVPs
│   ├── business-analyst/ # Salida de Historias de Usuario (HU)
│   ├── qa-documental/    # Salida de reportes de auditoría y feedback
│   ├── designer-ux/      # Salida de wireframes y enlaces UI
│   └── tracker_bmad.md   # Bus de mensajes unificado para el handoff entre agentes
├── prompts/              # System Prompts de cada agente
│   ├── bs.md             # System Prompt del Business Storyteller
│   ├── pa.md             # System Prompt del Product Analyst
│   ├── pm.md             # System Prompt del Project Manager
│   ├── ba.md             # System Prompt del Business Analyst
│   ├── qa.md             # System Prompt del QA Documental
│   └── ux.md             # System Prompt del Diseñador UX
├── config_bmad.json      # Diccionario de rutas absolutas para las herramientas MCP
└── watcher_bmad.py       # Script orquestador (Bucle infinito + Candado OS)
```

_(Nota: Las subcarpetas dentro de `files/` corresponden a las áreas de trabajo de cada rol)._

## 🚀 2. Configuración y Arranque Inicial

La arquitectura mantiene a todos los agentes vivos en memoria, permitiendo que el orquestador enrute los mensajes de forma autónoma.

### Paso 1: Levantar los Paneles de Herdr (Inicialización en frío)

Debes crear los espacios de trabajo e inicializar a los 6 agentes en sus respectivos paneles para que estén listos para escuchar comandos. Ejecuta esto en tu terminal (adaptando el comando según tu CLI):

PowerShell

```
# 1. Business Storyteller
New-Item -ItemType Directory -Force .\agents\business-storyteller
Copy-Item ".\prompts\bs.md" .\agents\business-storyteller\AGENTS.md
herdr pane split --current --direction right --cwd .\agents\business-storyteller
herdr agent start business-storyteller --kind agy --pane wF:p1 -- --add-dir ..\..

# 2. Product Analyst
New-Item -ItemType Directory -Force .\agents\product-analyst
Copy-Item ".\prompts\pa.md" .\agents\product-analyst\AGENTS.md
herdr pane split --current --direction down --cwd .\agents\product-analyst
herdr agent start product-analyst --kind agy --pane wF:p3 -- --add-dir ..\..

# Repite el proceso
herdr agent start product-manager --kind agy --pane wF:p4 -- --add-dir "D:\Paulo\Cursos\DMC\template-bmad"
herdr agent start business-analyst --kind agy --pane wF:p2 -- --add-dir "D:\Paulo\Cursos\DMC\template-bmad"
herdr agent start qa-documental --kind agy --pane wF:p5 -- --add-dir "D:\Paulo\Cursos\DMC\template-bmad"
herdr agent start designer-ux --kind agy --pane wF:p6 -- --add-dir "D:\Paulo\Cursos\DMC\template-bmad"
```

### Paso 2: Activar el Motor de Automatización (Watcher)

Abre una nueva pestaña en tu terminal (fuera de los paneles de los agentes) e inicia el script de Python. El script aplicará el candado del sistema operativo y quedará a la espera:

Bash

```
python watcher_bmad.py
```

## 🛠️ 3. Modalidad de Ejecución Independiente y Desacople (Fase Business)

No es obligatorio que los agentes **Business Storyteller (BS)** y **Product Analyst (PA)** operen estrictamente dentro del flujo encadenado. Si deseas utilizarlos como herramientas independientes para refinar ideas o redactar _Product Briefs_ puntuales sin que el orquestador intervenga, debes retirarlos del alcance del script de Python.

### Desacople en el Watcher

Para evitar que el Watcher procese a estos agentes automáticamente, edita el archivo `watcher_bmad.py` y comenta (o elimina) las líneas correspondientes a `@BS:` y `@PA:` dentro del diccionario `agentes` en la función `procesar_tracker`:

Python

```
def procesar_tracker(ultima_linea):
    linea = ultima_linea.strip()
    
    # Mapeo de las etiquetas con el ID exacto del agente en Herdr
    agentes = {
        # "@BS:": "business-storyteller",   # COMENTADO: Fuera del flujo automático
        # "@PA:": "product-analyst",        # COMENTADO: Fuera del flujo automático
        "@PM:": "product-manager",  # Almacena el product backlog y las instrucciones
        "@BA:": "business-analyst",  # Almancena las historias de usuario
        "@QA:": "qa-documental",    # Almacena las historias de usuario aprobadas
        "@UX:": "designer-ux"   # Almacena las propuestas de diseño
    }
# ... (resto del script sin alteraciones)
```

### Ejecución Manual de Agentes Independientes

Con los agentes desacoplados, puedes ejecutarlos a voluntad utilizando cualquiera de estos tres métodos directamente en tu terminal:

**Opción A: Ingresando el texto en el chat (Uso de etiquetas XML)** Envía el texto crudo encapsulado en sus etiquetas correspondientes directamente por la CLI:

Bash

```
herdr agent prompt product-analyst "<idea_usuario>Necesito un bot de WhatsApp para mi veterinaria, solo para consultas, no urgencias.</idea_usuario>"
```

**Opción B: Ingresando el nombre del archivo generado** Si ya generaste un archivo markdown con el insumo en la carpeta correspondiente, puedes despertar al agente pasándole solo el nombre del archivo. El agente usará el `config_bmad.json` para extraer el contenido:

Bash

```
herdr agent prompt product-analyst "idea_veterinaria.md"
```

**Opción C: Actualizando manualmente el tracker_bmad.md** Si mantuviste al PA dentro del Watcher pero decidiste no usar al BS, puedes disparar el flujo autónomo a partir del Product Analyst abriendo tu archivo `files/tracker_bmad.md` y escribiendo manualmente:

Markdown

```
@PA: La idea de usuario está lista en el archivo idea_veterinaria.md. Procede con la creación del PRODUCT BRIEF.
```

## 🔄 4. Flujo de Trabajo Autónomo (Guía End-to-End)

Si decides mantener a los 6 agentes en el diccionario del `watcher_bmad.py`, el proceso completo de definición de software se ejecuta en cadena.

### Fase 1: Disparo Inicial (Ingreso de la Idea Cruda)

Interactúas directamente con el **Business Storyteller (BS)** entregándole la idea de negocio informal a través de un prompt en su panel:

Bash

```
herdr agent prompt business-storyteller "Quiero un bot de WhatsApp para mi veterinaria 'Patitas'. La gente llama mucho para sacar citas y a veces no contestamos..."
```

_A partir de este punto, el sistema opera sin intervención humana._

### Fase 2: Refinamiento y Product Brief (Fase Business)

1. **El Business Storyteller (BS):** Optimiza la idea cruda inyectando el dolor de negocio y agrupando actores. Guarda el archivo `idea_veterinaria.md` y actualiza automáticamente el Tracker escribiendo `@PA: La idea de usuario está lista...`.
    
2. **El Product Analyst (PA):** El Watcher detecta la línea, despierta al PA. Este lee la idea optimizada, estructura el **Product Brief (PRD)**, guarda su archivo `pb_veterinaria.md` y actualiza el Tracker escribiendo `@PM: El Product Brief está listo...`.
    

### Fase 3: Orquestación y Análisis (Fase Management)

1. **El Project Manager (PM):** Despertado por el Watcher, lee el Product Brief, redacta la visión estratégica y prioriza el **Backlog del MVP**. Guarda el documento y delega el trabajo en el Tracker (`@BA: Desglosa la Épica 1...`).
    
2. **El Business Analyst (BA):** Lee el MVP y el PB, redacta la **Historia de Usuario** atómica utilizando sintaxis Gherkin (BDD), guarda la especificación y solicita la auditoría (`@QA: La historia está lista...`).
    

### Fase 4: Auditoría y Auto-Corrección (QA)

El agente **QA Documental** cruza la Historia de Usuario contra el Product Brief original. Ocurre una bifurcación lógica:

- **Ruta de Rechazo (Bucle Autónomo):** Si detecta flujos alternativos faltantes (_Sad Paths_), genera un reporte de _feedback_ y devuelve la tarea (`@BA: La historia fue RECHAZADA...`). El Watcher despierta al BA, quien corrige el documento y vuelve a invocar al QA.
    
- **Ruta de Aprobación:** Si la historia es hermética, el QA genera el certificado y despierta al siguiente eslabón (`@UX: Historia aprobada...`).
    

### Fase 5: Traducción Visual (UX)

El **Designer UX** lee la historia aprobada, se conecta al servidor MCP de Stitch para inicializar el proyecto y generar los estados visuales (wireframes) correspondientes a cada escenario Gherkin. Guarda su reporte y notifica al área técnica (`@ARQ: Wireframes listos...`).

## 📊 5. Diagramas de Arquitectura y Secuencia

A continuación se detalla la topología física y el flujo asíncrono del sistema.

### Arquitectura Física y Lógica (Ecosistema BMAD)

```mermaid
flowchart TB
    subgraph Motor_Automatizacion [Motor Central de Orquestación]
        W["watcher_bmad.py<br><i>Bucle infinito + Candado OS</i>"]
        T[("tracker_bmad.md<br><i>Bus de Mensajes / Handoff</i>")]
        W -- "Monitorea (getmtime)" --> T
    end

    subgraph Config_Global [Enrutamiento Dinámico]
        JSON{"config_bmad.json<br><i>Diccionario de Rutas</i>"}
    end

    subgraph Entorno_Herdr [Agentes BMAD - Cadena Completa]
        direction LR
        BS("Business Storyteller<br><i>Optimizador de Ideas</i>")
        PA("Product Analyst<br><i>Definición PB</i>")
        PM("Product Manager<br><i>Agente Orquestador</i>")
        BA("Business Analyst<br><i>Agente Ejecutor</i>")
        QA("QA Documental<br><i>Agente Evaluador</i>")
        UX("Designer UX<br><i>Traductor Visual</i>")
    end

    subgraph Servidores_MCP [Herramientas de Sistema]
        MCP_FS[["MCP Filesystem<br><i>read_file / write_file</i>"]]
        MCP_ST[["MCP Stitch<br><i>Generador de UI</i>"]]
    end

    subgraph Sistema_Archivos [Carpetas Locales / Output]
        DIR_BS["📁 business-storyteller<br><i>(Ideas Refinadas)</i>"]
        DIR_PA["📁 product-analyst<br><i>(Product Briefs)</i>"]
        DIR_PM["📁 product-manager<br><i>(Backlogs/MVPs)</i>"]
        DIR_BA["📁 business-analyst<br><i>(Historias de Usuario)</i>"]
        DIR_QA["📁 qa-documental<br><i>(Feedback/Aprobaciones)</i>"]
        DIR_UX["📁 designer-ux<br><i>(Wireframes y UI)</i>"]
    end

    %% Relaciones del Motor a los Agentes
    T -- "Dispara comando CLI" --> PA
    T -- "Dispara comando CLI" --> PM
    T -- "Dispara comando CLI" --> BA
    T -- "Dispara comando CLI" --> QA
    T -- "Dispara comando CLI" --> UX

    %% Relaciones de Agentes con MCP y JSON
    BS & PA & PM & BA & QA & UX -. "Lee rutas" .-> JSON
    BS & PA & PM & BA & QA & UX === MCP_FS
    UX === MCP_ST

    %% Relaciones de MCP con el Sistema de Archivos
    MCP_FS --> DIR_BS
    MCP_FS --> DIR_PA
    MCP_FS --> DIR_PM
    MCP_FS --> DIR_BA
    MCP_FS --> DIR_QA
    MCP_FS --> DIR_UX
    MCP_FS -- "Actualiza Handoff" --> T
```

---

### Flujo de Trabajo (Secuencia Asíncrona)

```mermaid
%%{init: {
  'theme': 'base',
  'themeVariables': {
    'actorBkg': '#45818E',
    'actorBorder': '#76A5AF',
    'actorTextColor': '#000000',
    'actorLineColor': '#64748B',
    'participantBkg': '#334155',
    'participantBorder': '#475569',
    'participantTextColor': '#FFFFFF',
    'noteBkgColor': '#0F172A',
    'noteBorderColor': '#3B82F6',
    'noteTextColor': '#E2E8F0',
    'activationBkgColor': '#7F6000',
    'activationBorderColor': '#BF9000'
  }
}}%%
sequenceDiagram
    autonumber
    actor Usuario
    participant W as Watcher (Python)
    participant T as tracker_bmad.md
    participant C as config_bmad.json
    participant BS as Business Storyteller
    participant PA as Product Analyst
    participant PM as Product Manager
    participant BA as Business Analyst
    participant QA as QA Documental
    participant UX as Designer UX

    Note over W, T: El Watcher está encendido esperando<br>modificaciones en el Tracker.
    
    Usuario->>BS: Prompt en CLI: "Idea de negocio cruda"
    activate BS
    BS->>C: read_file (Busca ruta de salida)
    BS->>BS: Optimiza idea (Pain Points, Actores)
    BS->>C: write_file (Guarda idea_[nombre].md)
    BS->>T: write_file (Escribe "@PA: La idea de usuario está lista...")
    deactivate BS

    W->>T: Detecta cambio y lee última línea
    W->>PA: herdr agent prompt product-analyst "[Instrucción del BS]"
    
    activate PA
    PA->>C: read_file (Busca rutas)
    PA->>PA: Genera Product Brief estructurado
    PA->>C: write_file (Guarda pb_[nombre].md)
    PA->>T: write_file (Escribe "@PM: El Product Brief está listo...")
    deactivate PA

    W->>T: Detecta cambio y lee última línea
    W->>PM: herdr agent prompt project-manager "[Instrucción del PA]"
    
    activate PM
    PM->>C: read_file (Busca rutas)
    PM->>PM: Define MVP y Backlog de Épicas
    PM->>C: write_file (Guarda mvp_[nombre].md)
    PM->>T: write_file (Escribe "@BA: Desglosa la Épica P1...")
    deactivate PM

    W->>T: Detecta cambio y lee última línea
    W->>BA: herdr agent prompt business-analyst "[Instrucción del PM/QA]"
    
    activate BA
    BA->>C: read_file (Busca rutas PB y MVP)
    BA->>BA: Redacta Historia de Usuario y Gherkin
    BA->>C: write_file (Guarda hu_[nombre].md)
    BA->>T: write_file (Escribe "@QA: La HU está lista para auditar...")
    deactivate BA

    W->>T: Detecta cambio y lee última línea
    W->>QA: herdr agent prompt qa-documental "[Instrucción del BA]"
    
    activate QA
    QA->>C: read_file (Busca rutas PB y HU)
    QA->>QA: Audita Trazabilidad y Casos Límite
    
    alt OPCIÓN A: Rechazo
        QA->>C: write_file (Guarda feedback_qa_[nombre].md)
        QA->>T: write_file (Escribe "@BA: HU rechazada...")
        W->>BA: Inicia bucle de<br>auto-corrección
    else OPCIÓN B: Aprobación
        QA->>C: write_file (Guarda aprobado_qa_[nombre].md)
        QA->>T: write_file (Escribe "@UX: HU aprobada...")
    end
    deactivate QA

    W->>T: Detecta cambio y lee última línea
    W->>UX: herdr agent prompt designer-ux "[Instrucción del QA]"
    
    activate UX
    UX->>C: read_file (Busca ruta de HU Aprobada)
    UX->>UX: Llama al servidor Stitch (Wireframes UI)
    UX->>C: write_file (Guarda ux_[nombre].md)
    UX->>T: write_file (Escribe "@ARQ: Wireframes listos...")
    deactivate UX
```