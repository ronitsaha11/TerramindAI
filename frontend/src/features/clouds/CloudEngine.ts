import { CloudEvents } from './CloudEvents';
import { CloudLayerModel } from './models/CloudLayerModel';
import { CloudMovementModel } from './models/CloudMovementModel';
import { DEFAULT_CLOUD_CONFIG } from './CloudConfig';
import type { CloudState } from './CloudState';
import type { SimulationClock } from '../../core/simulation/SimulationClock';

export class CloudEngine {
  public readonly events = new CloudEvents();
  
  private layerModel: CloudLayerModel;
  private movementModel: CloudMovementModel;
  private simulationClock: SimulationClock;

  // We keep a local state representation to emit
  private state: CloudState;
  private lastTimeMs: number;

  constructor(simulationClock: SimulationClock) {
    this.simulationClock = simulationClock;
    this.layerModel = new CloudLayerModel(DEFAULT_CLOUD_CONFIG.altitudeMeters, DEFAULT_CLOUD_CONFIG.opacity);
    this.movementModel = new CloudMovementModel(DEFAULT_CLOUD_CONFIG.baseSpeedDegreesPerSecond);
    
    this.lastTimeMs = performance.now();

    this.state = this.buildState();
  }

  public initialize(): void {
    this.events.emitStateUpdated(this.state);
  }

  /**
   * Called by the environment/simulation engine on tick
   */
  public update(): void {
    const now = performance.now();
    const dtSeconds = (now - this.lastTimeMs) / 1000.0;
    this.lastTimeMs = now;

    // Simulation clock multiplier dictates how fast time is moving globally
    const clockMultiplier = this.simulationClock.getState().multiplier;

    this.movementModel.update(dtSeconds, clockMultiplier);

    const newState = this.buildState();
    
    // Only emit if state meaningfully changed (e.g., rotation updated enough)
    // For a smooth globe, we update continuously, but could throttle if needed.
    this.state = newState;
    this.events.emitStateUpdated(this.state);
  }

  public getState(): Readonly<CloudState> {
    return this.state;
  }

  private buildState(): CloudState {
    return {
      enabled: this.layerModel.isEnabled(),
      altitudeMeters: this.layerModel.getAltitudeMeters(),
      opacity: this.layerModel.getOpacity(),
      rotationOffsetDegrees: this.movementModel.getOffsetDegrees()
    };
  }
}
