import { useEffect, useState, useCallback } from 'react';
import { EarthEngine } from '../../earth/services/EarthEngine';
import { useLayerStore } from '../../earth/stores/useLayerStore';
import { NotificationService } from '../../../shared/services/notification.service';
import type { IDataset } from '../../../core/datasets/models/dataset';

export function useDatasetManager() {
  const [datasets, setDatasets] = useState<ReadonlyArray<IDataset>>(() => {
    const registry = EarthEngine.getInstance().getDatasetRegistry();
    return registry ? [...registry.list()] : [];
  });

  const refresh = useCallback(() => {
    const registry = EarthEngine.getInstance().getDatasetRegistry();
    if (registry) {
      setDatasets([...registry.list()]);
    }
  }, []);

  useEffect(() => {
    const registry = EarthEngine.getInstance().getDatasetRegistry();
    if (!registry) return;

    // Subscribe to changes
    const unsubscribe = registry.subscribe(refresh);
    return () => unsubscribe();
  }, [refresh]);

  const removeDataset = useCallback((id: string) => {
    const registry = EarthEngine.getInstance().getDatasetRegistry();
    if (registry) {
      const dataset = registry.get(id);
      registry.unregister(id);
      if (dataset) {
        NotificationService.success(`Removed dataset: ${dataset.name}`);
      }
    }
  }, []);

  const toggleVisibility = useCallback((id: string) => {
    const layerManager = EarthEngine.getInstance().getLayerManager();
    const registry = EarthEngine.getInstance().getDatasetRegistry();
    if (layerManager && registry) {
      const current = useLayerStore.getState().layers.find(l => l.id === id)?.visible ?? true;
      const isVisible = !current;
      layerManager.setVisibility(id, isVisible);
      
      const dataset = registry.get(id);
      if (dataset) {
        NotificationService.info(`${dataset.name} is now ${isVisible ? 'visible' : 'hidden'}`);
      }
    }
  }, []);

  return {
    datasets,
    removeDataset,
    toggleVisibility,
    refresh
  };
}
