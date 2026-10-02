import request from 'supertest';
import app from '../../src/app';

describe('GET /api/v1/servicios - US2', () => {
  beforeAll(async () => {
    await request(app).post('/api/v1/servicios').send({
      codigo: 'TEST-101',
      nombre: 'Desarrollo Web',
      categoria: 'Desarrollo',
      tarifa_base: 80.0,
      unidad_medida: 'Hora',
      estado: 'activo'
    });

    await request(app).post('/api/v1/servicios').send({
      codigo: 'TEST-102',
      nombre: 'Diseño UX',
      categoria: 'Diseño',
      tarifa_base: 65.0,
      unidad_medida: 'Hora',
      estado: 'inactivo'
    });
  });

  it('Debe listar los servicios registrados con código HTTP 200', async () => {
    const res = await request(app).get('/api/v1/servicios');
    expect(res.status).toBe(200);
    expect(res.body).toHaveProperty('data');
    expect(Array.isArray(res.body.data)).toBe(true);
    expect(res.body.total).toBeGreaterThanOrEqual(2);
  });

  it('Debe filtrar los servicios por categoría', async () => {
    const res = await request(app).get(`/api/v1/servicios?categoria=${encodeURIComponent('Diseño')}`);
    expect(res.status).toBe(200);
    expect(res.body.data.length).toBe(1);
    expect(res.body.data[0].categoria).toBe('Diseño');
  });

  it('Debe filtrar los servicios por estado', async () => {
    const res = await request(app).get('/api/v1/servicios?estado=inactivo');
    expect(res.status).toBe(200);
    expect(res.body.data.every((s: any) => s.estado === 'inactivo')).toBe(true);
  });
});
