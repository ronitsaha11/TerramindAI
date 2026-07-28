import type { IFeature } from '../../../core/interactions/interaction.types';

export interface VisibleDatasetResult {
  readonly datasetId: string;
  readonly visibleFeatures: ReadonlyArray<IFeature>;
  readonly featureCount: number;
  readonly elapsedMs: number;
}

export interface ViewportQueryResult {
  readonly datasets: ReadonlyArray<VisibleDatasetResult>;
  readonly totalVisibleFeatures: number;
  readonly totalElapsedMs: number;
  readonly timestamp: number;
}

export type ViewportQueryListener = (result: ViewportQueryResult) => void;
