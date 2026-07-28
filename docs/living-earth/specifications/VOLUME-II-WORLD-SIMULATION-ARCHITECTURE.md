# TerraMind Living Earth Experience

**Volume II: World Simulation Architecture**

- **Version:** 1.0.0
- **Status:** DRAFT
- **Phase:** 11.5
- **Last Updated:** 2026-07-28

**Dependencies:**
- Living Earth Master Plan
- Volume I: Vision & Product Philosophy

**Influences:**
- Volume III: Rendering
- Volume IV: Camera
- Volume V: Planet Systems
- Volume VI: Space Systems
- Volume VII: Streaming & Transition
- Volume VIII: Performance
- Volume IX: Experience Choreography

---

## 1. Purpose

This volume defines the architectural model for TerraMind's world simulation layer. The simulation architecture serves as the centralized, authoritative source of world state. It provides the timing, environmental variables, and celestial orientations necessary to breathe life into the digital Earth. By establishing a rigid, decoupled simulation core, we ensure that rendering, camera, and application logic remain stateless consumers, resulting in a predictable, stable, and highly performant platform.

## 2. Architectural Goals

The world simulation layer is designed to achieve the following architectural goals:

- **Deterministic Behavior:** The state of the world at any given simulation time must be identical across identical inputs, ensuring predictable and replayable experiences.
- **Continuous Simulation:** The simulation must progress steadily and autonomously, free from UI-induced pauses or frame drops.
- **Loose Coupling:** The simulation layer must not possess any knowledge of how its state is rendered or how the camera observes it.
- **Extensibility:** The architecture must readily accommodate future dynamic layers (e.g., weather, orbits, traffic) without structural refactoring.
- **Predictability:** State transitions and time progression must follow strict mathematical models.
- **Testability:** The entire simulation layer must be capable of running headlessly in a Node.js environment without WebGL or DOM dependencies.

## 3. Core Principles

- **Simulation is the source of truth.**
  - *Description:* All environmental states (time of day, rotation, atmospheric conditions) originate exclusively from the simulation layer.
  - *Motivation:* Prevents state drift and conflicting values across different subsystems.
  - *Architectural implications:* The rendering layer must only read state, never modify it.

- **Rendering consumes simulation state.**
  - *Description:* Visual output is a pure function of the current simulation state.
  - *Motivation:* Ensures scientific credibility and strict separation of concerns.
  - *Architectural implications:* Shaders and geometry engines require strict, typed data interfaces from the simulation layer.

- **Time advances independently of rendering.**
  - *Description:* Simulation time is computed using delta time, completely detached from the display frame rate.
  - *Motivation:* A drop in frame rate must not cause the simulation to slow down or lag.
  - *Architectural implications:* The simulation tick loop must safely accommodate varying frame durations.

- **User interaction influences but does not own simulation.**
  - *Description:* While users may adjust simulation speed or pause time, they do not own the simulation loop itself.
  - *Motivation:* The world must continue to exist and evolve even when the user is passive.
  - *Architectural implications:* User events dispatch intent to the simulation controller, which applies changes at the next valid tick.

- **Simulation remains active while the application is idle.**
  - *Description:* Even with zero user input, the simulation clock continues to tick and update environmental parameters.
  - *Motivation:* Reinforces the "living ecosystem" product philosophy.
  - *Architectural implications:* The background loop must be highly optimized to prevent idle battery drain on mobile devices.

## 4. System Responsibilities

The simulation layer is strictly responsible for the following domains:

- **World Time:** Tracking absolute simulation time, delta time, elapsed time, and time-scale multipliers.
- **Global State:** Managing top-level planetary variables (e.g., global planetary rotation angle).
- **Celestial State:** Computing the relative positions of celestial bodies (e.g., Sun position vector relative to the Earth).
- **Environmental State:** Tracking global environmental variables (e.g., baseline atmospheric density, global illumination intensity).
- **Simulation Lifecycle:** Managing the start, pause, resume, and shutdown phases of the simulation tick loop.
- **Event Coordination:** Broadcasting tick events and state updates to registered downstream consumers (Renderers, Planet Systems, UI).

## 5. Architectural Boundaries

The simulation layer maintains strict boundaries with adjacent systems:

- **Rendering (Volume III):** The simulation layer provides an immutable snapshot of current state (e.g., sun vector, rotation angle) per frame. It possesses zero knowledge of shaders, WebGL, or draw calls.
- **Camera (Volume IV):** The camera calculates its matrix based on the Earth's orientation provided by the simulation. The simulation does not know where the camera is looking.
- **Planet Systems (Volume V):** Planet systems (Oceans, Atmosphere) consume simulation variables (time, lighting angle) to calculate their local procedural behaviors.
- **Space Systems (Volume VI):** Space systems query the simulation for celestial time and orientation to position the skybox and starfields.
- **Streaming (Volume VII):** The streaming engine may use simulation state (e.g., camera location combined with planetary rotation) to preemptively load data, but the simulation itself performs no IO.
- **UI:** The UI subscribes to simulation state to display time or controls, and sends intents to adjust time scales. The simulation layer is completely UI-agnostic.

## 6. Lifecycle Model

The simulation operates within a defined lifecycle model:

- **Initialization:** The simulation allocates memory, zeroes out state, applies initial configuration (e.g., start time, scale), but time does not progress.
- **Running:** The core tick loop is active. Delta time is computed, state is updated, and snapshots are broadcasted to consumers.
- **Paused:** The tick loop remains active to broadcast static state snapshots, but delta time is forced to zero. The environment freezes, but downstream consumers continue to receive frames.
- **Resumed:** Time progression is restored. Delta time computation smoothly restarts without introducing large time jumps.
- **Shutdown:** The tick loop is terminated, memory is freed, and event broadcasters are destroyed.

## 7. Time Model

The concept of time within the simulation architecture is distinct from real-world time:

- **Continuous Progression:** Time flows mathematically forward based on elapsed real-world milliseconds multiplied by a configurable time scale.
- **Separation from Frame Rate:** The delta time injected into state calculations is derived from high-resolution timers (e.g., `performance.now()`), ensuring consistency whether running at 30fps or 144fps.
- **Consistency:** All subsystems receive the exact same timestamp and delta time for a given tick, preventing race conditions or visual tearing between systems (e.g., shadows moving out of sync with rotation).
- **Pause/Resume Concepts:** Pausing the simulation only affects the accumulation of simulation time; the internal tick loop continues to dispatch zero-delta frames to keep the renderer alive.
- **Configurability:** The time scale must be dynamically adjustable (e.g., 1x, 10x, 1000x real-time) to allow accelerated environmental observation.

## 8. Quality Attributes

- **Reliability:** The tick loop must gracefully handle browser tab backgrounding and throttling without causing catastrophic time jumps upon foregrounding.
- **Predictability:** Given the same start time and delta steps, celestial and planetary states must yield identical outputs.
- **Scalability:** The state snapshot broadcasting mechanism must support numerous subscribers (e.g., multiple planet systems) efficiently.
- **Maintainability:** Pure mathematical functions must be separated from state management logic.
- **Testability:** The core engine must execute deterministically in unit tests without requiring a browser context.
- **Observability:** Current simulation time, delta time, and tick duration must be easily exposable to performance profiling tools.

## 9. Architectural Risks

- **Tight Coupling:** 
  - *Risk:* Passing rendering contexts (WebGL/Deck.gl) directly into the simulation loop.
  - *Mitigation:* Enforce strict Interface Segregation. The simulation only returns raw numbers and vectors.
- **Multiple Sources of Truth:** 
  - *Risk:* Planet systems maintaining their own internal clocks that drift from the main simulation.
  - *Mitigation:* Downstream systems must accept time as a parameter from the central tick event, rather than calculating it locally.
- **Frame-Dependent Logic:** 
  - *Risk:* State updates that multiply by a hardcoded frame rate instead of delta time.
  - *Mitigation:* All physics and rotation math must explicitly integrate using the provided `deltaTime`.
- **Hidden State:** 
  - *Risk:* Modifying simulation variables outside of the designated tick update phase.
  - *Mitigation:* Expose state to consumers exclusively via immutable snapshots or read-only properties.
- **Performance Bottlenecks:** 
  - *Risk:* Garbage collection spikes caused by allocating thousands of state snapshot objects per second.
  - *Mitigation:* Utilize pre-allocated object pools, flat arrays, or zero-allocation mutation patterns for state propagation.

## 10. Summary

The World Simulation Architecture forms the beating heart of the Living Earth Experience. By strictly isolating the progression of time and the calculation of global state from the complexities of rendering and presentation, TerraMind guarantees a stable, deterministic, and highly extensible platform. This centralized source of truth enables a cohesive and mathematically precise ecosystem.

---

## Implementation Requirements

The following formal implementation requirements authorize future engineering work. All implementation sprints must fulfill and trace back to these IDs.

- **SIM-001 (Core Clock):** The system SHALL implement a centralized simulation clock that tracks absolute simulation time, delta time, and elapsed real time using a high-resolution timer.
- **SIM-002 (Tick Loop):** The system SHALL implement a continuous tick loop that executes independently of user interaction.
- **SIM-003 (Time Independence):** State calculations SHALL utilize delta time to ensure behavior remains consistent regardless of hardware frame rate.
- **SIM-004 (State Immutability):** The simulation SHALL provide downstream consumers with an immutable, read-only snapshot of the current state per tick.
- **SIM-005 (Time Scaling):** The system SHALL support dynamic adjustments to the time scale (including zero for pausing) without disrupting the tick loop execution.
- **SIM-006 (Event Broadcasting):** The system SHALL provide a performant, zero-allocation publish/subscribe mechanism for broadcasting tick events to registered observers.
- **SIM-007 (Headless Execution):** The simulation engine SHALL be completely decoupled from the DOM and WebGL, allowing execution in headless Node.js environments.
- **SIM-008 (Background Recovery):** The simulation SHALL detect extreme delta times caused by browser tab throttling and clamp them to prevent catastrophic state jumps upon tab foregrounding.
- **SIM-009 (Celestial Vector):** The simulation SHALL compute and expose a continuous sun position vector based on the current simulation time.
- **SIM-010 (Earth Rotation):** The simulation SHALL compute and expose the Earth's rotational angle based on elapsed simulation time.
