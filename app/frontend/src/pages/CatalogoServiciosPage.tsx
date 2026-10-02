import React, { useState, useEffect, useCallback } from 'react';
import { Servicio, serviciosApi } from '../services/serviciosApi';
import { TablaServicios } from '../components/TablaServicios';
import { FiltrosCatalogo } from '../components/FiltrosCatalogo';
import { FormularioServicioModal } from '../components/FormularioServicioModal';

export const CatalogoServiciosPage: React.FC = () => {
  const [servicios, setServicios] = useState<Servicio[]>([]);
  const [loading, setLoading] = useState(true);
  const [categoria, setCategoria] = useState('');
  const [estado, setEstado] = useState('');
  const [isModalOpen, setIsModalOpen] = useState(false);

  const cargarServicios = useCallback(async () => {
    try {
      setLoading(true);
      const res = await serviciosApi.listar({
        categoria: categoria || undefined,
        estado: estado || undefined
      });
      setServicios(res.data);
    } catch (err) {
      console.error('Error cargando servicios', err);
    } finally {
      setLoading(false);
    }
  }, [categoria, estado]);

  useEffect(() => {
    cargarServicios();
  }, [cargarServicios]);

  return (
    <div className="min-h-screen bg-gray-100 p-8">
      <div className="max-w-6xl mx-auto">
        <div className="flex justify-between items-center mb-6">
          <div>
            <h1 className="text-2xl font-bold text-gray-900">Catálogo de Servicios</h1>
            <p className="text-sm text-gray-600">Gestión de tarifario y servicios parametrizables</p>
          </div>
          <button
            onClick={() => setIsModalOpen(true)}
            className="bg-blue-600 hover:bg-blue-700 text-white font-medium px-4 py-2 rounded-md text-sm shadow-sm transition-colors"
          >
            + Nuevo Servicio
          </button>
        </div>

        <FiltrosCatalogo
          categoria={categoria}
          estado={estado}
          onCategoriaChange={setCategoria}
          onEstadoChange={setEstado}
        />

        <TablaServicios servicios={servicios} loading={loading} />

        <FormularioServicioModal
          isOpen={isModalOpen}
          onClose={() => setIsModalOpen(false)}
          onSuccess={cargarServicios}
        />
      </div>
    </div>
  );
};
