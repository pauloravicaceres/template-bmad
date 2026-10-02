export interface Servicio {
  id: string;
  codigo: string;
  nombre: string;
  descripcion?: string | null;
  categoria: string;
  tarifa_base: number;
  moneda: string;
  unidad_medida: string;
  estado: string;
  created_at: Date;
  updated_at: Date;
}

// In-memory array fallback to allow execution without active database instance
const dbServicios: Servicio[] = [];

export class ServicioModel {
  static async findByNombreYCategoria(nombre: string, categoria: string): Promise<Servicio | null> {
    const found = dbServicios.find(
      s => s.nombre.toLowerCase() === nombre.toLowerCase() && s.categoria.toLowerCase() === categoria.toLowerCase()
    );
    return found || null;
  }

  static async findByCodigo(codigo: string): Promise<Servicio | null> {
    const found = dbServicios.find(s => s.codigo.toLowerCase() === codigo.toLowerCase());
    return found || null;
  }

  static async create(data: Omit<Servicio, 'id' | 'created_at' | 'updated_at'>): Promise<Servicio> {
    const newServicio: Servicio = {
      ...data,
      id: `srv-${Date.now()}-${Math.floor(Math.random() * 1000)}`,
      created_at: new Date(),
      updated_at: new Date()
    };
    dbServicios.push(newServicio);
    return newServicio;
  }

  static async findMany(params: {
    categoria?: string;
    estado?: string;
    page: number;
    limit: number;
  }): Promise<{ data: Servicio[]; total: number; page: number; limit: number }> {
    let filtered = dbServicios;
    if (params.categoria) {
      filtered = filtered.filter(s => s.categoria.toLowerCase() === params.categoria!.toLowerCase());
    }
    if (params.estado) {
      filtered = filtered.filter(s => s.estado === params.estado);
    }

    const total = filtered.length;
    const startIndex = (params.page - 1) * params.limit;
    const data = filtered.slice(startIndex, startIndex + params.limit);

    return { data, total, page: params.page, limit: params.limit };
  }
}
