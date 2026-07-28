# TerraMind Living Earth Experience

**Volume VII: Streaming & Transition Architecture**

- **Version:** 1.0.0
- **Status:** DRAFT
- **Phase:** 11.5
- **Last Updated:** 2026-07-28

**Dependencies:**
- Living Earth Master Plan
- Volume I: Vision & Product Philosophy
- Volume II: World Simulation Architecture
- Volume III: Rendering Architecture
- Volume IV: Camera & Navigation
- Volume V: Planet Systems
- Volume VI: Space Systems

**Influences:**
- Volume VIII: Performance & Scalability
- Volume IX: Experience Choreography

---

## 1. Purpose

This volume establishes the architectural specification for how TerraMind continuously delivers, updates, and transitions world content. The Streaming Architecture acts as the logistical nervous system of the Living Earth Experience. It is responsible for ensuring that the world feels continuously available by coordinating data delivery, progressive refinement, and seamless level-of-detail (LOD) transitions. Crucially, streaming does not own the simulation, nor does it own the rendering logic; it simply coordinates the availability of geospatial data so that exploration is never interrupted by loading screens.

## 2. Architectural Goals

The Streaming & Transition Architecture is designed to achieve the following goals:

- **Seamless Exploration:** The user must be able to navigate the entire globe without encountering hard loading pauses or freezing frames.
- **Progressive Refinement:** Visual clarity should increase gradually as high-resolution data becomes available, maintaining spatial context at all times.
- **Continuous World Availability:** Even during severe bandwidth restrictions, a base level of planetary context must always remain visible.
- **Predictable Transitions:** Changes in Level of Detail or data layers must interpolate smoothly, avoiding geometric "popping" or jarring visual shifts.
- **Graceful Degradation:** The architecture must handle missing, delayed, or corrupted data without crashing the renderer or simulation.
- **Scalability:** The system must efficiently manage the asynchronous fetching of terabytes of planetary data by resolving requests strictly based on the camera's viewport.
- **Extensibility:** The caching and streaming pipeline must support diverse future data types (e.g., volumetric clouds, dynamic traffic) through a unified resource interface.
- **Reliability:** Background loading operations must never block the main simulation or rendering threads.

## 3. Streaming Principles

- **The user should never wait for the world.**
  - *Description:* The UI should never display a blocking "Loading" screen during spatial navigation.
  - *Motivation:* Waiting breaks immersion and disrupts the feeling of a living planet.
  - *Architectural implications:* Low-resolution proxy geometry and textures must be presented immediately while higher-resolution data streams in asynchronously.

- **Streaming supports exploration rather than interrupts it.**
  - *Description:* Data fetching happens in the background, governed by the camera's movement.
  - *Motivation:* The user's focus should remain on the intelligence, not on the platform's data mechanics.
  - *Architectural implications:* Network requests and cache decompression must occur off the main thread (e.g., via Web Workers).

- **Loading shall be progressive.**
  - *Description:* Data resolution increases incrementally as the camera zooms in.
  - *Motivation:* Prevents massive bandwidth spikes and provides immediate, albeit blurry, visual feedback.
  - *Architectural implications:* The architecture mandates a hierarchical spatial index (e.g., Quadtree) for data requests.

- **Streaming shall never become the source of truth.**
  - *Description:* Streaming merely fetches what the Planet Systems request based on the simulation state.
  - *Motivation:* Prevents streaming logic from accidentally attempting to determine simulation time or weather states.
  - *Architectural implications:* Streaming services accept deterministic resource URIs and bounding boxes as inputs; they do not calculate them.

- **Missing data shall degrade gracefully.**
  - *Description:* If a high-resolution tile fails to load, the system retains the lower-resolution parent tile indefinitely.
  - *Motivation:* A blurry mountain is infinitely better than a transparent void.
  - *Architectural implications:* The rendering layer must hold references to parent nodes until child nodes report a "ready for presentation" state.

- **Transitions preserve spatial continuity.**
  - *Description:* When swapping LODs, the transition must be visually smoothed.
  - *Motivation:* Abrupt geometry popping destroys the illusion of scale and altitude.
  - *Architectural implications:* The renderer and streaming system must coordinate cross-fading or dithering during tile replacements.

- **Prefetching should anticipate movement without changing simulation.**
  - *Description:* The streaming architecture may fetch data adjacent to the camera's current trajectory before it enters the frustum.
  - *Motivation:* Prevents visual pop-in during fast pans or Fly-To maneuvers.
  - *Architectural implications:* The streaming layer requires a predictive vector from the Camera architecture but does not influence the camera itself.

## 4. Responsibilities

The Streaming Architecture is exclusively responsible for coordinating:

- **Terrain Data Availability:** Fetching and caching digital elevation models.
- **Imagery Availability:** Fetching and caching base satellite/aerial imagery maps.
- **Asset Availability:** Delivering static 3D models or environmental textures.
- **LOD Coordination:** Managing the hierarchy of loaded tiles to ensure memory budgets are respected.
- **Cache Coordination:** Orchestrating in-memory and persistent storage to prevent redundant network requests.
- **Transition Orchestration:** Signaling the Rendering architecture when a new LOD is fully ready to be blended into the scene.
- **Prefetch Coordination:** Prioritizing network requests based on camera trajectory and velocity.
- **Content Lifecycle Management:** Safely evicting off-screen or occluded data to prevent memory exhaustion.

## 5. Architectural Boundaries

To maintain platform stability, the streaming layer operates within strict boundaries:

**Streaming owns:**
- Content availability (fetching, decoding).
- Progressive refinement state management (tracking which LODs are loaded).
- Transition coordination (signaling readiness).

**Streaming does NOT own:**
- Simulation state (Time, Sun position).
- Rendering logic (Shaders, Draw calls, Dithering math).
- Camera intent (Determining where the user wants to go).
- Planet logic (Determining how the Earth wraps or generates meshes).
- Space logic (Determining star placement).

**Interactions:**
- **Simulation (Vol II):** Streaming may listen to simulation time to evict stale dynamic data, but it does not modify the clock.
- **Rendering (Vol III):** Streaming delivers data payloads to the GPU buffers. Rendering executes the visual fade based on Streaming's readiness signal.
- **Camera (Vol IV):** Streaming continuously consumes the camera's view frustum and velocity vector to prioritize data requests.
- **Planet Systems (Vol V):** Planet systems define the spatial grid (e.g., Quadtree). Streaming satisfies the data requirements for that grid.
- **Space Systems (Vol VI):** Streaming delivers high-resolution celestial catalogs upon initialization.
- **Performance (Vol VIII):** Streaming throttles its concurrent requests and cache limits based on Performance layer budgets.
- **User Interface:** The UI may display discrete loading indicators (e.g., a subtle spinner) derived from streaming queues, but it does not control the queue.

## 6. Conceptual Streaming Lifecycle

Data within the TerraMind platform conceptually follows this lifecycle:

1. **Initialization:** The application launches. Global, low-resolution base maps are immediately loaded from local cache to establish the initial planetary context.
2. **Discovery:** As the camera moves, Planet Systems evaluate the frustum and generate a list of required spatial indices (tiles).
3. **Prefetch:** The Streaming layer predicts camera trajectory and queues spatial indices slightly outside the current frustum at low priority.
4. **Streaming:** The Streaming layer dispatches network or local storage requests for the visible spatial indices via background workers.
5. **Refinement:** The payload is decoded. The Streaming layer signals the Renderer that a higher-resolution tile is ready for transition.
6. **Retention:** The tile remains in active memory as long as it intersects the frustum or remains in the immediate prefetch neighborhood.
7. **Eviction:** When the camera moves away, or memory budgets are exceeded, the Streaming layer purges the tile from active memory, retaining it in a local LRU cache.
8. **Shutdown:** All active network requests are aborted, and background workers are terminated cleanly.

## 7. Transition Architecture

The concept of a Transition bridges the gap between Streaming (data availability) and Rendering (visual presentation):

- **Zoom Transitions:** As the user zooms in, parent tiles must smoothly cross-fade into child tiles. The Streaming layer guarantees that all child tiles are fully decoded in memory before signaling the Renderer to begin the fade.
- **Camera Movement Transitions:** Fast pans across the surface require prioritizing the loading of the camera's leading edge over the trailing edge.
- **LOD Transitions:** Geometric LOD swaps (e.g., terrain meshes) must utilize geomorphing or dithering to prevent the horizon from suddenly shifting altitude.
- **Planetary Transitions:** Switching from daytime imagery to night-time emissive layers must interpolate based on the Simulation's terminator line, avoiding hard toggles.
- **Visual Continuity:** Under no circumstances should a high-resolution tile replace a low-resolution tile instantly if it causes a jarring frame discontinuity.
- **Fade Philosophy:** Fading is a rendering responsibility, but it is purely orchestrated by the Streaming layer's readiness state machine.

## 8. Content Availability Model

TerraMind conceptualizes world content as a progressively refined mosaic rather than a single monolithic asset:

- **Progressive Availability:** The Earth is always visible. Resolution is merely a function of time and bandwidth.
- **Partial Availability:** If a specific geographic tile fails to load (e.g., server 404), its siblings will continue to refine while the failed tile falls back to its parent's resolution.
- **Deferred Refinement:** The system will not request maximum resolution for a region until camera motion has settled, saving bandwidth during rapid Fly-To maneuvers.
- **Visual Placeholders:** The lowest available LOD always acts as a visual placeholder. Blank geometry is considered an architectural failure.
- **Data Consistency:** Terrain elevation and surface imagery must be synchronized; imagery should not refine to LOD 10 if terrain is stuck at LOD 2, preventing visual distortion.
- **Recovery:** Transient network errors automatically retry with exponential backoff, silently repairing the mosaic without user intervention.

## 9. Quality Attributes

- **Reliability:** The streaming queue must never deadlock, even when inundated with thousands of tile requests during extreme camera maneuvers.
- **Predictability:** Network bandwidth should be saturated smoothly, avoiding sudden spikes that could impact other web platform activities.
- **Responsiveness:** Tile decoding (e.g., parsing geometry) must not block the main JavaScript thread, ensuring the camera remains 100% responsive.
- **Performance Awareness:** The architecture must adhere to strict memory budgets, aggressively evicting stale data.
- **Scalability:** The tile registry must support traversing infinitely deep Quadtrees without performance degradation.
- **Maintainability:** Network fetching logic must be strictly abstracted from decoding logic to allow easy swapping of protocols or formats in the future.
- **Extensibility:** The system must seamlessly support streaming abstract vector data (e.g., flight paths) alongside raster imagery using the same spatial lifecycle.
- **Fault Tolerance:** Corrupted payloads must be caught, discarded, and gracefully handled without crashing the render loop.

## 10. Architectural Risks

- **Blocking Operations:**
  - *Risk:* Heavy JSON parsing or geometry generation occurring on the main thread, causing camera stutter.
  - *Mitigation:* Mandate the use of Web Workers or off-thread decoding for all incoming streaming payloads.
- **Cache Inconsistency:**
  - *Risk:* Retaining stale imagery tiles while adjacent tiles load newer versions, resulting in visible seams.
  - *Mitigation:* Cache keys must incorporate dataset version hashes to ensure temporal consistency across tiles.
- **Transition Discontinuity:**
  - *Risk:* The renderer swapping a tile before its texture is fully uploaded to the GPU, causing a black flash.
  - *Mitigation:* The Streaming layer must explicitly verify GPU upload completion before signaling the Transition state.
- **Duplicate Ownership:**
  - *Risk:* The Terrain system attempting to fetch its own tiles directly, bypassing the Streaming layer's priority queue.
  - *Mitigation:* Enforce strict dependency injection; Planet Systems only request coordinates, Streaming handles the delivery.
- **Resource Exhaustion:**
  - *Risk:* Panning the camera quickly accumulates thousands of pending network requests, exhausting browser limits.
  - *Mitigation:* The Streaming architecture must implement request cancellation for tiles that exit the frustum before their download completes.
- **Visible Loading Artifacts:**
  - *Risk:* A high-resolution tile appearing instantly over a blurry background, jarring the user.
  - *Mitigation:* The Architecture mandates cross-fade rendering orchestrated by streaming readiness.

## 11. Summary

The Streaming & Transition Architecture ensures that TerraMind delivers a continuous, immersive exploration experience. By isolating data delivery from simulation and rendering, maintaining progressive LOD hierarchies, and enforcing graceful degradation, the platform guarantees that the user never waits for the world. Streaming provides the logistical foundation required for a living, infinitely scalable digital Earth.

---

## Implementation Requirements

| Requirement ID | Description | Priority | Verification Method | Source Volume |
|---|---|---|---|---|
| **STR-001** | The Streaming architecture SHALL evaluate requests strictly based on the view frustum and velocity provided by the Camera architecture. | Critical | Unit Test / Integration | Vol VII |
| **STR-002** | The system SHALL implement progressive refinement, always displaying a lower-resolution parent asset while a child asset is loading. | High | Visual Inspection | Vol VII |
| **STR-003** | Data decoding and parsing SHALL occur asynchronously off the main thread to prevent UI or Camera stuttering. | Critical | Profiling | Vol VII |
| **STR-004** | The architecture SHALL orchestrate smooth visual transitions (cross-fading or dithering) when swapping LODs. | High | Visual Inspection | Vol VII |
| **STR-005** | The Streaming layer SHALL gracefully degrade to the nearest available LOD if a network request fails, without crashing the renderer. | High | Automated UI Test | Vol VII |
| **STR-006** | The system SHALL actively cancel pending network requests for spatial regions that exit the camera frustum prior to download completion. | Medium | Network Profiling | Vol VII |
| **STR-007** | The Streaming architecture SHALL NOT directly modify rendering state or simulation time. | High | Code Review | Vol VII |
| **STR-008** | The architecture SHALL synchronize the loading of terrain geometry and surface imagery to prevent extreme LOD mismatches. | Medium | Visual Inspection | Vol VII |
| **STR-009** | The system SHALL implement a memory-aware eviction policy (e.g., LRU) to purge off-screen data while respecting predefined limits. | High | Memory Profiling | Vol VII |
| **STR-010** | The Streaming layer SHALL explicitly verify that data is fully uploaded to GPU memory before signaling the Renderer to initiate a transition. | Critical | Architecture Review | Vol VII |

---

## Cross-Volume Traceability

The Streaming & Transition Architecture coordinates heavily with other Living Earth systems without dictating their internal logic:

- **World Simulation (Vol II):** Streaming listens to simulation time to manage the invalidation of dynamic (time-sensitive) data layers.
- **Rendering (Vol III):** Streaming acts as the data provider. Rendering executes the visual fade transitions dictated by the Streaming layer's readiness signals.
- **Camera (Vol IV):** Streaming continuously consumes the Camera's frustum and velocity to drive spatial querying, prefetching, and priority sorting.
- **Planet Systems (Vol V):** Planet Systems define the mathematical structure of the Earth (e.g., Quadtree geometry); Streaming fills that structure with data.
- **Space Systems (Vol VI):** Streaming manages the initial background loading of high-resolution celestial catalogs during platform startup.
- **Performance (Vol VIII):** Streaming accepts memory and network bandwidth budgets from the Performance layer, strictly curtailing its operations to maintain 60FPS.
- **Experience Choreography (Vol IX):** Streaming informs the Choreography layer of overarching loading progress, allowing the UI to display subtle, non-blocking contextual feedback.
