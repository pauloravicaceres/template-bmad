import { z } from 'zod';

export const createServicioSchema = z.object({
  codigo: z.string().min(1, 'El código es requerido'),
  nombre: z.string().min(1, 'El nombre es requerido'),
  descripcion: z.string().optional(),
  categoria: z.string().min(1, 'La categoría es requerida'),
  tarifa_base: z.number({ invalid_type_error: 'La tarifa debe ser un número' }).gt(0, 'La tarifa debe ser un número positivo'),
  moneda: z.string().length(3, 'El código de moneda ISO debe tener 3 letras').default('USD'),
  unidad_medida: z.string().min(1, 'La unidad de medida es requerida'),
  estado: z.enum(['activo', 'inactivo']).default('activo')
});

export type CreateServicioDto = z.infer<typeof createServicioSchema>;
