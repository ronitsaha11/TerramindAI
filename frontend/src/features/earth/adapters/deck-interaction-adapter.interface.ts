import type { PickingInfo } from '@deck.gl/core';

/**
 * An adapter specifically for Deck.gl to bridge the gap between rendering-engine
 * picking events and the renderer-independent Interaction Core.
 */
export interface IDeckInteractionAdapter {
  /**
   * Translates a Deck.gl hover event into a domain hover state change.
   * 
   * @param info - The raw PickingInfo object provided by Deck.gl.
   */
  onLayerHover(info: PickingInfo): void;

  /**
   * Translates a Deck.gl click event into a domain selection state change.
   * 
   * @param info - The raw PickingInfo object provided by Deck.gl.
   */
  onLayerClick(info: PickingInfo): void;
}
