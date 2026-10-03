# Modelo de Datos y Esquema

- **ID Feature:** 001-HU_configurador_y_calculo_cotizaciones
- **Fecha:** 2026-10-02

## 1. Entidades del Dominio (TypeScript)

### `ServiceItem`
Representa un servicio o módulo configurable del catálogo.
```typescript
export interface ServiceItem {
  id: string;
  name: string;
  basePrice: number;
  description: string;
}
```

### `QuoteItem`
Representa un ítem seleccionado dentro de la cotización en curso.
```typescript
export interface QuoteItem {
  serviceId: string;
  quantity: number;
  customPrice?: number;
}
```

### `CalculationResult`
Resultado inmutable devuelto por el motor de cálculo.
```typescript
export interface CalculationResult {
  subtotal: number;
  discount: number;
  tax: number;
  total: number;
  isValid: boolean;
  errors: Record<string, string>;
}
```

## 2. Esquema de Base de Datos PostgreSQL (`app/backend/migrations/001_init.sql`)

```sql
CREATE TABLE services_catalog (
    id VARCHAR(36) PRIMARY KEY,
    name VARCHAR(255) NOT NULL,
    base_price NUMERIC(12, 2) NOT NULL CHECK (base_price >= 0),
    description TEXT,
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quotes (
    id VARCHAR(36) PRIMARY KEY,
    subtotal NUMERIC(12, 2) NOT NULL CHECK (subtotal >= 0),
    total NUMERIC(12, 2) NOT NULL CHECK (total >= 0),
    status VARCHAR(50) DEFAULT 'DRAFT',
    created_at TIMESTAMP WITH TIME ZONE DEFAULT CURRENT_TIMESTAMP
);

CREATE TABLE quote_items (
    id VARCHAR(36) PRIMARY KEY,
    quote_id VARCHAR(36) REFERENCES quotes(id) ON DELETE CASCADE,
    service_id VARCHAR(36) REFERENCES services_catalog(id),
    quantity INT NOT NULL CHECK (quantity > 0),
    unit_price NUMERIC(12, 2) NOT NULL CHECK (unit_price >= 0),
    subtotal NUMERIC(12, 2) NOT NULL CHECK (subtotal >= 0)
);
```
