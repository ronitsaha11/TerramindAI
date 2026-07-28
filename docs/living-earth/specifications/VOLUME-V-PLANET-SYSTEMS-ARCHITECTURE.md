# TerraMind Living Earth Experience

**Volume V: Planet Systems Architecture**

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
- Volume VI: Space Systems
- Volume VII: Streaming & Transition
- Volume VIII: Performance
- Volume IX: Experience Choreography

---

## 1. Purpose

This volume defines the architectural specification for every planetary subsystem responsible for representing the Earth within the TerraMind platform. It delineates the ownership, boundaries, and lifecycles of distinct planetary layers—such as terrain, oceans, atmosphere, and clouds. By formalizing layer independence and structural boundaries, this architecture ensures that the planet can evolve modularly, accommodating future data sources and analytical overlays without compromising the integrity of the core simulation or rendering models.

## 2. Architectural Goals

The planetary architecture is designed to achieve the following goals:

- **Planet Consistency:** All planetary layers must co-exist within a unified coordinate system and scale, avoiding visual overlaps, gaps, or z-fighting.
- **Scientific Realism:** The structural representation of the planet must adhere to established geodesic and physical models (e.g., WGS84).
- **Layer Independence:** Distinct planetary systems (e.g., ocean surfaces vs. cloud volumes) must be developed, tested, and scaled independently without hardcoded cross-dependencies.
- **Modular Evolution:** The architecture must readily support the introduction of new planetary layers (e.g., dynamic snow cover, vegetation) without refactoring the foundational Earth entity.

## 3. Planet Principles

- **Earth is continuous.**
  - *Description:* The planet exists as a seamless globe.
  - *Motivation:* Prevents the appearance of "seams" or edges when navigating at high altitudes or crossing the dateline.
  - *Architectural implications:* All planetary systems must natively support spherical wrapping and continuous geometric representation.

- **Planet owns planetary data.**
  - *Description:* The Earth entity is the central orchestrator for all static and semi-static planetary layers.
  - *Motivation:* Centralizes the management of planetary assets and memory budgets.
  - *Architectural implications:* Rendering and simulation modules query the Planet entity to discover what environmental layers exist.

- **Terrain is independent.**
  - *Description:* Topography and surface elevation are managed as an isolated system.
  - *Motivation:* Allows high-resolution elevation data to be streamed or swapped without affecting oceans or clouds.
  - *Architectural implications:* Terrain provides an altitude querying interface to other systems, but does not own them.

- **Ocean is independent.**
  - *Description:* Water bodies are treated as a distinct systemic layer, separate from the underlying bathymetry.
  - *Motivation:* Facilitates procedural water simulation and specialized specular rendering logic.
  - *Architectural implications:* The Ocean system must cleanly overlay the Terrain system without requiring unified mesh generation.

- **Atmosphere is independent.**
  - *Description:* The volumetric gas envelope surrounding the planet is an isolated system.
  - *Motivation:* Allows precise tuning of atmospheric scattering physics independent of surface materials.
  - *Architectural implications:* The Atmosphere system evaluates solely against the simulation sun vector and camera altitude.

- **Clouds are independent.**
  - *Description:* Cloud cover exists as a decoupled system hovering above the terrain and oceans.
  - *Motivation:* Enables future transitions from static cloud imagery to dynamic, volumetric cloud simulations.
  - *Architectural implications:* The Cloud system must manage its own distinct LOD and streaming budgets.

- **Night illumination is independent.**
  - *Description:* City lights and dark-side shading are managed separately from daytime albedo.
  - *Motivation:* Ensures that localized emissive data can be updated without replacing base satellite imagery.
  - *Architectural implications:* Night lights are treated as an emissive overlay tightly coupled to the simulation's sun vector.

## 4. Planet Components

The architecture delegates responsibilities to the following discrete components:

- **Earth:** The root composite entity. Orchestrates the initialization, lifecycle, and memory budgets of all child planetary systems.
- **Terrain:** Manages the geometric representation of the planet's solid surface, including elevation modeling (DEM) and primary imagery draping.
- **Ocean:** Manages the mathematical and visual representation of sea level, procedural wave generation, and water masking.
- **Atmosphere:** Manages the parameters and boundaries of the planetary atmosphere, defining scattering coefficients and density distributions.
- **Cloud Layer:** Manages global cloud coverage maps, weather-related visual obstructions, and their respective shadows.
- **Night Lights:** Manages emissive data sets representing human activity, evaluating intensity based on the local solar terminator.
- **Surface Materials:** Manages physical surface properties (roughness, metallicity) across different biomes, ensuring accurate lighting evaluation.
- **Coordinate Systems:** The mathematical foundation converting geodetic coordinates (longitude, latitude, altitude) into Cartesian space (ECEF/Cartesian 3D) for the rendering and simulation layers.

## 5. Component Relationships

Interactions between planetary components are strictly defined to prevent tight coupling:

- **Terrain & Ocean:** The Ocean system overlays the Terrain system, utilizing masks or depth tests to prevent rendering water under mountains, but they do not share unified meshes.
- **Atmosphere & Terrain/Ocean:** The Atmosphere system envelopes the surface components. Surface components rely on atmospheric scattering output to correctly shade distant objects.
- **Clouds & Surface:** The Cloud system projects shadows down onto the Terrain and Ocean systems based on the simulation sun vector.
- **Earth & All Components:** The root Earth component acts as the central registry, instantiating and suspending child components based on streaming budgets and camera proximity.

## 6. Architectural Boundaries

Planet Systems maintain clear boundaries with external architectures:

- **Interaction with Simulation (Volume II):** Planet Systems consume read-only time, rotation, and solar vector snapshots to determine local lighting conditions and dynamic state.
- **Interaction with Rendering (Volume III):** Planet Systems provide declarative structures (e.g., coordinate bounds, material parameters) to the rendering pipelines. They do not execute WebGL calls.
- **Interaction with Space (Volume VI):** Planet Systems end at the upper atmospheric boundary. The Space system takes over for celestial bodies and starfields beyond this threshold.
- **Interaction with Streaming (Volume VII):** Planet Systems define the data they need (e.g., "Terrain needs LOD 4 at this coordinate"), which the Streaming architecture fetches and resolves.
- **Interaction with Camera (Volume IV):** Planet Systems provide elevation data to the Camera to enforce collision constraints, but they do not control camera movement.

## 7. Planet Lifecycle

The Planet Systems undergo a defined lifecycle conceptually managed by the root Earth component:

- **Initialization:** Coordinate systems are established, memory boundaries are defined, and placeholder/low-resolution assets are loaded to provide an immediate global view.
- **Active:** The planetary layers actively consume simulation state and streaming data, updating their properties and boundaries dynamically as time progresses.
- **Streaming:** Individual layers actively request higher-resolution tiles or geometry as the camera approaches, swapping assets asynchronously to avoid blocking the main thread.
- **Suspended:** Layers (or specific geographic sectors of layers) that fall outside the camera's frustum or are occluded are marked as suspended, freeing processing resources while remaining in memory.
- **Shutdown:** Data caches are flushed, memory buffers are explicitly released, and component relationships are severed.

## 8. Quality Attributes

- **Performance:** Planet Systems must rigidly enforce culling and LOD rules to ensure that high-resolution data is only processed when visually necessary.
- **Scalability:** The architecture must effortlessly support the loading of terabytes of planetary data by isolating data management into the Streaming system.
- **Reliability:** Missing or corrupted terrain/imagery tiles must be handled gracefully, falling back to lower-resolution data without crashing the subsystem.
- **Scientific Credibility:** All planetary components must accurately reflect physical models, particularly regarding the WGS84 ellipsoid and atmospheric physics.
- **Maintainability:** Isolating systems (e.g., making Clouds independent from Terrain) ensures that rendering enhancements to one layer do not require refactoring another.

## 9. Risks

- **Layer Coupling:** 
  - *Risk:* Hardcoding terrain logic into ocean rendering, making it impossible to update ocean physics without breaking landmasses.
  - *Mitigation:* Enforce strict Interface Segregation between environmental layers.
- **Coordinate Drift:** 
  - *Risk:* Discrepancies between WebGL 32-bit floats and real-world 64-bit coordinates causing visual shaking at the surface.
  - *Mitigation:* Mandate relative-to-center (RTC) or similar high-precision coordinate transformation architectures natively within the Coordinate System component.
- **Duplicate Ownership:** 
  - *Risk:* Both the Camera and the Terrain attempting to manage frustum culling.
  - *Mitigation:* Clarify that Camera defines the frustum; Planet Systems consume it to cull their own data.
- **Visual Inconsistency:** 
  - *Risk:* Clouds responding to a different sun vector than the terrain, breaking shadows.
  - *Mitigation:* All planetary systems must draw their environmental state strictly from the centralized World Simulation snapshot.

## 10. Summary

The Planet Systems Architecture establishes the structural foundation of the digital Earth. By enforcing strict layer independence, centralizing coordinate mathematics, and decoupling data management from rendering, TerraMind ensures that the planet remains mathematically precise, visually consistent, and infinitely scalable as new environmental intelligence layers are introduced.

---

## Implementation Requirements

The following requirements mandate the formal engineering outcomes for the Planet Systems architecture.

| ID | Description | Priority | Verification | Source Volume |
|---|---|---|---|---|
| **PLN-001** | The architecture SHALL model the Earth as a continuous, mathematically accurate ellipsoid (e.g., WGS84). | Critical | Code Review / Unit Test | Vol V |
| **PLN-002** | Terrain, Ocean, Atmosphere, and Cloud systems SHALL operate as completely independent modules without tight coupling. | High | Code Review | Vol V |
| **PLN-003** | The planetary coordinate system SHALL natively support 64-bit precision to eliminate spatial jitter at ground level. | Critical | Visual Inspection / Unit Test | Vol V |
| **PLN-004** | The Terrain system SHALL expose an asynchronous altitude query interface for collision detection by the Camera. | High | Integration Test | Vol V |
| **PLN-005** | The Night Lights emissive layer SHALL dynamically evaluate its intensity against the localized solar terminator provided by the simulation. | Medium | Visual Inspection | Vol V |
| **PLN-006** | All Planet Systems SHALL consume the unified View/Projection frustum from the Camera to execute internal culling logic. | High | Profiling | Vol V |
| **PLN-007** | Planet Systems SHALL NOT directly execute network requests; all asset fetching SHALL delegate to the Streaming architecture. | High | Code Review | Vol V |
| **PLN-008** | The Root Earth component SHALL act as the central orchestrator for the initialization and suspension of all child planetary layers. | Medium | Unit Test | Vol V |
| **PLN-009** | Missing or corrupted planetary data tiles SHALL gracefully fall back to lower-resolution data without crashing the system. | High | Manual QA | Vol V |
| **PLN-010** | The Ocean system SHALL mathematically evaluate the simulation sun vector to present physically accurate specular reflections. | Medium | Visual Inspection | Vol V |
