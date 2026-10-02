import { Request, Response, NextFunction } from 'express';
import { createServicioSchema } from '../schemas/servicio.schema';
import { servicioQuerySchema } from '../schemas/servicioQuery.schema';
import { ServiciosService } from '../services/servicios.service';

export class ServiciosController {
  static async crearServicio(req: Request, res: Response, next: NextFunction) {
    try {
      const dataValida = createServicioSchema.parse(req.body);
      const servicio = await ServiciosService.registrarServicio(dataValida);
      return res.status(201).json(servicio);
    } catch (error) {
      next(error);
    }
  }

  static async listarServicios(req: Request, res: Response, next: NextFunction) {
    try {
      const queryValida = servicioQuerySchema.parse(req.query);
      const resultado = await ServiciosService.listarServicios(queryValida);
      return res.status(200).json(resultado);
    } catch (error) {
      next(error);
    }
  }
}
