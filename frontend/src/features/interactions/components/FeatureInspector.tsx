import React from 'react';
import { useInteractionStore } from '../../earth/stores/use-interaction-store';

/**
 * FeatureInspector displays the currently selected feature's full properties.
 * 
 * It is completely decoupled from the rendering engine and reads strictly
 * from the synchronized Zustand projection.
 */
export const FeatureInspector: React.FC = () => {
  const { selectedFeature } = useInteractionStore();

  if (!selectedFeature) {
    return (
      <div className="flex h-full w-full items-center justify-center p-4 text-sm text-gray-500">
        No feature selected. Click a feature on the map to inspect it.
      </div>
    );
  }

  const properties = Object.entries(selectedFeature.properties);

  return (
    <div className="flex h-full w-full flex-col bg-gray-900 text-sm text-gray-200">
      <div className="border-b border-gray-800 bg-gray-950 p-4">
        <h3 className="font-semibold text-white">Feature Inspector</h3>
        <p className="text-xs text-gray-400">ID: {selectedFeature.id}</p>
        <p className="text-xs text-gray-400">Dataset: {selectedFeature.datasetId}</p>
      </div>
      
      <div className="flex-1 overflow-y-auto p-4">
        {properties.length > 0 ? (
          <table className="w-full text-left text-xs">
            <tbody>
              {properties.map(([key, value]) => (
                <tr key={key} className="border-b border-gray-800/50">
                  <td className="py-2 pr-4 align-top font-mono text-gray-400">{key}</td>
                  <td className="break-all py-2 text-white">{String(value)}</td>
                </tr>
              ))}
            </tbody>
          </table>
        ) : (
          <div className="text-gray-500 italic">This feature contains no properties.</div>
        )}
      </div>
    </div>
  );
};
