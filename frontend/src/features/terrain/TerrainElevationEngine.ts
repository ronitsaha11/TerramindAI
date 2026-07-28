import type { StreamingEngine } from '../streaming/StreamingEngine';
import type { IDEMProvider } from './DEMProvider';
import { MapzenDEMProvider } from './DEMProvider';
import { DEMCache } from './DEMCache';
import type { TerrainParameters } from './DEMTypes';

export class TerrainElevationEngine {
  private streamingEngine: StreamingEngine;
  private provider: IDEMProvider;
  private cache: DEMCache;
  private params: TerrainParameters;

  constructor(streamingEngine: StreamingEngine) {
    this.streamingEngine = streamingEngine;
    this.provider = new MapzenDEMProvider();
    this.cache = new DEMCache();
    this.params = {
      exaggeration: 1.0,
      meshMaxError: 4.0
    };
  }

  public async initialize(): Promise<void> {
    await this.provider.initialize();
  }

  public destroy(): void {
    this.provider.destroy();
  }

  public getProvider(): IDEMProvider {
    return this.provider;
  }

  public getCache(): DEMCache {
    return this.cache;
  }

  public getParameters(): Readonly<TerrainParameters> {
    return this.params;
  }

  public setExaggeration(value: number): void {
    this.params.exaggeration = Math.max(0, value);
  }

  public getStreamingEngine(): StreamingEngine {
    return this.streamingEngine;
  }
}
