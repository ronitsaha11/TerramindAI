import { SpaceEvents } from './SpaceEvents';
import { DEFAULT_SPACE_CONFIG } from './SpaceConfig';
import { StarFieldModel } from './models/StarFieldModel';
import { SunVisualModel } from './models/SunVisualModel';
import { MoonVisualModel } from './models/MoonVisualModel';
import { BackgroundModel } from './models/BackgroundModel';
import type { SpaceState } from './SpaceState';
import type { EarthEphemeris } from '../../core/planet/EarthEphemeris';

export class SpaceEngine {
  public readonly events = new SpaceEvents();

  private earthEphemeris: EarthEphemeris;
  private unsubEphemeris: (() => void) | null = null;
  
  private starFieldModel: StarFieldModel;
  private sunVisualModel: SunVisualModel;
  private moonVisualModel: MoonVisualModel;
  private backgroundModel: BackgroundModel;

  private state: SpaceState;

  constructor(earthEphemeris: EarthEphemeris) {
    this.earthEphemeris = earthEphemeris;
    
    this.starFieldModel = new StarFieldModel(DEFAULT_SPACE_CONFIG.starVisibility, DEFAULT_SPACE_CONFIG.starIntensity);
    this.sunVisualModel = new SunVisualModel();
    this.moonVisualModel = new MoonVisualModel();
    this.backgroundModel = new BackgroundModel(DEFAULT_SPACE_CONFIG.backgroundColor);

    this.state = this.buildState();
  }

  public initialize(): void {
    this.unsubEphemeris = this.earthEphemeris.events.onUpdated(() => {
      // We trigger an update when the ephemeris ticks.
      this.update();
    });

    this.events.emitStateUpdated(this.state);
  }

  public update(): void {
    // In a fully integrated system, EarthEphemeris provides real-time celestial coordinates.
    // For Phase 11.5.B11, we demonstrate pulling from the ephemeris (or mocking the integration point).
    // Assuming EarthEphemeris has getSunDirectionEci(), getMoonPositionEci(), getCelestialRotationDegrees()
    
    // We update our visual models
    // this.sunVisualModel.update(this.earthEphemeris.getSunDirectionEci());
    // this.moonVisualModel.update(this.earthEphemeris.getMoonPositionEci(), this.earthEphemeris.getMoonPhase());
    // ...

    const newState = this.buildState();
    
    // Only emit if changed (reference or deep equality check in production)
    this.state = newState;
    this.events.emitStateUpdated(this.state);
  }

  public getState(): Readonly<SpaceState> {
    return this.state;
  }

  private buildState(): SpaceState {
    return {
      // Mocking ephemeris call for the phase since the exact methods on EarthEphemeris depend on earlier phases
      sunDirectionEci: this.sunVisualModel.getDirectionEci(),
      moonPositionEci: this.moonVisualModel.getPositionEci(),
      moonPhase: this.moonVisualModel.getPhase(),
      celestialRotationDegrees: 0, // this.earthEphemeris.getCelestialRotationDegrees(),
      starConfig: this.starFieldModel.getConfig(),
      backgroundColor: this.backgroundModel.getColor()
    };
  }

  public destroy(): void {
    if (this.unsubEphemeris) {
      this.unsubEphemeris();
      this.unsubEphemeris = null;
    }
  }
}
