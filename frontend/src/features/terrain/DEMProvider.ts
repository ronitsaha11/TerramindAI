import type { DEMProviderConfig } from './DEMTypes';
import { MAPZEN_ELEVATION_DECODER } from './ElevationDecoder';

export interface IDEMProvider {
  getConfig(): Readonly<DEMProviderConfig>;
  getElevationDecoder(): Record<string, number>;
  initialize(): Promise<void>;
  destroy(): void;
}

export class MapzenDEMProvider implements IDEMProvider {
  private config: DEMProviderConfig;

  constructor() {
    this.config = {
      id: 'mapzen-terrarium',
      // Public AWS endpoint for Mapzen Terrarium format
      url: 'https://s3.amazonaws.com/elevation-tiles-prod/terrarium/{z}/{x}/{y}.png',
      minZoom: 0,
      maxZoom: 15,
      attribution: 'Mapzen Terrarium'
    };
  }

  public getConfig(): Readonly<DEMProviderConfig> {
    return this.config;
  }

  public getElevationDecoder(): Record<string, number> {
    return MAPZEN_ELEVATION_DECODER;
  }

  public async initialize(): Promise<void> {
    // Provider specific setup if needed
  }

  public destroy(): void {
    // Cleanup
  }
}
