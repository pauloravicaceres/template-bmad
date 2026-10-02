import request from 'supertest';
import app from '../../src/app';

describe('POST /api/v1/servicios - US1', () => {
  it('Debe registrar un nuevo servicio exitosamente con HTTP 201', async () => {
    const payload = {
      codigo: 'SRV-001',
      nombre: 'Consultoría Cloud',
      descripcion: 'Asesoría en arquitectura cloud AWS/GCP',
      categoria: 'Consultoría',
      tarifa_base: 150.50,
      moneda: 'USD',
      unidad_medida: 'Hora',
      estado: 'activo'
    };

    const res = await request(app)
      .post('/api/v1/servicios')
      .send(payload);

    expect(res.status).toBe(201);
    expect(res.body).toHaveProperty('id');
    expect(res.body.nombre).toBe(payload.nombre);
    expect(res.body.tarifa_base).toBe(150.50);
  });

  it('Debe retornar 400 Bad Request si la tarifa es menor o igual a 0', async () => {
    const payload = {
      codigo: 'SRV-002',
      nombre: 'Auditoría DB',
      categoria: 'Auditoría',
      tarifa_base: -10,
      unidad_medida: 'Hora'
    };

    const res = await request(app)
      .post('/api/v1/servicios')
      .send(payload);

    expect(res.status).toBe(400);
    expect(res.body).toHaveProperty('error');
  });

  it('Debe retornar 409 Conflict ante intento de duplicado por nombre y categoría', async () => {
    const payload = {
      codigo: 'SRV-003',
      nombre: 'Soporte 24/7',
      categoria: 'Soporte',
      tarifa_base: 50.0,
      unidad_medida: 'Mes'
    };

    await request(app).post('/api/v1/servicios').send(payload);
    
    const duplicatePayload = {
      ...payload,
      codigo: 'SRV-004'
    };

    const res = await request(app)
      .post('/api/v1/servicios')
      .send(duplicatePayload);

    expect(res.status).toBe(409);
  });
});
