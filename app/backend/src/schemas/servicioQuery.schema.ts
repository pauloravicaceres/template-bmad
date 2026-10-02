import { z } from 'zod';

export const servicioQuerySchema = z.object({
  categoria: z.string().optional(),
  estado: z.enum(['activo', 'inactivo']).optional(),
  page: z.union([z.string(), z.number()]).optional().transform(val => (val ? Number(val) : 1)),
  limit: z.union([z.string(), z.number()]).optional().transform(val => (val ? Number(val) : 10))
});

export type ServicioQueryDto = z.infer<typeof servicioQuerySchema>;
