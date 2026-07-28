import { CameraInterpolator } from './CameraInterpolator';

export class TimeInterpolator {
  public static calculateClockRate(startRate: number, targetRate: number, t: number): number {
    return CameraInterpolator.lerp(startRate, targetRate, t);
  }
}
