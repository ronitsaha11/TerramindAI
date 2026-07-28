/**
 * Astronomical and Mathematical Constants for the Earth Reference System.
 * Priorities: Deterministic visualization accuracy over astronomical observatory precision.
 */

/** 
 * Unix Epoch timestamp for J2000.0 (January 1.5, 2000, TT).
 * J2000.0 is exactly 2000-01-01T12:00:00Z.
 * 946728000000 milliseconds.
 */
export const J2000_EPOCH_MS = 946728000000;

/** Milliseconds in a standard 24-hour solar day */
export const MS_PER_DAY = 86400000;

/** Earth's mean radius in meters (WGS84 approx) */
export const EARTH_RADIUS_METERS = 6371000;

/** 
 * Stellar angle constants for Earth Rotation Angle (ERA) calculation.
 * ERA(Tu) = 2π(0.7790572732640 + 1.00273781191135448 * Tu)
 * Tu is Julian UT1 date - 2451545.0.
 * We use degrees instead of radians for internal consistency.
 */
export const ERA_CONSTANT_DEGREES = 280.46061837504;
export const ERA_RATE_DEGREES_PER_DAY = 360.9856122880876;
