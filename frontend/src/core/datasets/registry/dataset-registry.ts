import type { IDataset } from '../models/dataset';
import type { IDatasetRegistry, RegistryChangeListener } from './dataset-registry.interface';
import { DuplicateDatasetError, DatasetNotFoundError } from '../errors/dataset.error';

/**
 * Implementation of the Dataset Registry.
 * Manages the canonical collection of datasets.
 * Preserves insertion order and emits lightweight change notifications.
 */
export class DatasetRegistry implements IDatasetRegistry {
  private readonly datasets: Map<string, IDataset>;
  private readonly listeners: Set<RegistryChangeListener>;

  constructor() {
    this.datasets = new Map<string, IDataset>();
    this.listeners = new Set<RegistryChangeListener>();
  }

  public register(dataset: IDataset): void {
    if (this.datasets.has(dataset.id)) {
      throw new DuplicateDatasetError(`Dataset with ID '${dataset.id}' is already registered.`);
    }

    this.datasets.set(dataset.id, dataset);
    this.notifyListeners();
  }

  public unregister(id: string): void {
    if (!this.datasets.has(id)) {
      throw new DatasetNotFoundError(`Dataset with ID '${id}' not found in registry.`);
    }

    this.datasets.delete(id);
    this.notifyListeners();
  }

  public get(id: string): IDataset | undefined {
    return this.datasets.get(id);
  }

  public has(id: string): boolean {
    return this.datasets.has(id);
  }

  public list(): ReadonlyArray<IDataset> {
    return Array.from(this.datasets.values());
  }

  public count(): number {
    return this.datasets.size;
  }

  public clear(): void {
    if (this.datasets.size > 0) {
      this.datasets.clear();
      this.notifyListeners();
    }
  }

  public subscribe(listener: RegistryChangeListener): () => void {
    this.listeners.add(listener);
    return () => this.unsubscribe(listener);
  }

  public unsubscribe(listener: RegistryChangeListener): void {
    this.listeners.delete(listener);
  }

  /**
   * Invokes all subscribed listeners.
   */
  private notifyListeners(): void {
    this.listeners.forEach((listener) => {
      try {
        listener();
      } catch (error) {
        // Log errors from listeners so they don't break the notification chain or registry mutations.
        console.error('Error in DatasetRegistry listener:', error);
      }
    });
  }
}
