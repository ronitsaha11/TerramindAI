/**
 * Responsible for rendering a dataset domain object into a format consumable by a rendering engine (e.g., Deck.gl, MapLibre).
 * Ownership: Converts abstract dataset representations into visual layer representations.
 */
export interface IDatasetRenderer<TDataset, TRenderOutput> {
  /**
   * Takes a dataset and returns a rendering output.
   * 
   * @param dataset - The dataset to render.
   * @returns The output specific to the targeted rendering engine.
   */
  render(dataset: TDataset): TRenderOutput;
}
