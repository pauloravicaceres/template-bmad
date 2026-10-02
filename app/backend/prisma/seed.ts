import { PrismaClient } from '@prisma/client';

const prisma = new PrismaClient();

async function main() {
  console.log('Sembrando datos iniciales en la base de datos...');
  
  const serviciosIniciales = [
    {
      codigo: 'SRV-001',
      nombre: 'Consultoría en Arquitectura Cloud',
      descripcion: 'Diseño y optimización de infraestructura en AWS y GCP',
      categoria: 'Consultoría',
      tarifa_base: 150.0,
      moneda: 'USD',
      unidad_medida: 'Hora',
      estado: 'activo'
    },
    {
      codigo: 'SRV-002',
      nombre: 'Desarrollo de Software a Medida',
      descripcion: 'Construcción de aplicaciones web/mobile fullstack',
      categoria: 'Desarrollo',
      tarifa_base: 85.0,
      moneda: 'USD',
      unidad_medida: 'Hora',
      estado: 'activo'
    },
    {
      codigo: 'SRV-003',
      nombre: 'Diseño de Interfaz UX/UI',
      descripcion: 'Prototipado e investigación de usuario',
      categoria: 'Diseño',
      tarifa_base: 70.0,
      moneda: 'USD',
      unidad_medida: 'Hora',
      estado: 'activo'
    }
  ];

  for (const srv of serviciosIniciales) {
    await prisma.servicio.upsert({
      where: { codigo: srv.codigo },
      update: {},
      create: srv
    });
  }

  console.log('Seeding completado con éxito.');
}

main()
  .catch((e) => {
    console.error(e);
    process.exit(1);
  })
  .finally(async () => {
    await prisma.$disconnect();
  });
