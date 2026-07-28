import { ChoreographyEvents } from './ChoreographyEvents';
import { ChoreographyValidation } from './ChoreographyValidation';
import { DEFAULT_CHOREOGRAPHY_STATE } from './ChoreographyConfig';
import { Easing } from './interpolation/Easing';
import { CameraInterpolator } from './interpolation/CameraInterpolator';
import { AltitudeArcModel } from './interpolation/AltitudeArcModel';
import { TimeInterpolator } from './interpolation/TimeInterpolator';
import type { IChoreographyState } from './ChoreographyState';
import type { IFlightParameters, InterruptionReason } from './ChoreographyTypes';
import type { CameraEngine } from '../../core/camera';
import type { SimulationClock } from '../../core/simulation';

export class ChoreographyEngine {
  public readonly events = new ChoreographyEvents();

  private cameraEngine: CameraEngine;
  private simulationClock: SimulationClock;
  private state: IChoreographyState;

  // Caching start state for interpolation
  private startLat: number = 0;
  private startLon: number = 0;
  private startAlt: number = 0;
  private startBearing: number = 0;
  private startPitch: number = 0;
  private startClockRate: number = 1;
  private cachedDistanceDegrees: number = 0;

  constructor(cameraEngine: CameraEngine, simulationClock: SimulationClock) {
    this.cameraEngine = cameraEngine;
    this.simulationClock = simulationClock;
    this.state = { ...DEFAULT_CHOREOGRAPHY_STATE };
  }

  public flyTo(params: IFlightParameters): void {
    ChoreographyValidation.validateFlightParams(params);
    
    // Interrupt any existing flight
    if (this.state.status === 'animating') {
      this.interrupt('NEW_SEQUENCE');
    }

    const camState = this.cameraEngine.getState();
    this.startLat = camState.latitude;
    this.startLon = camState.longitude;
    this.startAlt = camState.altitude;
    this.startBearing = camState.bearing;
    this.startPitch = camState.pitch;
    this.startClockRate = params.startClockRate ?? this.simulationClock.getState().multiplier;

    // Estimate geographic distance (very naive for arcing calculation)
    const dLat = params.targetLatitude - this.startLat;
    const dLon = params.targetLongitude - this.startLon;
    this.cachedDistanceDegrees = Math.sqrt(dLat * dLat + dLon * dLon);

    this.state = {
      status: 'animating',
      activeFlight: { ...params },
      progress: 0,
      elapsedTime: 0,
      interruptionReason: 'NONE'
    };
    this.events.emitStateUpdated(this.state);
  }

  public tick(deltaMs: number): void {
    if (this.state.status !== 'animating' || !this.state.activeFlight) return;

    this.state.elapsedTime += deltaMs;
    const flight = this.state.activeFlight;
    const t = Math.min(1.0, this.state.elapsedTime / flight.durationMs);
    
    if (t >= 1.0) {
      this.finishFlight();
      return;
    }

    this.state.progress = t;
    const easedT = flight.easing === 'linear' ? Easing.linear(t) : Easing.easeInOutCubic(t);

    this.evaluateInterpolators(flight, easedT);
    this.events.emitStateUpdated(this.state);
  }

  private evaluateInterpolators(flight: IFlightParameters, t: number): void {
    const lat = CameraInterpolator.lerp(this.startLat, flight.targetLatitude, t);
    const lon = CameraInterpolator.lerpLongitude(this.startLon, flight.targetLongitude, t);
    
    const targetAlt = flight.targetAltitude ?? this.startAlt; // fallback
    const alt = flight.arcEnabled 
      ? AltitudeArcModel.calculateArcAltitude(this.startAlt, targetAlt, t, this.cachedDistanceDegrees)
      : CameraInterpolator.lerp(this.startAlt, targetAlt, t);
      
    const bearing = CameraInterpolator.lerpLongitude(this.startBearing, flight.targetBearing ?? this.startBearing, t);
    const pitch = CameraInterpolator.lerp(this.startPitch, flight.targetPitch ?? this.startPitch, t);

    // Issue jumpTo on CameraEngine
    this.cameraEngine.jumpTo({
      latitude: lat,
      longitude: lon,
      altitude: alt,
      bearing: bearing,
      pitch: pitch
    });

    if (flight.targetClockRate !== undefined) {
      const clockRate = TimeInterpolator.calculateClockRate(this.startClockRate, flight.targetClockRate, t);
      this.simulationClock.setMultiplier(clockRate);
    }
  }

  private finishFlight(): void {
    if (!this.state.activeFlight) return;

    const flight = this.state.activeFlight;
    
    // Snap to exact target
    this.cameraEngine.jumpTo({
      latitude: flight.targetLatitude,
      longitude: flight.targetLongitude,
      altitude: flight.targetAltitude ?? this.startAlt,
      bearing: flight.targetBearing ?? this.startBearing,
      pitch: flight.targetPitch ?? this.startPitch
    });

    if (flight.restoreClockRate && flight.startClockRate !== undefined) {
      this.simulationClock.setMultiplier(flight.startClockRate);
    } else if (flight.targetClockRate !== undefined) {
      this.simulationClock.setMultiplier(flight.targetClockRate);
    }

    this.state = {
      ...this.state,
      status: 'idle',
      activeFlight: null,
      progress: 1.0,
      interruptionReason: 'NONE'
    };
    this.events.emitStateUpdated(this.state);
  }

  public interrupt(reason: InterruptionReason): void {
    if (this.state.status !== 'animating') return;

    const flight = this.state.activeFlight;
    if (flight && flight.restoreClockRate && flight.startClockRate !== undefined) {
      this.simulationClock.setMultiplier(flight.startClockRate);
    }

    this.state = {
      ...this.state,
      status: 'interrupted',
      activeFlight: null,
      interruptionReason: reason
    };
    this.events.emitStateUpdated(this.state);
  }

  public cancel(): void {
    this.interrupt('NEW_SEQUENCE');
  }

  public isAnimating(): boolean {
    return this.state.status === 'animating';
  }

  public getState(): Readonly<IChoreographyState> {
    return this.state;
  }
}
