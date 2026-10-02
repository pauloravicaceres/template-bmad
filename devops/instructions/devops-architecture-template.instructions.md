---
description: 'Plantilla maestra para la generación y mantenimiento de la arquitectura de operaciones y pipeline.'
---

# 🏗️ PLANTILLA MAESTRA: ARQUITECTURA DEVOPS Y PIPELINE VIVO (`devops-architecture.md`)

## 🎯 OBJETIVO Y REGLA CRÍTICA DE RENDERIZADO SELECTIVO
Este documento dicta la estructura obligatoria del archivo `devops-architecture.md` que debes crear y mantener en la raíz de operaciones (ej. `infra/`, `devops/` o la raíz del repositorio).

**🚨 REGLA CRÍTICA DE RENDERIZADO SELECTIVO:** 
NO debes regenerar toda la arquitectura cloud o el pipeline base desde cero en cada iteración. Al ejecutar una tarea, debes mantener la estructura del documento intacta y **SOLO modificar o detallar con código Mermaid aquellas configuraciones (ej. un nuevo paso en CI/CD, un nuevo contenedor, cambios en variables de entorno o red) que hayan sido introducidas o alteradas en la tarea actual**. El resto de la infraestructura se declara implícitamente como inalterada.

---

## 📄 ESTRUCTURA OBLIGATORIA DEL DOCUMENTO CONSOLIDADO

Tu archivo `devops-architecture.md` debe contener obligatoriamente las siguientes secciones. Completa y actualiza cada una utilizando la sintaxis de Markdown y diagramas de Mermaid correspondientes:

### 1. Topología de Infraestructura
- **Diagrama Físico (Mermaid):** Diagrama `flowchart` que muestre la red de componentes físicos o lógicos (Internet -> WAF -> Load Balancers -> Contenedores/Pods Frontend y Backend -> Bases de Datos y Caché).

### 2. Pipeline DevSecOps Completo
- **Flujo CI/CD (Mermaid):** Diagrama `flowchart` del ciclo de vida del código: Commit -> Build -> Pruebas Unitarias/Integración -> Escaneos de Seguridad (SAST, Análisis de Dependencias, Búsqueda de Secretos) -> Escaneo de Imágenes -> Container Registry -> Despliegue.
- *(Actualiza este pipeline únicamente si modificas los pasos en GitHub Actions, GitLab CI, etc.)*

### 3. Git Flow y Entornos
- **Estrategia de Ramificación (Mermaid):** Diagrama `gitGraph` o `flowchart` que conecte las ramas de Git (`main`, `develop`, `feature/*`) con los entornos físicos desplegados (DEV, QA, UAT, PROD).

### 4. Estrategia de Despliegue (Deployment & Rollback)
- **Flujo de Despliegue (Mermaid):** Diagrama explicando cómo se libera el tráfico en producción (ej. Blue-Green Deployment, Canary Releases o Rolling Updates).
- **Plan de Rollback:** Representación visual o textual de los pasos para revertir a una versión anterior en caso de fallo (Health check failed -> Rollback to stable).

### 5. Matriz de Observabilidad y Secretos
- **Gestión de Secretos:** Flujo de inyección de secretos (ej. AWS Secrets Manager / Azure Key Vault -> Env Vars -> Contenedor). Prohibición explícita de credenciales en código.
- **Observabilidad (Mermaid):** Diagrama de recolección de Logs, Métricas, Traces y Errores (ej. hacia Grafana/Prometheus, Datadog o ELK) y gestión de alertas/incidentes.
