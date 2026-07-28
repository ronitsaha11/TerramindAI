# TerraMind Living Earth Experience

**Volume VI: Space Systems Architecture**

- **Version:** 1.0.0
- **Status:** DRAFT
- **Phase:** 11.5
- **Last Updated:** 2026-07-28

**Dependencies:**
- Living Earth Master Plan
- Volume I: Vision & Product Philosophy
- Volume II: World Simulation Architecture
- Volume III: Rendering Architecture
- Volume V: Planet Systems Architecture

**Influences:**
- Volume VII: Streaming & Transition
- Volume VIII: Performance
- Volume IX: Experience Choreography

---

## 1. Purpose

This volume defines the architectural specification governing TerraMind's celestial environment. It delineates the conceptual ownership of the space environment surrounding Earth—specifically the Sun, Moon, starfield, and deep space background. The Space Systems Architecture ensures that celestial bodies interact cohesively with the planet without violating the core principle that Earth remains the primary focus of the platform.

## 2. Architectural Goals

The Space Systems architecture is designed to achieve the following goals:

- **Scientific Consistency:** Celestial mechanics must align mathematically with the central World Simulation clock, producing accurate orbital positions.
- **Natural Celestial Motion:** Movement of the Sun, Moon, and stars must be continuous and smooth, strictly correlated with the passage of simulation time.
- **Visual Stability:** The celestial sphere must remain anchored perfectly to the camera frustum without suffering from depth-buffer jitter or bounding-box clipping at high altitudes.
- **Scalability:** The architecture must readily support the future addition of dynamic orbital bodies (e.g., satellites, debris) without redesigning the foundational skybox.
- **Modularity:** Space rendering systems must be entirely decoupled from terrestrial (planet) rendering systems, minimizing rendering overlap.

## 3. Space Principles

- **Sun follows simulation.**
  - *Description:* The Sun's position is a pure derivative of the centralized simulation time.
  - *Motivation:* Prevents the introduction of a secondary, competing time source for lighting.
  - *Architectural implications:* The Sun component queries the World Simulation for its vector rather than calculating it independently.

- **Moon follows simulation.**
  - *Description:* The Moon's orbital position and phase reflect the central simulation time.
  - *Motivation:* Ensures scientific credibility, particularly concerning tides or nocturnal illumination in future phases.
  - *Architectural implications:* Lunar rendering requires periodic position updates sourced from the simulation's orbital models.

- **Stars are background context.**
  - *Description:* The starfield provides essential orientation cues but is not the focal point.
  - *Motivation:* Complex, interactive constellations distract from intelligence analysis on the Earth.
  - *Architectural implications:* Star rendering should prioritize performance and anti-aliasing over deep astronomical interactivity.

- **Space enhances orientation.**
  - *Description:* The deep space background provides spatial framing when zoomed out.
  - *Motivation:* A pure black void eliminates scale and perspective.
  - *Architectural implications:* The background must include subtle galactic textures or Milky Way representations to establish camera orientation relative to the galactic plane.

- **Earth remains primary focus.**
  - *Description:* Space components exist only to contextualize the planet.
  - *Motivation:* TerraMind is an Earth Intelligence platform, not a solar system explorer.
  - *Architectural implications:* The camera and interaction models heavily restrict navigation beyond Earth's orbital sphere.

## 4. Space Components

The architecture delegates responsibilities to the following discrete components:

- **Sun:** Manages the visual representation of the solar disc and lens flares. Conceptually acts as the origin point for the global directional light used by the Planet Systems.
- **Moon:** Manages the geometric or billboarding representation of the Moon, including its phase rendering based on the Sun-Earth-Moon angle.
- **Stars:** Manages the point-cloud or cubemap representation of the stellar background.
- **Deep Space Background:** Manages the lowest-level rendering layer (the infinite sphere or cubemap) presenting the Milky Way or galactic noise.
- **Celestial Lighting Inputs:** A conceptual interface translating physical celestial positions into lighting variables consumed by the Rendering Architecture.
- **Orbital Context:** The spatial region encompassing Near-Earth space, conceptually reserving bounds for future satellite or orbital intelligence rendering.

## 5. Architectural Boundaries

Space Systems maintain clear boundaries with external architectures:

- **Interaction with Simulation (Volume II):** Space Systems query the simulation for absolute time to evaluate planetary rotation and orbital mechanics.
- **Interaction with Rendering (Volume III):** Space Systems declare their visual bounds and textures to the rendering pipeline. The renderer handles the depth evaluation to ensure space renders behind the Earth.
- **Interaction with Planet (Volume V):** Space Systems do not interact directly with Planet Systems. The Atmosphere (Planet) occludes Space Systems naturally via the rendering depth buffer.
- **Interaction with Camera (Volume IV):** Space Systems evaluate the camera's rotational matrix to position the skybox, effectively remaining at an infinite distance regardless of camera translation.
- **Interaction with Streaming (Volume VII):** Space Systems may request high-resolution star catalogs or celestial textures, though these are typically cached at initialization.

## 6. Celestial Relationships

Interactions between celestial components are conceptually defined to maintain visual accuracy:

- **Sun and Moon:** The visual phase of the Moon is determined by computing the vector from the Moon to the Sun. The Sun is the singular illuminator.
- **Sun and Stars:** During daytime rendering (from a surface perspective), atmospheric scattering (Planet System) naturally obscures the Stars. However, from orbital perspectives, Stars remain visible alongside the Sun.
- **Earth and Space:** The Earth acts as the central anchor. All Space Systems rotate relative to the Earth based on the simulation's rotation matrix.

## 7. Lifecycle

The Space Systems undergo a defined lifecycle:

- **Initialization:** Celestial meshes (skyboxes, sun billboards) are constructed. Initial time is fetched from the simulation to set starting vectors.
- **Active:** During every simulation tick, celestial components evaluate their orbital matrices and update their transform configurations for the renderer.
- **Streaming:** High-resolution star catalogs or deep-space imagery are loaded asynchronously to replace low-resolution initial placeholders.
- **Shutdown:** Celestial resources, buffers, and textures are explicitly released.

## 8. Quality Attributes

- **Reliability:** The orbital mathematics must gracefully handle extreme time scaling (e.g., centuries per second) without floating-point explosions.
- **Scientific Credibility:** Stellar positioning must correspond roughly to actual celestial spheres, maintaining relative accuracy to Earth's axial tilt.
- **Performance:** Rendering thousands of stars must not bottleneck the GPU. The architecture mandates highly optimized batching or shader-driven approaches for the starfield.
- **Maintainability:** The mathematical evaluation of orbits must remain strictly isolated from the visual presentation of the celestial bodies.
- **Extensibility:** The Space architecture must easily accommodate the addition of arbitrary dynamic orbital bodies (satellites) in subsequent phases.

## 9. Risks

- **Lighting Inconsistencies:** 
  - *Risk:* The visual Sun disc becoming desynchronized with the actual directional light vector used by the Planet Systems.
  - *Mitigation:* Both the Sun visualizer and the Planet rendering pipeline must query the exact same lighting vector from the central Simulation layer.
- **Multiple Celestial Authorities:** 
  - *Risk:* The Space system attempting to dictate time of day to the Earth based on the Sun's position.
  - *Mitigation:* Strict unidirectional flow: Simulation dictates time, Space responds to time.
- **Visual Discontinuities:** 
  - *Risk:* The skybox clipping or suffering from z-fighting as the camera zooms far away from the Earth.
  - *Mitigation:* The rendering pipeline must draw the Space systems using a dedicated depth-cleared pass or an infinite projection matrix.
- **Coordinate Errors:** 
  - *Risk:* Floating-point limits causing the Sun or Moon to jitter when calculating vast spatial distances.
  - *Mitigation:* Celestial bodies should be rendered conceptually on a unit sphere scaled and translated around the camera, rather than at literal astronomical distances.

## 10. Summary

The Space Systems Architecture establishes the cosmic context for the TerraMind platform. By treating the Sun, Moon, and stars as decoupled observational entities that rigidly follow the central World Simulation, the platform guarantees a scientifically credible, visually stable, and highly performant celestial environment that perfectly complements the Living Earth without overwhelming it.

---

## Implementation Requirements

The following requirements mandate the formal engineering outcomes for the Space Systems architecture.

| ID | Description | Priority | Verification | Source Volume |
|---|---|---|---|---|
| **SPC-001** | The visual position of the Sun SHALL be derived exclusively from the centralized World Simulation sun vector. | Critical | Code Review / Unit Test | Vol VI |
| **SPC-002** | The Space Systems SHALL be rendered such that they always appear at optical infinity relative to the Camera. | High | Visual Inspection | Vol VI |
| **SPC-003** | The starfield SHALL remain fixed relative to the celestial sphere, rotating smoothly around the Earth based on simulation time. | High | Automated UI Test | Vol VI |
| **SPC-004** | The visual phase of the Moon SHALL be dynamically evaluated based on the relative angle between the Earth, Moon, and Sun. | Medium | Visual Inspection | Vol VI |
| **SPC-005** | Space Systems SHALL NOT implement independent timekeeping mechanisms. | Critical | Code Review | Vol VI |
| **SPC-006** | The deep space background SHALL provide sufficient visual texture (e.g., Milky Way) to allow users to orient themselves when zoomed out. | Medium | Manual QA | Vol VI |
| **SPC-007** | Rendering of the starfield SHALL be optimized to prevent GPU bottlenecks, favoring shader-driven or batched point implementations. | High | Profiling | Vol VI |
| **SPC-008** | The Space architecture SHALL maintain distinct boundaries from Planet Systems, relying on the rendering depth buffer for natural occlusion by the Earth. | High | Integration Test | Vol VI |
| **SPC-009** | The architecture SHALL reserve conceptual bounding regions (Orbital Context) capable of supporting future Near-Earth Object rendering. | Low | Architecture Review | Vol VI |
| **SPC-010** | Celestial mathematics SHALL utilize relative-to-camera rendering techniques to eliminate floating-point jitter at astronomical distances. | High | Visual Inspection | Vol VI |
