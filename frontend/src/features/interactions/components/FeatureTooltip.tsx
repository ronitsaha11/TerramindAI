import React from 'react';
import { useInteractionStore } from '../../earth/stores/use-interaction-store';

/**
 * FeatureTooltip consumes the synchronized Zustand interaction state
 * and renders a tooltip overlay near the user's cursor.
 * 
 * It is completely unaware of Deck.gl or the InteractionManager.
 */
export const FeatureTooltip: React.FC = () => {
  const { hoveredFeature, cursorX, cursorY } = useInteractionStore();

  if (!hoveredFeature || cursorX === null || cursorY === null) {
    return null;
  }

  // Extract a few properties for preview
  const entries = Object.entries(hoveredFeature.properties).slice(0, 5);

  return (
    <div
      className="pointer-events-none absolute z-50 rounded bg-gray-900/90 p-3 text-xs text-white shadow-lg backdrop-blur"
      style={{
        left: cursorX + 15,
        top: cursorY + 15,
        maxWidth: 300,
      }}
    >
      <div className="mb-2 border-b border-gray-700 pb-1 font-semibold">
        Feature: {hoveredFeature.id}
        <div className="text-[10px] text-gray-400">Dataset: {hoveredFeature.datasetId}</div>
      </div>
      
      <div className="flex flex-col gap-1">
        {entries.length > 0 ? (
          entries.map(([key, value]) => (
            <div key={key} className="flex justify-between gap-4">
              <span className="text-gray-400">{key}:</span>
              <span className="truncate">{String(value)}</span>
            </div>
          ))
        ) : (
          <div className="text-gray-500 italic">No properties</div>
        )}
      </div>
    </div>
  );
};
