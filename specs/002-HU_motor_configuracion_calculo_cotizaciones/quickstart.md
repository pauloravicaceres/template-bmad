# Guía de Inicio Rápido (Quickstart)

- **ID Feature:** 001-HU_configurador_y_calculo_cotizaciones
- **Rama Git:** `feat/001-HU_configurador_y_calculo_cotizaciones`

## Requisitos Previos
- Node.js 20 LTS o superior
- Docker y Docker Compose (opcional para desarrollo local en contenedores)

## 1. Configuración de Entorno

### Frontend (`app/frontend`)
```bash
cd app/frontend
npm install
npm run dev
```

### Backend (`app/backend`)
```bash
cd app/backend
npm install
npm run dev
```

## 2. Ejecución de Pruebas Unitarias del Motor de Cómputo

Para verificar que el motor de cálculo cumpla con la precisión matemática y las reglas BDD (cantidades ≤ 0, carrito vacío):
```bash
cd app/frontend
npm test -- calculationEngine.test.ts
```
