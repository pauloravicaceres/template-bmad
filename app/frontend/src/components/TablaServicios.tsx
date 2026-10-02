import React from 'react';
import { Servicio } from '../services/serviciosApi';

interface Props {
  servicios: Servicio[];
  loading: boolean;
}

export const TablaServicios: React.FC<Props> = ({ servicios, loading }) => {
  if (loading) {
    return (
      <div className="text-center py-12 bg-white rounded-lg border">
        <p className="text-gray-500 text-sm">Cargando catálogo de servicios...</p>
      </div>
    );
  }

  if (servicios.length === 0) {
    return (
      <div className="text-center py-12 bg-white rounded-lg border">
        <p className="text-gray-500 text-sm">No se encontraron servicios registrados.</p>
      </div>
    );
  }

  return (
    <div className="bg-white rounded-lg border shadow-sm overflow-hidden">
      <table className="w-full text-left text-sm text-gray-600">
        <thead className="bg-gray-50 border-b text-xs font-semibold text-gray-500 uppercase tracking-wider">
          <tr>
            <th className="px-6 py-3">Código</th>
            <th className="px-6 py-3">Nombre</th>
            <th className="px-6 py-3">Categoría</th>
            <th className="px-6 py-3">Tarifa Base</th>
            <th className="px-6 py-3">Unidad</th>
            <th className="px-6 py-3">Estado</th>
          </tr>
        </thead>
        <tbody className="divide-y divide-gray-200">
          {servicios.map(srv => (
            <tr key={srv.id} className="hover:bg-gray-50">
              <td className="px-6 py-4 font-mono text-xs text-gray-900">{srv.codigo}</td>
              <td className="px-6 py-4 font-medium text-gray-900">{srv.nombre}</td>
              <td className="px-6 py-4">{srv.categoria}</td>
              <td className="px-6 py-4 font-semibold text-gray-900">
                {srv.moneda} {srv.tarifa_base.toFixed(2)}
              </td>
              <td className="px-6 py-4">{srv.unidad_medida}</td>
              <td className="px-6 py-4">
                <span
                  className={`inline-flex items-center px-2.5 py-0.5 rounded-full text-xs font-medium ${
                    srv.estado === 'activo'
                      ? 'bg-green-100 text-green-800'
                      : 'bg-gray-100 text-gray-800'
                  }`}
                >
                  {srv.estado}
                </span>
              </td>
            </tr>
          ))}
        </tbody>
      </table>
    </div>
  );
};
