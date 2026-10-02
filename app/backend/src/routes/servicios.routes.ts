import { Router } from 'express';
import { ServiciosController } from '../controllers/servicios.controller';

const router = Router();

router.post('/', ServiciosController.crearServicio);
router.get('/', ServiciosController.listarServicios);

export default router;
