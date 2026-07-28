/**
 * Represents the lifecycle state of a dataset in TerraMind AI.
 * The lifecycle tracks the dataset from creation through validation, rendering, and disposal.
 */
export type DatasetLifecycleState =
  | 'created'
  | 'validating'
  | 'ready'
  | 'rendering'
  | 'error'
  | 'disposed'
  | (string & {}); // Allows future states to be added if needed
