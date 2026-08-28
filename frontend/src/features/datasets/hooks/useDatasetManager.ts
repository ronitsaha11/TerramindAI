import { useCallback } from 'react';
import { useQuery } from '@tanstack/react-query';
import { useLayerStore } from '../../earth/stores/useLayerStore';
import { NotificationService } from '../../../shared/services/notification.service';
import type { IDataset } from '../../../core/datasets/models/dataset';
import { useProjectStore } from '../../../stores/useProjectStore';

const API_BASE_URL = import.meta.env.VITE_API_BASE_URL;

/** Shape of a dataset row as returned by the backend API. */
interface DatasetApiRow {
  id: string;
  name: string;
  type: string;
  extent?: [number, number, number, number];
  crs: string;
  feature_count: number;
  created_at: string;
  updated_at: string;
}

export function useDatasetManager() {
  const { activeProjectId } = useProjectStore();

  const { data: apiDatasets = [], refetch: refresh } = useQuery({
    queryKey: ['datasets', activeProjectId],
    queryFn: async () => {
      if (!activeProjectId) return [];
      const res = await fetch(`${API_BASE_URL}/projects/${activeProjectId}/datasets`);
      if (!res.ok) throw new Error('Failed to fetch datasets');
      const json = (await res.json()) as { data: DatasetApiRow[] };
      return json.data.map((d): IDataset => ({
        id: d.id,
        name: d.name,
        type: d.type,
        state: 'ready',
        data: null,
        metadata: {
          bounds: d.extent,
          featureCount: d.feature_count,
          sizeInBytes: 0,
          customProps: { crs: d.crs, format: d.type },
        },
        createdAt: new Date(d.created_at).getTime(),
        updatedAt: new Date(d.updated_at).getTime(),
      }));
    },
    enabled: !!activeProjectId,
  });

  // Note: we don't have a DELETE endpoint yet on the backend, 
  // so this just removes from local map temporarily.
  const removeDataset = useCallback((_id: string) => {
    // TODO: implement DELETE endpoint in backend
    NotificationService.info(`Deleting dataset from backend is not yet implemented.`);
  }, []);

  const toggleVisibility = useCallback((id: string) => {
    const dataset = apiDatasets.find((d: IDataset) => d.id === id);
    if (dataset) {
      const currentLayers = useLayerStore.getState().layers;
      const existing = currentLayers.find(l => l.id === id);
      const isVisible = !(existing?.visible ?? false);

      if (existing) {
        const updatedLayers = currentLayers.map(l => l.id === id ? { ...l, visible: isVisible } : l);
        useLayerStore.getState().setLayers(updatedLayers, useLayerStore.getState().layerOrder);
      } else {
        const newLayer = { 
          id, 
          label: dataset.name, 
          category: 'geojson' as const, 
          visible: isVisible, 
          opacity: 1, 
          selected: false, 
          order: currentLayers.length 
        };
        useLayerStore.getState().setLayers([...currentLayers, newLayer], [...useLayerStore.getState().layerOrder, id]);
      }
      
      NotificationService.info(`${dataset.name} is now ${isVisible ? 'visible' : 'hidden'}`);
    }
  }, [apiDatasets]);

  return {
    datasets: apiDatasets,
    removeDataset,
    toggleVisibility,
    refresh
  };
}
