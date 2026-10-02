import { apiClient } from './apiClient';

export interface Servicio {
  id: string;
  codigo: string;
  nombre: string;
  descripcion?: string;
  categoria: string;
  tarifa_base: number;
  moneda: string;
  unidad_medida: string;
  estado: string;
}

export interface CrearServicioInput {
  codigo: string;
  nombre: string;
  descripcion?: string;
  categoria: string;
  tarifa_base: number;
  moneda?: string;
  unidad_medida: string;
  estado?: string;
}

export interface ListarServiciosParams {
  categoria?: string;
  estado?: string;
  page?: number;
  limit?: number;
}

export interface PaginatedResult<T> {
  data: T[];
  total: number;
  page: number;
  limit: number;
}

export const serviciosApi = {
  crear: async (input: CrearServicioInput): Promise<Servicio> => {
    const res = await apiClient.post<Servicio>('/servicios', input);
    return res.data;
  },

  listar: async (params?: ListarServiciosParams): Promise<PaginatedResult<Servicio>> => {
    const res = await apiClient.get<PaginatedResult<Servicio>>('/servicios', { params });
    return res.data;
  }
};
