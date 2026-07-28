import type { DatasetType } from '../types/dataset-type';
import type { DatasetLifecycleState } from '../types/dataset-lifecycle';
import type { IDatasetMetadata } from '../metadata/metadata.interface';
import type { DatasetStyle } from '../../styles/style.types';

/**
 * Represents an immutable domain object for a dataset in TerraMind AI.
 * This entity does not contain mutable UI or rendering state.
 */
export interface IDataset<
  TData = unknown,
  TMetadata extends IDatasetMetadata = IDatasetMetadata
> {
  /**
   * Unique identifier for the dataset.
   */
  readonly id: string;

  /**
   * Human-readable name of the dataset.
   */
  readonly name: string;

  /**
   * The type of the dataset format (e.g., geojson, vector-tile).
   */
  readonly type: DatasetType;

  /**
   * The current lifecycle state of the dataset.
   */
  readonly state: DatasetLifecycleState;

  /**
   * The actual underlying data or reference to it.
   */
  readonly data: TData;

  /**
   * Metadata associated with the dataset.
   */
  readonly metadata: TMetadata;

  /**
   * Timestamp indicating when the dataset was created.
   */
  readonly createdAt: number;

  /**
   * Timestamp indicating when the dataset was last updated.
   */
  readonly updatedAt: number;

  /**
   * Optional JSON-serializable styling configuration for the dataset.
   */
  readonly style?: DatasetStyle;
}
