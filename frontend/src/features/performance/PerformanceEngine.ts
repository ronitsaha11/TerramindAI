import { PerformanceEvents } from './PerformanceEvents';
import { PerformanceValidation } from './PerformanceValidation';
import { RollingAverageModel } from './models/RollingAverageModel';
import { GovernorModel } from './models/GovernorModel';
import { HysteresisModel } from './models/HysteresisModel';
import type { IPerformanceState, FidelityLevel } from './PerformanceTypes';
import type { PerformanceProfile } from './PerformanceProfile';
import { LOW_PROFILE, MEDIUM_PROFILE, HIGH_PROFILE, ULTRA_PROFILE } from './PerformanceProfile';

export class PerformanceEngine {
  public readonly events = new PerformanceEvents();

  private state: IPerformanceState;
  private currentProfile: PerformanceProfile;

  private rollingAverage: RollingAverageModel;
  private governor: GovernorModel;
  private hysteresis: HysteresisModel;


  constructor() {
    this.rollingAverage = new RollingAverageModel();
    this.governor = new GovernorModel();
    this.hysteresis = new HysteresisModel();

    this.state = {
      rollingFps: 60,
      fidelityLevel: 'ULTRA', // Start at max, let it degrade if needed
      throttling: false,
      lastAdjustmentTime: 0
    };
    
    this.currentProfile = ULTRA_PROFILE;
  }

  public initialize(): void {
    this.events.emitStateUpdated(this.state);
    this.events.emitProfileUpdated(this.currentProfile);
  }

  public tick(deltaMs: number): void {
    const validDeltaMs = PerformanceValidation.validateDeltaMs(deltaMs);
    const instantFps = 1000 / validDeltaMs;
    
    const rollingFps = this.rollingAverage.update(instantFps);
    
    this.state.rollingFps = rollingFps;
    
    const currentTime = performance.now();
    if (this.hysteresis.canAdjust(currentTime)) {
      const nextLevel = this.governor.evaluate(this.state.fidelityLevel, rollingFps);
      
      if (nextLevel !== this.state.fidelityLevel) {
        this.state.fidelityLevel = nextLevel;
        this.state.lastAdjustmentTime = currentTime;
        this.state.throttling = (nextLevel !== 'ULTRA');
        
        this.hysteresis.recordAdjustment(currentTime);
        
        this.currentProfile = this.getProfileForLevel(nextLevel);
        
        this.events.emitStateUpdated(this.state);
        this.events.emitProfileUpdated(this.currentProfile);
      }
    }
  }
  
  private getProfileForLevel(level: FidelityLevel): PerformanceProfile {
    switch (level) {
      case 'LOW': return LOW_PROFILE;
      case 'MEDIUM': return MEDIUM_PROFILE;
      case 'HIGH': return HIGH_PROFILE;
      case 'ULTRA': return ULTRA_PROFILE;
    }
  }

  public getState(): Readonly<IPerformanceState> {
    return this.state;
  }
  
  public getProfile(): Readonly<PerformanceProfile> {
    return this.currentProfile;
  }
}
