import type { PickingInfo } from '@deck.gl/core';
import type { IDeckInteractionAdapter } from './deck-interaction-adapter.interface';
import type { IInteractionManager, IFeature } from '../../../core/interactions';

/**
 * Implementation of the DeckInteractionAdapter.
 * Transforms PickingInfo into renderer-independent IFeature objects and forwards
 * them to the core InteractionManager.
 */
export class DeckInteractionAdapter implements IDeckInteractionAdapter {
  private readonly interactionManager: IInteractionManager;

  constructor(interactionManager: IInteractionManager) {
    this.interactionManager = interactionManager;
  }

  public onLayerHover(info: PickingInfo): void {
    if (!info.object) {
      // Clear hovered feature but maintain mouse coordinates if cursor is over the canvas
      this.interactionManager.setHovered(null, info.x ?? null, info.y ?? null);
      return;
    }

    try {
      const feature = this.mapPickingInfoToFeature(info);
      this.interactionManager.setHovered(feature, info.x ?? null, info.y ?? null);
    } catch (e) {
      console.warn('DeckInteractionAdapter: Failed to process hover event gracefully.', e);
      // Fail safely on malformed picking info without crashing the render loop
    }
  }

  public onLayerClick(info: PickingInfo): void {
    if (!info.object) {
      this.interactionManager.clearSelection();
      return;
    }

    try {
      const feature = this.mapPickingInfoToFeature(info);
      this.interactionManager.setSelected(feature);
    } catch (e) {
      console.warn('DeckInteractionAdapter: Failed to process click event gracefully.', e);
    }
  }

  /**
   * Translates the mutable, renderer-specific PickingInfo into an immutable IFeature.
   */
  private mapPickingInfoToFeature(info: PickingInfo): IFeature {
    const rawObject = info.object as Record<string, unknown>;
    const properties = (rawObject.properties as Record<string, unknown>) || {};
    
    // Feature ID Resolution
    // 1. Deck.gl info.object.id
    // 2. GeoJSON properties.id
    // 3. Auto-generated UUID as last resort (to ensure the domain gets a valid string)
    const id = 
      (typeof rawObject.id === 'string' ? rawObject.id : undefined) ?? 
      (typeof properties.id === 'string' ? properties.id : undefined) ?? 
      crypto.randomUUID();

    // Dataset ID Mapping
    // If the layer was built by the DatasetLayerFactory, its ID is prefixed with 'layer-'
    // e.g. layer-uuid -> datasetId = uuid
    const layerId = info.layer?.id || 'unknown';
    const datasetId = layerId.startsWith('layer-') ? layerId.replace('layer-', '') : layerId;

    return Object.freeze({
      id,
      datasetId,
      properties: Object.freeze({ ...properties }),
      geometry: rawObject.geometry ? Object.freeze({ ...(rawObject.geometry as Record<string, unknown>) }) : undefined,
    });
  }
}
