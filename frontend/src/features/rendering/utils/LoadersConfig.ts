import { registerLoaders } from '@loaders.gl/core';
import { ImageLoader } from '@loaders.gl/images';

export class LoadersConfig {
  /**
   * Configures loaders.gl to use web workers for image decoding to prevent
   * main thread stalls during rapid camera movement or heavy streaming.
   */
  public static initialize(): void {
    registerLoaders([ImageLoader]);
    
    // Set global loader options if necessary, e.g., imagebitmap parsing
    // Deck.gl's TileLayer natively leverages @loaders.gl/images
    // By default, modern loaders.gl uses createImageBitmap asynchronously
    // which operates off the main thread.
  }
}
