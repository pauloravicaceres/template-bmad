# ibk-apolo-plugin

> Plugin organizacional para definición de producto: guía el ciclo de vida de iniciativas en Initiative Specification, Solution Design Package y Delivery Plan, con orquestación y handoff entre artefactos y sistemas externos REST.

| | |
|---|---|
| **Tipo** | Plugin organizacional |
| **Estado** | borrador |
| **Propietario** | ai-delivery |
| **Versión** | 0.1.0 |
| **Audiencia** | business-analysts, product-owners, ste-engineers |
| **Punto de entrada** | `@ibk-apolo-orchestrator` |

## 🎯 Alcance
| **Incluye ✅** | Definición de iniciativas · diseño de Initiative Specification/Solution Design Package · validación de handoff · planificación de Jira/Xray · análisis de repos/GitHub/Figma |
| **No incluye ❌** | Implementación funcional de backend/frontend · acceso MCP · cambios de código fuente del repo de trabajo |

## Cuándo usarlo
- ✅ Cuando una iniciativa necesita estructurar la definición, el diseño y el paso a desarrollo.
- ✅ Cuando un equipo necesita convertir una Initiative Specification en un Solution Design Package sellado y luego en un desglose listo para Jira.
- ✅ Cuando hay que validar un handoff o completar un flujo de definición de producto con GitHub/Figma/Jira.

## Cuándo NO usarlo
- ❌ No usarlo para escribir código de negocio en un servicio técnico.
- ❌ No usarlo como reemplazo del análisis de arquitectura o implementación real del producto.

## Artefactos incluidos
### Agentes
| Agente | Propósito | Cuándo usarlo |
|---|---|---|
| `ibk-apolo-orchestrator` | Orquesta el flujo de tres etapas y delega a subagentes. | Iniciar o continuar una iniciativa y decidir la etapa correcta. |
| `ibk-apolo-business-analyst` | Genera y valida la Initiative Specification de una iniciativa. | Definición inicial con texto, CSV, transcripción o documentos. |
| `ibk-apolo-system-design-architect` | Enriquece la Initiative Specification y produce el Solution Design Package con diagramas y diseño. | Generar el paquete de Solution Design y validar si está listo. |
| `ibk-apolo-tech-delivery-planner` | Convierte el Solution Design Package en un desglose listo para Jira (Delivery Plan / Delivery Backlog). | Preparar Epic/HU/ET/HAB y cargar issues. |

### Habilidades (Skills)
| Habilidad | Propósito | Tipo | Riesgo |
|---|---|---|---|
| `ibk-apolo-document-extraction` | Extrae texto de PDFs/DOCX/PPTX para enriquecer la iniciativa. | Análisis | medio |
| `ibk-apolo-figma-api` | Consulta un archivo de Figma para extraer tokens/componentes. | Integración | medio |
| `ibk-apolo-figma-design-builder` | Genera diseño y artefactos Figma desde una especificación de diseño. | Integración | medio |
| `ibk-apolo-github-repo-context` | Lee repositorios GitHub o carpetas locales como base de conocimiento. | Contexto | bajo |
| `ibk-apolo-handoff-validator` | Valida contratos de handoff entre etapas. | Validación | bajo |
| `ibk-apolo-jira-cloud-api` | Interactúa con Jira Cloud REST para lectura/creación/actualización. | Integración | medio |
| `ibk-apolo-screen-yaml-skill` | Convierte tags de Adobe en un paquete YAML/MD para handoff. | Transformación | medio |

### Instrucciones / Prompts
| Artefacto | Propósito |
|---|---|
| `ibk-apolo-anti-hallucination-policy.instructions.md` | Regla de no invención de datos ni IDs no presentes, y de no declarar una escritura exitosa sin verificarla. |
| `ibk-apolo-business-analysis-standards.instructions.md` | Estándares de análisis y trazabilidad para BA/PO. |
| `ibk-apolo-governance-compliance.instructions.md` | Reglas de conformidad del plugin con la gobernanza del repositorio. |
| `ibk-apolo-hu-template.instructions.md` | Plantilla estándar para historias de usuario en el Delivery Plan. |
| `ibk-apolo-jira-configure.prompt.md` | Configura la sesión de Jira para el Delivery Plan. |
| `ibk-apolo-jira-create-hu.prompt.md` | Crea HUs, subtareas y ETs en Jira. |
| `ibk-apolo-jira-read.prompt.md` | Lee issues y consultas JQL. |
| `ibk-apolo-jira-update-hu.prompt.md` | Actualiza issues existentes. |

## Requisitos previos
- Python 3 con dependencias del plugin instaladas.
- Variables de entorno para Jira/Figma/GitHub según el flujo a ejecutar.
- Repositorio o carpeta base de conocimiento cuando Initiative Specification/Solution Design Package requieren contexto técnico.

## Uso rápido
```text
@ibk-apolo-orchestrator iniciar iniciativa para definir una nueva propuesta
@ibk-apolo-business-analyst preparar Initiative Specification desde documento o CSV
@ibk-apolo-system-design-architect convertir Initiative Specification a Solution Design Package sellado
@ibk-apolo-tech-delivery-planner preparar Delivery Plan y crear HU en Jira
```

## 📄 Detalle
→ [ARCHITECTURE.md](./ARCHITECTURE.md) · [GUIDE.md](./GUIDE.md)

## Mantenimiento
| Propietario | Estado | Versión | Creado | Próxima revisión |
|---|---|---|---|---|
| ai-delivery | borrador | 0.1.0 | 2026-08-31 | 2026-11-30 |
