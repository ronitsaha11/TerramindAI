# TerraMind Living Earth Experience

**Volume IV: Camera & Navigation Architecture**

- **Version:** 1.0.0
- **Status:** DRAFT
- **Phase:** 11.5
- **Last Updated:** 2026-07-28

**Dependencies:**
- Living Earth Master Plan
- Volume I: Vision & Product Philosophy
- Volume II: World Simulation Architecture
- Volume III: Rendering Architecture

**Influences:**
- Volume VII: Streaming & Transition
- Volume VIII: Performance
- Volume IX: Experience Choreography

---

## 1. Purpose

This volume establishes the architectural boundaries and conceptual models for the Camera and Navigation subsystems. The camera represents the user's observational window into the Living Earth Experience. Architecturally, the camera is strictly an observer; it translates user intent (manual inputs or automated transitions) into viewpoint parameters. It never owns the world simulation state, and it never executes rendering instructions. By formalizing this separation, we ensure navigation remains predictable, immersive, and independent of backend simulation complexity.

## 2. Architectural Goals

The navigation architecture is designed to fulfill the following goals:

- **Predictable Navigation:** Camera movements must always resolve predictably regardless of input modality (mouse, keyboard, programmatic trigger).
- **Spatial Awareness:** The camera must inherently preserve the user's understanding of their location, scale, and orientation relative to the Earth.
- **Continuous Exploration:** Moving from orbital altitudes down to surface-level terrain must occur without loading screens, discrete jumps, or perspective breaks.
- **Smooth Transitions:** Automated movements (e.g., Fly-To commands) must interpolate seamlessly, respecting kinetic momentum.
- **User Orientation:** The camera must gracefully handle poles, the equator, and complex terrain without inducing disorientation or gimbal lock.

## 3. Camera Principles

- **Camera never owns world state.**
  - *Description:* The camera does not know what time it is, where the sun is, or what the weather is doing.
  - *Motivation:* Prevents tight coupling with the world simulation.
  - *Architectural implications:* The camera only calculates matrices based on abstract spatial coordinates.

- **Camera follows simulation.**
  - *Description:* The camera observes a moving planet. It must account for planetary rotation without modifying the rotation itself.
  - *Motivation:* The user expects to remain anchored to a location on Earth even as the planet rotates in space.
  - *Architectural implications:* Camera matrices must be computed relative to the simulation's current planetary orientation matrix.

- **Every motion has purpose.**
  - *Description:* Camera animations and movements are exclusively driven by user intent or intelligence presentation.
  - *Motivation:* Gratuitous camera shakes or uncontrolled drift erode the platform's professional utility.
  - *Architectural implications:* Idle camera states must remain mathematically stable and static relative to the anchor point.

- **Motion preserves orientation.**
  - *Description:* Rapid jumps across the globe must visually describe the journey (e.g., zooming out, panning across, zooming in).
  - *Motivation:* Teleportation destroys spatial context and confuses users.
  - *Architectural implications:* Trajectory generation is a mandatory component of any point-to-point camera movement.

- **Navigation is interruptible.**
  - *Description:* Any automated camera transition can be canceled instantly by a manual user input.
  - *Motivation:* The user must always feel in absolute control of the viewpoint.
  - *Architectural implications:* The camera state machine must support immediate preemptive overrides without leaving the camera in an invalid state.

- **Motion never surprises the user.**
  - *Description:* Collision with terrain or violent constraint snapping is strictly forbidden.
  - *Motivation:* Jarring collisions break immersion and cause frustration.
  - *Architectural implications:* The camera controller must enforce continuous altitude constraints and collision detection mathematically during trajectory evaluation.

## 4. Responsibilities

The camera architecture is exclusively responsible for managing:

- **Orbit:** Rotation around a defined focal point on the planet's surface or around the planet itself.
- **Pan:** Lateral translation across the planetary surface.
- **Zoom:** Scaling the distance between the camera and the focal point, enforcing altitude constraints.
- **Fly-To:** Generating and executing smooth, continuous trajectories between two arbitrary geographic coordinates.
- **Focus:** Tracking or framing a specific geographic entity or bounding box dynamically.
- **Tracking:** Maintaining a stable observation vector relative to a moving object on the planet's surface.
- **Animation:** Evaluating kinetic interpolation (easing) over time for programmatic movements.
- **Navigation State:** Retaining the current valid viewpoint (latitude, longitude, altitude, pitch, bearing) and outputting derived matrices.

## 5. Architectural Boundaries

To preserve stability, the camera adheres to the following boundaries:

- **Interaction with Rendering (Volume III):** The camera provides the projection and view matrices per frame. It does not issue draw calls or possess knowledge of scene geometry.
- **Interaction with Simulation (Volume II):** The camera consumes the current planetary rotation matrix to anchor itself to the Earth. It does not dictate simulation time.
- **Interaction with Planet Systems (Volume V):** The camera queries planet systems (e.g., Terrain) to determine surface altitude for collision prevention, but it does not instruct the terrain how to load.
- **Interaction with Streaming (Volume VII):** The camera broadcasts its current viewpoint frustum so that the streaming engine can determine which data tiles to load. The camera itself fetches no data.
- **Interaction with UI:** The UI sends navigation intents (e.g., "Fly to coordinates"). The camera executes the intent and broadcasts state changes back so the UI can update compasses or coordinate readouts.

## 6. Camera State Model

The camera operates as a state machine conceptually consisting of the following modes:

- **Idle:** The camera is completely at rest relative to the planetary surface. No inputs or interpolations are active.
- **Manual:** The user is actively manipulating the viewpoint via input devices. The camera continuously evaluates constraints and applies kinetic friction upon release.
- **Animated:** The camera is autonomously interpolating along a predefined trajectory (e.g., a Fly-To command).
- **Tracking:** The camera is dynamically updating its focal point to match a moving coordinate provided by an external data stream.
- **Interrupted:** A transitional state triggered when manual input overrides an Animated or Tracking state, smoothly handing control back to the Manual state.

## 7. Navigation Philosophy

The navigation design is driven by principles that empower the user:

- **Discoverability:** Complex maneuvers (like tilting or bearing adjustments) must be intuitive and discoverable through standard mouse/touch gestures.
- **Context Preservation:** When zooming in on a target, the camera must naturally tilt to preserve the horizon, ensuring the user understands surface scale.
- **Spatial Continuity:** The experience of flying across the globe must emulate physical reality—arcing out into space before descending, rather than sliding abruptly across the surface.
- **Progressive Movement:** Input sensitivity must scale dynamically with altitude. Panning at ground level moves meters; panning in orbit moves continents.

## 8. Quality Attributes

- **Responsiveness:** Input lag between user action and camera movement must be imperceptible.
- **Predictability:** Gestures must yield identical camera behaviors regardless of the current latitude or altitude.
- **Accessibility:** All manual camera controls must be fully operable via keyboard inputs, screen readers, and alternative input devices.
- **Precision:** The mathematical representation of the camera must support millimeter-level precision without suffering from floating-point jitter at surface level.
- **Maintainability:** The camera controller logic must be cleanly isolated from input event listeners to allow headless testing.

## 9. Risks

- **Motion Sickness:**
  - *Risk:* Rapid, un-eased camera animations or extreme field-of-view distortions.
  - *Mitigation:* Enforce strict easing functions, clamp maximum rotation speeds, and avoid unnatural FOV values.
- **Camera Discontinuity:**
  - *Risk:* "Popping" or teleporting between frames when receiving programmatic updates.
  - *Mitigation:* Require all automated location updates to flow through the interpolation trajectory engine.
- **Orientation Loss:**
  - *Risk:* Users becoming lost after complex manual manipulations (e.g., pitch and bearing adjustments).
  - *Mitigation:* Provide UI mechanisms to instantly reset bearing to North and pitch to nadir via a smooth animation.
- **Conflicting Controllers:**
  - *Risk:* The UI issuing a Fly-To command while the user is actively panning, resulting in erratic fighting.
  - *Mitigation:* Implement strict state machine priorities where manual input instantly cancels programmatic intents.

## 10. Summary

The Camera and Navigation Architecture defines the rules of observation for the Living Earth. By enforcing a strict separation from rendering and simulation, establishing a robust state model, and prioritizing spatial continuity, TerraMind ensures that users can intuitively and gracefully explore the planet at any scale without sacrificing orientation or immersion.

---

## Implementation Requirements

The following requirements mandate the formal engineering outcomes for the Camera and Navigation systems.

| ID | Description | Priority | Verification | Source Volume |
|---|---|---|---|---|
| **CAM-001** | The camera SHALL function as a stateless observer, reading orientation from the World Simulation and emitting view/projection matrices. | High | Code Review | Vol IV |
| **CAM-002** | The camera controller SHALL dynamically scale pan and zoom input sensitivity relative to current altitude. | High | Automated UI Test | Vol IV |
| **CAM-003** | The system SHALL implement a trajectory generator for "Fly-To" actions that arcs altitude proportionally to the distance traveled. | High | Visual Inspection | Vol IV |
| **CAM-004** | The camera state machine SHALL permit immediate interruption of any programmatic animation by manual user input. | High | Automated UI Test | Vol IV |
| **CAM-005** | The camera SHALL enforce altitude and collision constraints continuously, preventing penetration of the planet's surface. | Critical | Unit Test | Vol IV |
| **CAM-006** | The camera's idle state SHALL remain mathematically anchored to the Earth's surface, accounting natively for planetary rotation. | Critical | Unit Test | Vol IV |
| **CAM-007** | The camera SHALL utilize double-precision or relative-to-center mathematical techniques to prevent floating-point jitter at surface level. | High | Visual Inspection | Vol IV |
| **CAM-008** | The camera architecture SHALL be cleanly decoupled from browser DOM events, accepting abstract input intents instead. | Medium | Code Review | Vol IV |
| **CAM-009** | All manual camera maneuvers SHALL be fully achievable via standard keyboard input for accessibility. | High | Manual QA | Vol IV |
| **CAM-010** | The camera SHALL broadcast its current view frustum to support downstream data streaming and culling optimizations. | High | Integration Test | Vol IV |
