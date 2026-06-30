# Reproduction Target Table

This table is derived from `data/figure_index.csv`, the local McCarthy 2018 PDF,
and the current Python module audit. "Existing base" means the repository has a
script or module path, not that the result is final thesis-faithful reproduction.

Difficulty scale: L = low, M = medium, H = high, VH = very high.

| McCarthy section | Target | Type | Model | Required algorithms | Existing base | Difficulty | First round? | Data needed | Expected output | Acceptance standard |
|---|---|---|---|---|---|---:|---:|---|---|---|
| 2.1 | Fig 2.1 reference frames | Schematic | Geometry | Plotting | Yes | L | No | None | Figure | Visual layout match |
| 2.2 | Fig 2.2 collinear point geometry | Schematic | CR3BP geometry | Lagrange geometry | Yes | L | No | None | Figure | Visual layout match |
| 2.2 | Fig 2.3 libration points | Numeric | Earth-Moon CR3BP | Lagrange points | Yes | L | Yes | `mu` | CSV + figure | Compare with JPL system block |
| 2.3 | Fig 2.4 ZVC at JC levels | Numeric | Earth-Moon CR3BP | Jacobi, ZVC grid | Yes | L | Yes | `mu`, JC | CSV/grid + figure | Correct open/closed regions |
| 2.3 | Fig 2.5 Earth-Moon rotating frame | Numeric/schematic | Earth-Moon CR3BP | Frame plotting | Yes | L | No | Constants | Figure | Visual consistency |
| 2.3 | Fig 2.6 multi-system ZVC | Numeric | Earth-Moon, Saturn-Titan, Sun-Earth | Jacobi, ZVC grid | Yes | M | Yes | System constants | CSV/grid + figure | Trends match thesis |
| 2.4 | Fig 2.7 linear modes | Numeric | Earth-Moon L1 | Linearization, eigensystem | Yes | M | No | L1 state | Figure + frequencies | Mode classification correct |
| 2.4 | Fig 2.8 Lissajous linear motion | Numeric | Earth-Moon L1 | Center modes | Yes | M | No | L1 state | Figure | Projection shapes match |
| 2.5 | Fig 2.9 single shooting | Schematic | Correction method | Flow diagram | Yes | L | No | None | Figure | Method diagram readable |
| 2.5 | Fig 2.10 multiple shooting arcs | Schematic | Correction method | Flow diagram | Yes | L | No | None | Figure | Method diagram readable |
| 2.5 | Fig 2.11 L2 Lyapunov correction | Numeric | Earth-Moon CR3BP | STM, single shooting | Yes | M | Yes | Initial guess | CSV + figure | Closure and Jacobi drift reported |
| 2.5 | Fig 2.12 continuation schemes | Schematic | Continuation | Natural and pseudo-arclength | Yes | L | No | None | Figure | Scheme match |
| 2.5 | Fig 2.13 Jupiter-Europa families | Numeric | Jupiter-Europa CR3BP | Periodic correction, continuation | Yes | H | No | Family seeds | CSV + figure | Family type and trend match |
| 2.6 | Fig 2.14 L1 manifolds | Numeric | Earth-Moon CR3BP | Monodromy, manifolds | Yes | H | No | Periodic orbit | CSV + figure | Stable/unstable branches plausible |
| 2.6 | Fig 2.15 L2 halo stability | Numeric | Earth-Moon CR3BP | Monodromy, Floquet, stability | Yes | H | No | Halo family | CSV + figure | Stability trend match |
| 3.1 | Fig 3.1 torus concept | Schematic | Geometry | Torus mesh | Yes | L | No | None | Figure | Visual match |
| 3.1 | Fig 3.2 invariant curve concept | Schematic | Stroboscopic map | Rotation angle | Yes | L | No | None | Figure | Visual match |
| 3.1 | Fig 3.3 7-point invariant curve map | Numeric/schematic | Earth-Moon CR3BP | Stroboscopic map, STM correction | Yes | M | No | Seed orbit | CSV + figure | Map residual reported |
| 3.2 | Fig 3.4 patch curves | Schematic | Torus correction | Multiple shooting | Yes | L | No | None | Figure | Visual match |
| 3.3.1 | Fig 3.5 constant-energy quasi-halo tori | Numeric | Earth-Moon L1 CR3BP | Torus correction, continuation | Yes | VH | No | Corrected family | CSV/NPZ + figure | Residuals, JC span, thesis times |
| 3.3.1 | Fig 3.6 quasi-halo amplitudes | Numeric curve | Earth-Moon L1 CR3BP | Continuation metrics | Yes | VH | No | Family table | CSV + figure | Amplitude trend and values |
| 3.3.1 | Fig 3.7 constant-energy quasi-vertical tori | Numeric | Earth-Moon L1 CR3BP | Torus correction, continuation | Yes | VH | No | Corrected family | CSV/NPZ + figure | Residuals, JC span, thesis times |
| 3.3.1 | Fig 3.8 quasi-vertical amplitudes | Numeric curve | Earth-Moon L1 CR3BP | Continuation metrics | Yes | VH | No | Family table | CSV + figure | Amplitude trend and values |
| 3.3.1 | Fig 3.9 frequency ratio vs mapping time | Numeric curve | Earth-Moon L1 CR3BP | Frequency ratio, continuation | Yes | H | No | Family tables | CSV + figure | Ratio trend and resonance notes |
| 3.3.1 | Fig 3.10 period-q halo examples | Numeric | Earth-Moon CR3BP | Floquet resonance, correction | Yes | H | No | Period-q seeds | CSV + figure | Period q closure |
| 3.3.1 | Fig 3.11 Poincare map | Numeric | Earth-Moon CR3BP | Poincare section, periodic orbits | Yes | H | No | Section samples | CSV + figure | Islands and central orbits |
| 3.3.2 | Fig 3.12 constant-frequency quasi-halo tori | Numeric | Earth-Moon L2 CR3BP | Fixed ratio torus correction | Yes | VH | No | Corrected family | CSV/NPZ + figure | Thesis JC targets |
| 3.3.2 | Fig 3.13 quasi-halo amplitudes and JC | Numeric curve | Earth-Moon L2 CR3BP | Fixed ratio continuation | Yes | VH | No | Family table | CSV + figure | Trend and JC targets |
| 3.3.2 | Fig 3.14 constant-frequency quasi-vertical tori | Numeric | Earth-Moon L2 CR3BP | Fixed ratio torus correction | Yes | VH | No | Corrected family | CSV/NPZ + figure | Thesis JC targets |
| 3.3.2 | Fig 3.15 quasi-vertical JC and mapping time | Numeric curve | Earth-Moon L2 CR3BP | Fixed ratio continuation | Yes | VH | No | Family table | CSV + figure | Trend and endpoint |
| 3.3.3 | Fig 3.16 constant-time quasi-DRO tori | Numeric | Earth-Moon DRO CR3BP | DRO correction, stroboscopic torus, continuation | Yes | VH | After DRO gate | DRO family | CSV/NPZ + figure | Thesis `T0=14.74 d`, JC targets |
| 3.3.3 | Fig 3.17 quasi-DRO amplitude and JC | Numeric curve | Earth-Moon DRO CR3BP | Mapping-time continuation | Yes | VH | After DRO gate | Family table | CSV + figure | Z amplitude and JC vs rho |
| 4.1 | Fig 4.1 DG eigenstructure | Numeric | Earth-Moon L2 QPO | DG, Floquet/DG relation | Yes | VH | No | Corrected torus | CSV + figure | Eigenvalue-loop structure |
| 4.1 | Fig 4.2 QPO stability index | Numeric curve | Earth-Moon L1 QPO | DG, stability index | Yes | VH | No | Corrected family | CSV + figure | Stability trend |
| 4.2 | Fig 4.3 quasi-halo +x unstable manifold | Numeric | Earth-Moon L1 QPO | DG eigenvectors, manifold propagation | Yes | VH | No | Corrected torus | CSV/NPZ + figure | Snapshot times and branch shape |
| 4.2 | Fig 4.4 quasi-halo -x unstable manifold | Numeric | Earth-Moon L1 QPO | DG eigenvectors, manifold propagation | Yes | VH | No | Corrected torus | CSV/NPZ + figure | Snapshot times and branch shape |
| 4.2 | Fig 4.5 quasi-vertical +x unstable manifold | Numeric | Earth-Moon L1 QPO | DG eigenvectors, manifold propagation | Yes | VH | No | Corrected torus | CSV/NPZ + figure | Snapshot times and branch shape |
| 4.2 | Fig 4.6 quasi-vertical -x unstable manifold | Numeric | Earth-Moon L1 QPO | DG eigenvectors, manifold propagation | Yes | VH | No | Corrected torus | CSV/NPZ + figure | Snapshot times and branch shape |
| 4.2 | Fig 4.7 quasi-halo vs periodic manifold | Numeric | Earth-Moon L1 QPO/periodic | QPO and periodic manifolds | Yes | VH | No | Corrected tori and halo | Figure + tables | Comparison geometry |
| 4.2 | Fig 4.8 quasi-vertical vs periodic manifold | Numeric | Earth-Moon L1 QPO/periodic | QPO and periodic manifolds | Yes | VH | No | Corrected tori and halo | Figure + tables | Comparison geometry |
| 5.1 | Fig 5.1 Sun-Earth long propagation | Application | Sun-Earth CR3BP/ephemeris | Long propagation | Yes | H | No | QPO state | Figure + drift | Correct duration and drift |
| 5.2 | Fig 5.2 eclipse geometry | Schematic | Sun-Moon geometry | Geometry | Yes | L | No | None | Figure | Visual match |
| 5.2 | Fig 5.3 LOS geometry | Schematic | Earth-Moon-spacecraft | Geometry | Yes | L | No | None | Figure | Visual match |
| 5.2 | Fig 5.4 synodic geometry | Schematic | Sun-Earth-Moon | Frame geometry | Yes | M | No | Ephemeris/geometry | Figure | Phase geometry match |
| 5.2 | Fig 5.5 quasi-DRO return scene | Application | Earth-Moon DRO | DRO, quasi-DRO propagation | Yes | H | After DRO gate | DRO/QPO states | CSV + figure | 10 returns, JC drift |
| 5.2 | Fig 5.6 quasi-DRO by phase | Application | Sun-Earth-Moon ephemeris | Ephemeris embedding, eclipse | Yes | VH | No | DE421, QPO | Figure + eclipse metrics | Phase scenes |
| 5.2 | Fig 5.7 quasi-DRO by epoch | Application | Sun-Earth-Moon ephemeris | Ephemeris embedding, eclipse | Yes | VH | No | DE421, epochs | Figure + eclipse metrics | Epoch scenes |
| 5.3 | Fig 5.8 halo-to-Lyapunov transfer | Application | Earth-Moon CR3BP | Transfer shooting | Yes | VH | No | Boundary orbits | Figure + delta-v | Converged endpoint and cost |
| 5.3 | Fig 5.9 NRHO departure locations | Application | Earth-Moon CR3BP | NRHO correction, intersections | Yes | VH | No | NRHO families | Figure + table | Perilune and stability match |
| 5.3 | Fig 5.10 transfer trajectories | Application | Earth-Moon CR3BP | Transfer correction | Yes | VH | No | NRHO arcs | Figure + delta-v | Flight times and endpoint error |
| 5.3 | Fig 5.11 NRHO-to-NRHO transfer | Application | Earth-Moon CR3BP | Symmetry/transfer arcs | Yes | VH | No | Transfer arcs | Figure | Geometry and continuity |
| 5.3 | Fig 5.12 rendezvous maneuver curve | Application | Earth-Moon CR3BP | Arrival scan | Yes | VH | No | Transfer branch | CSV + figure | Curve trend and fold notes |
| 5.4 | Fig 5.13 periapsis heat map | Application | Sun-Earth CR3BP | Stable manifolds, event detection | Yes | VH | No | Manifold samples | CSV + figure | Periapsis map |
| 5.4.1 | Fig 5.14 LEO to L1 transfer | Application | Sun-Earth CR3BP | Stable manifold access | Yes | VH | No | Manifold branch | Figure + metrics | Target radius and trajectory |
| 3.3.3 support | JPL DRO periodic validation | Validation target | Earth-Moon CR3BP | CR3BP, Jacobi, STM, monodromy, stability | Partial | M | Yes | JPL API row | JSON/CSV report | Closure, JC drift, stability match |

## First Round Recommendation

Do not start with the full QPO torus family. The first executable numerical
target should be the JPL DRO periodic validation row. It prepares the exact
algorithm chain needed for McCarthy Figures 3.16-3.17 while keeping the task
bounded and independently verifiable.
