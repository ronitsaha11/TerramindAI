import type { IDatasetLayerController } from './dataset-layer-controller.interface';
import type { IDatasetRegistry } from '../../../core/datasets/registry/dataset-registry.interface';
import type { IDatasetLayerFactory } from '../../../core/datasets/rendering/dataset-layer.factory.interface';
import type { LayerManager } from './LayerManager';
import type { LayerConfig, LayerCategory } from '../types/layer.types';
import { UnsupportedDatasetTypeError } from '../../../core/datasets/rendering/rendering.error';
import type { IDataset } from '../../../core/datasets/models/dataset';
import type { ILayerLifecycleManager } from './layer-lifecycle-manager.interface';

/**
 * Implementation of the DatasetLayerController.
 * Orchestrates the translation of Datasets into renderable LayerConfigs.
 * Dependencies are strictly injected.
 */
export class DatasetLayerController implements IDatasetLayerController {
  private readonly registry: IDatasetRegistry;
  private readonly factory: IDatasetLayerFactory;
  private readonly layerManager: LayerManager;
  private readonly lifecycleManager: ILayerLifecycleManager;
  
  private unsubscribe: (() => void) | null = null;
  private isInitialized = false;

  constructor(
    registry: IDatasetRegistry,
    factory: IDatasetLayerFactory,
    layerManager: LayerManager,
    lifecycleManager: ILayerLifecycleManager
  ) {
    this.registry = registry;
    this.factory = factory;
    this.layerManager = layerManager;
    this.lifecycleManager = lifecycleManager;
  }

  public initialize(): void {
    if (this.isInitialized) {
      console.warn('DatasetLayerController is already initialized.');
      return;
    }

    // Initial sync
    this.syncAll();

    // Subscribe to ongoing changes
    this.unsubscribe = this.registry.subscribe(() => {
      this.syncAll();
    });

    this.isInitialized = true;
  }

  public destroy(): void {
    if (this.unsubscribe) {
      this.unsubscribe();
      this.unsubscribe = null;
    }
    this.isInitialized = false;
  }

  /**
   * Performs a complete synchronization between the Registry and the LayerManager.
   * Compares current registry datasets with what the LayerManager knows, adding or removing as necessary.
   */
  private syncAll(): void {
    try {
      const datasets = this.registry.list();
      const desiredIds = datasets.map(d => d.id);
      
      const reconciliationPlan = this.lifecycleManager.reconcile(desiredIds);

      // 1. Remove layers
      for (const datasetId of reconciliationPlan.remove) {
        // The factory prefixes IDs with 'layer-', so we must remove that layer ID
        this.layerManager.removeLayer(`layer-${datasetId}`);
      }
      
      // 2. Add or keep datasets
      for (const datasetId of reconciliationPlan.add) {
        const dataset = this.registry.get(datasetId);
        if (dataset) {
          this.syncDataset(dataset);
        }
      }

      // 'keep' layers are already in LayerManager, no action needed for this sprint.
    } catch (error) {
      console.error('DatasetLayerController synchronization failed:', error);
      // Let infrastructure errors bubble or log, but do not swallow completely silently.
    }
  }

  /**
   * Syncs an individual dataset into the LayerManager.
   */
  private syncDataset(dataset: IDataset): void {
    try {
      const definition = this.factory.create(dataset);
      
      const config: LayerConfig = {
        id: definition.id,
        label: definition.name,
        category: definition.renderType as LayerCategory,
        data: definition.sourceData,
        style: {
          visible: definition.visible,
          opacity: definition.opacity,
          // Extract specific style properties if present in definition.style
          // For now, we pass basic defaults or those derived from the definition.
        },
      };

      this.layerManager.registerLayer(config);
    } catch (error) {
      if (error instanceof UnsupportedDatasetTypeError) {
        console.warn(`Skipping unsupported dataset '${dataset.id}':`, error.message);
      } else {
        console.error(`Failed to sync dataset '${dataset.id}' to LayerManager:`, error);
        // Infrastructure or unexpected errors propagate
        throw error;
      }
    }
  }
}
