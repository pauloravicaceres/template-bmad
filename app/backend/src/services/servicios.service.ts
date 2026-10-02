import { ServicioModel, Servicio } from '../models/servicio.model';
import { CreateServicioDto } from '../schemas/servicio.schema';
import { ServicioQueryDto } from '../schemas/servicioQuery.schema';

export class ServiciosService {
  static async registrarServicio(dto: CreateServicioDto): Promise<Servicio> {
    const existeNombreCategoria = await ServicioModel.findByNombreYCategoria(dto.nombre, dto.categoria);
    if (existeNombreCategoria) {
      const error: any = new Error(`El servicio '${dto.nombre}' ya existe en la categoría '${dto.categoria}'`);
      error.statusCode = 409;
      throw error;
    }

    const existeCodigo = await ServicioModel.findByCodigo(dto.codigo);
    if (existeCodigo) {
      const error: any = new Error(`El código de servicio '${dto.codigo}' ya está registrado`);
      error.statusCode = 409;
      throw error;
    }

    return await ServicioModel.create(dto);
  }

  static async listarServicios(query: ServicioQueryDto) {
    const page = query.page || 1;
    const limit = query.limit || 10;
    return await ServicioModel.findMany({
      categoria: query.categoria,
      estado: query.estado,
      page,
      limit
    });
  }
}
