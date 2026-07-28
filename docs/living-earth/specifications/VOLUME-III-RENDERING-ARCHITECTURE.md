# TerraMind Living Earth Experience

**Volume III: Rendering Architecture**

- **Version:** 1.0.0
- **Status:** DRAFT
- **Phase:** 11.5
- **Last Updated:** 2026-07-28

**Dependencies:**
- Living Earth Master Plan
- Volume I: Vision & Product Philosophy
- Volume II: World Simulation Architecture

**Influences:**
- Volume IV: Camera & Navigation
- Volume V: Planet Systems
- Volume VI: Space Systems
- Volume VII: Streaming & Transition
- Volume VIII: Performance
- Volume IX: Experience Choreography

---

## 1. Purpose

This volume defines the architectural model for TerraMind's rendering layer. The rendering architecture is strictly responsible for transforming the numerical state produced by the World Simulation into visual representations. It defines the conceptual pipeline, renderer hierarchy, scene composition model, and lighting philosophy required to generate the Living Earth Experience. Most critically, this document establishes that the rendering layer is a stateless consumer; it presents world information but never owns it.

## 2. Architectural Goals

The rendering architecture is designed to achieve the following goals:

- **Visual Consistency:** Ensuring all rendering subsystems (oceans, atmosphere, terrain, data) share a unified lighting model, coordinate space, and depth composition.
- **Scientific Credibility:** Rendering must accurately portray the simulation's state through physically-based approaches rather than artistic approximations.
- **Predictable Rendering:** Given identical simulation states and camera parameters, the renderer must deterministically output identical frames.
- **Scalability:** The architecture must cleanly isolate subsystems to allow the independent introduction of new rendering layers (e.g., volumetric clouds, dynamic weather) without rewriting the core composition engine.
- **Extensibility:** Facilitating the seamless integration of external intelligence overlays alongside native environmental rendering.
- **Performance Awareness:** The architecture must aggressively enforce level-of-detail (LOD) and culling strategies early in the conceptual pipeline.
- **Loose Coupling:** Rendering systems must decouple completely from business logic, data fetching, and simulation state generation.
- **Testability:** Visual presentation logic must be structured in a way that allows independent validation of materials and composition hierarchy.

## 3. Core Principles

- **Rendering consumes simulation state.**
  - *Description:* Visual output is generated exclusively from the immutable snapshots provided by the World Simulation.
  - *Motivation:* Guarantees that what the user sees mathematically matches what the platform simulates.
  - *Architectural implications:* Renderers possess zero internal simulation loops or physics integrators.

- **Rendering is stateless with respect to world ownership.**
  - *Description:* The renderer retains no authoritative memory of environmental states between frames.
  - *Motivation:* Prevents synchronization errors between the simulation clock and the rendering loop.
  - *Architectural implications:* All world parameters (time of day, rotation angle, sun vector) must be injected into the renderer every frame.

- **Visuals reflect simulation.**
  - *Description:* Graphical effects (e.g., twilight coloring, shadow angles) are side-effects of simulation variables, not hardcoded aesthetic choices.
  - *Motivation:* Establishes trust and maintains scientific credibility.
  - *Architectural implications:* Shader uniform bindings must trace back to simulation-derived values.

- **Rendering never modifies simulation.**
  - *Description:* The rendering pipeline strictly observes; it cannot write back to the World Simulation.
  - *Motivation:* Enforces unidirectional data flow and prevents feedback loops.
  - *Architectural implications:* The rendering layer operates on read-only interfaces.

- **Consistency is prioritized over visual spectacle.**
  - *Description:* A cohesive, unified visual environment is more valuable than isolated, hyper-realistic but discordant effects.
  - *Motivation:* Visual discordance distracts from professional intelligence analysis.
  - *Architectural implications:* All subsystems must conform to a singular, shared lighting and material philosophy.

- **Smooth transitions preserve immersion.**
  - *Description:* Rendering state changes must interpolate smoothly.
  - *Motivation:* Abrupt graphical popping breaks the illusion of continuous physical space.
  - *Architectural implications:* LOD swapping and material transitions must incorporate blending or dithering mechanisms.

## 4. Rendering Responsibilities

The rendering layer is exclusively responsible for the following domains:

- **Scene Composition:** Assembling discrete visual elements (terrain, atmosphere, oceans) into a coherent, correctly ordered 3D space.
- **Lighting Application:** Evaluating global lighting parameters (sun vector, intensity) against surface materials to compute color and shadow.
- **Material Presentation:** Interpreting physical properties (roughness, albedo, normal) to render realistic surfaces.
- **Atmospheric Visualization:** Presenting volumetric scattering and atmospheric gradients based on sun position and altitude.
- **Ocean Visualization:** Presenting water surface dynamics and specular reflections.
- **Cloud Visualization:** Rendering global cloud cover layers.
- **Celestial Visualization:** Presenting the starfield, night-side illumination, and celestial bodies.
- **Terrain Presentation:** Rendering topography and base imagery maps.
- **Frame Composition:** Executing the final rasterization, post-processing, and buffer management required to present a frame to the display.

## 5. Architectural Boundaries

To prevent entanglement, the following boundaries are strictly enforced:

**Rendering owns:**
- Visual presentation (color, shading, geometry).
- Frame generation (buffer lifecycle, draw calls).
- Scene composition (depth sorting, culling).

**Rendering does NOT own:**
- Simulation state (time, rotation, environmental parameters).
- World time (delta time integration).
- Camera intent (user navigation logic).
- Environmental logic (weather patterns, celestial mechanics).

**Cross-System Interactions:**
- **World Simulation:** Provides immutable state snapshots (time, sun vector) per frame.
- **Camera:** Provides view and projection matrices per frame.
- **Planet Systems / Space Systems:** Provide declarative configurations or geometries representing environmental layers.
- **Streaming:** Provides raw data tiles (imagery, terrain, vectors) asynchronously.
- **UI:** Exists as an independent overlay rendered outside the 3D environmental context, communicating with the renderer only through state stores.

## 6. Conceptual Rendering Pipeline

The rendering architecture follows a strict, unidirectional conceptual flow:

1. **Simulation State:** The renderer receives the current immutable snapshot from the World Simulation and the matrices from the Camera.
2. **Scene Composition:** Visible entities are identified. Frustum culling and occlusion are evaluated. Entities are sorted by depth and opacity.
3. **Lighting Evaluation:** The global light source vector and ambient parameters are established for the current frame.
4. **Material Evaluation:** Visible surfaces calculate their physical interactions with the established lighting.
5. **Frame Composition:** Render targets are aggregated. Depth buffers are reconciled. Post-processing effects (e.g., anti-aliasing) are applied.
6. **Presentation:** The final composite frame is pushed to the user's display context.

## 7. Renderer Hierarchy

The architecture decomposes the rendering workload into specialized, conceptually distinct rendering components:

- **Planet Renderer:** The master composition root that aggregates all Earth-centric visual layers.
- **Atmosphere Renderer:** Responsible exclusively for volumetric scattering, sky coloring, and horizon gradients.
- **Ocean Renderer:** Responsible for presenting water surface materials, reflections, and dynamic normals.
- **Cloud Renderer:** Responsible for rendering cloud cover geometry or volumes.
- **Celestial Renderer:** Responsible for rendering the starfield background and distinct celestial bodies (e.g., Sun, Moon).
- **Terrain Renderer:** Responsible for managing and presenting the base planetary geometry, elevation models, and imagery textures.
- **Overlay Renderer:** Responsible for rendering analytical intelligence data (e.g., vectors, heatmaps, points) flawlessly integrated within the 3D depth context.

## 8. Scene Composition Model

The composition model dictates how disparate elements interact to form a unified image:

- **Layer Ordering:** Opaque terrain must evaluate before transparent layers (oceans, atmosphere) to ensure correct depth testing and prevent overdraw.
- **Visual Consistency:** All renderers must share the same depth buffer and coordinate system to prevent z-fighting and alignment issues.
- **Occlusion Concepts:** The architecture mandates strict frustum and horizon culling. Objects obscured by the planet's curvature or outside the camera's view must bypass the rendering pipeline.
- **Depth Perception:** Atmospheric scattering and haze must be consistently applied across both terrain and overlay renderers to provide accurate depth cues at a distance.
- **Spatial Coherence:** Transitions between localized data and global views must occur within a unified, continuous coordinate space.

## 9. Lighting & Material Philosophy

- **Lighting Ownership:** The rendering layer owns the *application* of lighting, but the simulation layer owns the *parameters* (sun direction, intensity). The renderer calculates the intersection of light and material.
- **Materials:** Materials represent physical properties, not fixed colors. They must respond predictably to changing lighting conditions.
- **Shadows:** Shadow evaluation is a rendering responsibility derived from simulation light vectors.
- **Reflections:** Specular highlights and reflections (e.g., oceans) must be dynamically derived from the unified light source.
- **Visual Consistency:** A single, physically-based lighting model must be enforced across all renderers (Terrain, Ocean, Clouds) to ensure a cohesive visual ecosystem.

## 10. Quality Attributes

- **Performance:** The pipeline must rigidly enforce culling and LOD management before executing draw calls to maintain 60FPS targets.
- **Reliability:** The renderer must gracefully handle missing or corrupted textures/geometry without crashing the application.
- **Predictability:** The composition hierarchy must ensure that transparent objects and depth tests resolve identically across different sessions and camera angles.
- **Scalability:** The architecture must support the dynamic addition or removal of overlay renderers without requiring engine reconfiguration.
- **Maintainability:** Specialized renderers (e.g., Atmosphere, Ocean) must remain decoupled, communicating only through the central Scene Composition model.
- **Testability:** Shaders and material functions must be isolated enough to permit visual regression testing.
- **Extensibility:** The lighting and composition models must support future extensions (e.g., multiple light sources, dynamic weather occlusion).
- **Visual Consistency:** Artifacts such as visual tearing, z-fighting, or inconsistent shadowing are treated as critical architectural defects.

## 11. Architectural Risks

- **Tight coupling with simulation:**
  - *Risk:* Renderers reading directly from simulation engines or calculating time delta internally.
  - *Mitigation:* The renderer must accept a plain data object containing the state snapshot per frame.
- **Renderer duplication:**
  - *Risk:* Different subsystems implementing their own conflicting lighting models or atmosphere approximations.
  - *Mitigation:* Enforce a centralized Lighting Evaluation stage that all renderers must consume.
- **State ownership confusion:**
  - *Risk:* The renderer attempting to modify sun position or camera angles to achieve a visual effect.
  - *Mitigation:* Renderers must operate exclusively on read-only interfaces.
- **Excessive rendering complexity:**
  - *Risk:* Over-engineering shaders beyond the visual requirements, compromising performance.
  - *Mitigation:* Strict adherence to the principle of "Scientific realism over spectacle." Performance budgets supersede aesthetic enhancements.
- **Performance regressions:**
  - *Risk:* Adding complex atmospheric or ocean renderers degrades the baseline frame rate.
  - *Mitigation:* Require robust LOD scaling and the ability to gracefully degrade rendering features on lower-end hardware.

## 12. Summary

The Rendering Architecture acts as the visual translation layer of the Living Earth Experience. It operates as a stateless consumer of the World Simulation, strictly prioritizing consistency, scientific credibility, and performance. By establishing clear boundaries, a unified lighting philosophy, and a structured composition hierarchy, TerraMind ensures a visually cohesive, predictable, and highly performant planetary environment.

---

## Implementation Requirements

The following formal implementation requirements authorize future engineering work. All implementation sprints must fulfill and trace back to these IDs.

| Requirement ID | Description | Priority | Verification Method | Source Volume |
|---|---|---|---|---|
| **REN-001** | The rendering pipeline SHALL operate statelessly with respect to environmental simulation state, accepting an immutable state snapshot per frame. | High | Code Review / Architecture Linting | Vol III |
| **REN-002** | All rendering subsystems SHALL consume a unified, centralized lighting model utilizing the sun vector provided by the simulation layer. | High | Visual Inspection / Unit Test | Vol III |
| **REN-003** | The rendering architecture SHALL enforce strict depth sorting and horizon culling prior to material evaluation. | High | Profiling / Frame Debugging | Vol III |
| **REN-004** | The system SHALL implement distinct, decoupled renderers for Atmosphere, Ocean, Terrain, and Space environments. | Medium | Code Review | Vol III |
| **REN-005** | Transitions between different Levels of Detail (LOD) SHALL incorporate smooth visual interpolation to prevent jarring geometric popping. | Medium | Visual Inspection | Vol III |
| **REN-006** | The rendering layer SHALL NOT perform delta time integration or modify any variables owned by the simulation layer. | High | Code Review | Vol III |
| **REN-007** | The architecture SHALL support graceful degradation of rendering complexity (e.g., disabling procedural oceans) based on hardware capability or performance budgets. | Medium | Manual Testing | Vol III |
| **REN-008** | Intelligence data overlays SHALL correctly compose within the global depth buffer alongside physical environmental layers. | High | Visual Inspection | Vol III |
