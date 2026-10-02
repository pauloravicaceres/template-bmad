import React from 'react';

interface Props {
  categoria: string;
  estado: string;
  onCategoriaChange: (val: string) => void;
  onEstadoChange: (val: string) => void;
}

export const FiltrosCatalogo: React.FC<Props> = ({
  categoria,
  estado,
  onCategoriaChange,
  onEstadoChange
}) => {
  return (
    <div className="flex flex-wrap gap-4 mb-6 bg-white p-4 rounded-lg border shadow-sm">
      <div className="w-48">
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
          Categoría
        </label>
        <select
          value={categoria}
          onChange={e => onCategoriaChange(e.target.value)}
          className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todas las categorías</option>
          <option value="Consultoría">Consultoría</option>
          <option value="Desarrollo">Desarrollo</option>
          <option value="Diseño">Diseño</option>
          <option value="Soporte">Soporte</option>
          <option value="Infraestructura">Infraestructura</option>
        </select>
      </div>

      <div className="w-48">
        <label className="block text-xs font-semibold text-gray-500 uppercase tracking-wider mb-1">
          Estado
        </label>
        <select
          value={estado}
          onChange={e => onEstadoChange(e.target.value)}
          className="w-full border rounded px-3 py-2 text-sm focus:outline-none focus:ring-2 focus:ring-blue-500"
        >
          <option value="">Todos los estados</option>
          <option value="activo">Activo</option>
          <option value="inactivo">Inactivo</option>
        </select>
      </div>
    </div>
  );
};
