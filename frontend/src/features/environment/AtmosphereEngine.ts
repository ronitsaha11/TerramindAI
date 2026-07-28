import { AtmosphereModel } from './AtmosphereModel';
import { SkyModel } from './lighting/SkyModel';
import { AtmosphereEvents } from './AtmosphereEvents';
import type { AtmosphereState, Vector3 } from './AtmosphereState';

// In a full implementation, we'd import and subscribe to EarthEphemeris here.
// For Phase 11.5.B8, we'll expose a setter for sun direction to be updated by the game loop.
export class AtmosphereEngine {
  public readonly events = new AtmosphereEvents();
  
  private model: AtmosphereModel;
  private skyModel: SkyModel;
  private state: AtmosphereState;

  constructor() {
    this.model = new AtmosphereModel();
    this.skyModel = new SkyModel();
    
    const initialSun: Vector3 = { x: 1, y: 0, z: 0 };
    const skyState = this.skyModel.generateSkyState(initialSun);

    this.state = {
      planetRadius: this.model.getPlanetRadius(),
      atmosphereRadius: this.model.getAtmosphereRadius(),
      rayleighScattering: this.model.getRayleighScattering(),
      mieScattering: this.model.getMieScattering(),
      rayleighScaleHeight: this.model.getRayleighScaleHeight(),
      mieScaleHeight: this.model.getMieScaleHeight(),
      sunDirectionEci: initialSun,
      zenithColor: skyState.zenithColor,
      horizonColor: skyState.horizonColor,
      ambientIntensity: skyState.ambientIntensity,
      twilightFactor: skyState.twilightFactor
    };
  }

  public initialize(): void {
    // Initial state broadcast
    this.events.emitStateUpdated(this.state);
  }

  public updateSunDirection(sunDirectionEci: Vector3): void {
    // Prevent per-frame allocation by modifying in place where possible,
    // though object spread is standard in React architectures.
    const skyState = this.skyModel.generateSkyState(sunDirectionEci);

    this.state = {
      ...this.state,
      sunDirectionEci,
      zenithColor: skyState.zenithColor,
      horizonColor: skyState.horizonColor,
      ambientIntensity: skyState.ambientIntensity,
      twilightFactor: skyState.twilightFactor
    };

    this.events.emitStateUpdated(this.state);
  }

  public getState(): Readonly<AtmosphereState> {
    return this.state;
  }

  public destroy(): void {
    // Cleanup subscriptions
  }
}
