# External Reproduction Resources

Date checked: 2026-07-01.

This note is a project-facing resource list for the McCarthy 2018 reproduction
effort. Priorities use:

- A: directly useful for key figure or numerical-table reproduction.
- B: useful for algorithmic upgrades or validation infrastructure.
- C: background reading or longer-term reference.

Current project status used for prioritization: Fig. 3.10 is a shape-match
figure with local period-q numerical overlays; Fig. 3.16 and Fig. 3.17 remain
partial physical-consistency baselines, not full numerical reproductions;
Chapter 4 has audited local/finite-amplitude DG manifold baselines but still
retains proxy thesis-scale backgrounds; Chapter 5 should not be upgraded before
the Chapter 3 quasi-DRO branch bottleneck is resolved.

## McCarthy 2018 Original Paper And Related Materials

Public artifact status:

- Thesis PDF: available through the Purdue Hammer thesis record and as the
  local project PDF.
- Separate public appendix: not found in the current search.
- Original numerical tables / branch data / initial states: not found.
- Official McCarthy 2018 reproduction code or public repository: not found.
- Public presentation material: no thesis-specific slide deck found; related
  AAS papers are available and useful for Chapter 5 interpretation.
- Third-party QPO repositories exist, but they should not be treated as
  McCarthy's original data.

| resource_name | url | resource_type | topic | direct_usefulness | possible_project_use | limitations | priority |
|---|---|---|---|---|---|---|---|
| McCarthy 2018 Purdue Hammer thesis record | https://hammer.purdue.edu/articles/thesis/Characterization_of_Quasi-Periodic_Orbits_for_Applications_in_the_Sun-Earth_and_Earth-Moon_Systems/7423658 | Thesis landing page / PDF record | Original McCarthy thesis; CR3BP QPO computation, invariant tori, DG stability, applications | Fig. 3.10: high; Fig. 3.16/3.17: high; Chapter 4: high; Chapter 5: high | Primary source for figure intent, equations, algorithm sequence, terminology, and figure classification | Does not expose machine-readable branch data or code; figures must still be digitized or recomputed | A |
| Local McCarthy 2018 PDF | `C:/Users/wwh20/Desktop/复现论文/2018_McCarthy_拟周期轨道.pdf` | Local PDF | Same thesis text and figures | Fig. 3.10: high; Fig. 3.16/3.17: high; Chapter 4: high; Chapter 5: high | Stable local reference for page/figure review without relying on Purdue site availability | Local file only; not an external data source; no embedded numerical CSV known | A |
| Purdue Engineering direct PDF URL for McCarthy 2018 | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Masters/2018_McCarthy.pdf | PDF URL / Purdue mirror candidate | Original thesis mirror | Fig. 3.10: high if accessible; Fig. 3.16/3.17: high if accessible; Chapter 4: high if accessible; Chapter 5: high if accessible | Try as a redundant source if Hammer or local PDF is unavailable | Prior project access log observed a Purdue "site under construction" response; do not rely on it until rechecked | B |
| Purdue Howell group M.S. thesis index | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/masters.html | Publication index | Howell group thesis listing, including McCarthy and Olikara | Helps locate original and predecessor theses | Use as a discovery route for related Purdue theses | JavaScript/page changes can hide direct links; index does not provide data tables | B |
| Olikara and Howell 2010, Computation of Quasi-Periodic Invariant Tori in the Restricted Three-Body Problem | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2010_AAS_OliHow.pdf | Conference paper PDF | Invariant curve method, natural parameterization, continuation for CR3BP tori | Fig. 3.16/3.17: high; Chapter 4: medium; Fig. 3.10: low; Chapter 5: low | Reconstruct McCarthy's inherited invariant-curve correction logic and continuation constraints | Method paper, not McCarthy's quasi-DRO data; examples are not the target branch | A |
| Olikara 2010 Purdue thesis record | https://docs.lib.purdue.edu/dissertations/AAI1489526/ | Thesis record | Predecessor invariant torus computation in CR3BP | Fig. 3.16/3.17: high; Chapter 4: medium | Fill details omitted by McCarthy about initialization, discretization, and constraints | Record/abstract source; direct PDF availability may vary | B |
| Olikara 2016 Colorado PhD thesis | https://hanspeterschaub.info/Papers/grads/ZubinOlikara.pdf | Thesis PDF | Collocation methods for quasi-periodic tori and heteroclinic connections | Fig. 3.16/3.17: medium; Chapter 4: high | Reference for moving from invariant-curve shooting to collocation/BVP torus methods and manifold connections | Not McCarthy's implementation; dynamics/examples differ | B |
| McCarthy and Howell 2019 AAS, Trajectory Design Using Quasi-Periodic Orbits in the Multi-Body Problem | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2019_AAS_McCHow.pdf | Conference paper PDF | Quasi-DRO applications, mapping-time resonance, Chapter 5-style trajectory design | Fig. 3.16/3.17: medium; Chapter 5: high | Interpret quasi-DRO application intent and resonance choices; compare Chapter 5 scenes qualitatively | Does not replace thesis branch data; often figure-level rather than table-level | B |
| McCarthy and Howell 2021 AAS, Quasi-Periodic Orbits in the Sun-Earth-Moon BCR4BP | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2021_AAS_McCHow.pdf | Conference paper PDF | BCR4BP quasi-periodic orbits and stability | Chapter 5: high; Fig. 3.16/3.17: medium | Later reference for BCR4BP upgrade after the CR3BP quasi-DRO branch is reliable | Later model and problem setting; not needed for current bottleneck documentation | B |
| McCarthy and Howell 2022 AAS paper | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2022_AAS_MccHow.pdf | Conference paper PDF | Cislunar access / quasi-periodic orbit applications | Chapter 5: medium | Context for transfer examples and application framing | Not a source for Fig. 3.10 or Fig. 3.16/3.17 branch data | C |
| Leveraging quasi-periodic orbits for trajectory design in cislunar space | https://link.springer.com/article/10.1007/s42064-020-0094-5 | Journal article | QPO continuation and cislunar trajectory design | Chapter 5: high; Fig. 3.16/3.17: medium | Peer-reviewed context for trajectory design claims and application-level wording | Paywall/metadata limits may restrict full-text access; not a raw-data source | B |
| dlujan17/QPOs | https://github.com/dlujan17/QPOs | Third-party GitHub repository | QPO computation code in Julia/MATLAB/Python | Fig. 3.16/3.17: medium as method reference | Inspect alternative implementation patterns for quasi-periodic orbit computation | Not official McCarthy code; small repo with limited validation; must not be cited as original thesis data | C |

## Quasi-Periodic Orbit / Invariant Torus Continuation Methods

| resource_name | url | resource_type | topic | direct_usefulness | possible_project_use | limitations | priority |
|---|---|---|---|---|---|---|---|
| Schilder, Osinga, Vogt 2005, Continuation of Quasi-Periodic Invariant Tori | https://epubs.siam.org/doi/10.1137/040611240 | Journal article | Natural parameterization and continuation of quasi-periodic invariant tori | Fig. 3.16/3.17: high for formulation replacement | Theory reference for switching away from fragile fixed-mapping local shooting; useful for fold/parameterization handling | General ODE method; not CR3BP-specific and may require adaptation | B |
| Olikara and Howell 2010 invariant curve method | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2010_AAS_OliHow.pdf | Conference paper PDF | Invariant curve discretization, stroboscopic map, CR3BP torus correction | Fig. 3.16/3.17: high; Chapter 4: medium | Audit current fixed-mapping implementation against the method ancestor | May share the same local-parameterization weakness that appears near rho about 1.44388 | A |
| Tor toolbox paper | https://arxiv.org/abs/2012.13256 | arXiv paper | Fourier/collocation torus BVP based on COCO | Fig. 3.16/3.17: high for route B | Candidate formulation for replacing fixed-mapping invariant-curve correction with a BVP torus continuation | MATLAB/COCO ecosystem; not an immediate drop-in for current NumPy/SciPy code | B |
| Tor toolbox repository | https://github.com/mingwu-li/torus_collocation | GitHub repository | COCO-based torus continuation implementation | Fig. 3.16/3.17: high for prototype study | Study data structures, Fourier/collocation residual definitions, and continuation setup | Requires MATLAB and COCO; examples are generic, not Earth-Moon quasi-DRO | B |
| Baresi, Scheeres et al., Fully Numerical Methods for Continuing Families of Quasi-Periodic Invariant Tori in Astrodynamics | https://openresearch.surrey.ac.uk/esploro/outputs/journalArticle/Fully-Numerical-Methods-for-Continuing-Families/99543723002346 | Journal article / repository record | Method comparison for astrodynamics invariant tori | Fig. 3.16/3.17: high; Chapter 4: medium | Select between invariant-curve, multiple shooting, and BVP/collocation approaches for the next algorithm route | May not provide complete executable implementation; use as a decision reference | B |
| Kolemen, Kasdin, Gurfil 2006, Quasi-Periodic Orbits of the RTBP Made Easy | https://www.princeton.edu/~ekolemen/publications/kolemen-kasdin-gurfil_-_quasi_periodic_orbits_of_RTBP_made_easy.pdf | Conference paper PDF | Frequency-domain / quasi-periodic RTBP methods | Fig. 3.16/3.17: medium | Alternative conceptual route for invariant torus construction and frequency constraints | Older and not McCarthy-specific; needs careful adaptation to current correction/audit gates | C |
| Pseudo-arclength continuation in the CR3BP with heyoka.py | https://bluescarni.github.io/heyoka.py/notebooks/Pseudo%20arc-length%20continuation%20in%20the%20CR3BP.html | Python notebook | PALC through folds for CR3BP periodic orbit families | Fig. 3.10: medium; Fig. 3.16/3.17: medium | Reference implementation for tangent constraints, folds, and high-accuracy propagation | Periodic-orbit example, not 2D torus continuation; current project already found PALC alone insufficient in fixed-mapping form | B |
| Pyoomph pseudo-arclength tutorial | https://pyoomph.readthedocs.io/en/latest/tutorial/temporal/stability/arclength.html | Documentation tutorial | General pseudo-arclength continuation and folds | Fig. 3.16/3.17: low | Use for explaining why natural parameters fail near folds | General ODE/equilibrium tutorial; not astrodynamics | C |

## Available Continuation Software Or Toolchains

| resource_name | url | resource_type | topic | direct_usefulness | possible_project_use | limitations | priority |
|---|---|---|---|---|---|---|---|
| COCO Continuation Core and Toolboxes | https://sourceforge.net/p/cocotools/wiki/Home/ | MATLAB toolbox | Continuation core for constrained nonlinear problems and BVPs | Fig. 3.16/3.17: high as infrastructure for route B | Prototype torus BVP continuation and compare against current fixed-mapping branch | MATLAB dependency; project is currently Python-first | B |
| COCO SIAM software page | https://archive-dsweb.siam.org/Software/coco-continuation-core-and-toolboxes-for-matlab.html | Software overview | COCO background, examples, documentation | Fig. 3.16/3.17: medium | Justify tool selection in research report; find tutorials | Secondary page; use SourceForge/GitHub for actual code | C |
| Tor toolbox / torus_collocation | https://github.com/mingwu-li/torus_collocation | MATLAB/COCO toolbox | Two-dimensional torus BVP using Fourier series and collocation | Fig. 3.16/3.17: high | Best external prototype candidate for replacing the quasi-DRO continuation formulation | Requires translating CR3BP equations and constraints into Tor/COCO form | B |
| AUTO-07P official page | https://cmvl.cs.concordia.ca/auto/ | Continuation software | Continuation and bifurcation for ODEs | Fig. 3.10: medium; Fig. 3.16/3.17: low to medium | Periodic-orbit continuation and fold diagnostics; potential baseline for Chapter 2/3 periodic families | Not specialized for 2D invariant tori; Fortran/Python workflow overhead | C |
| AUTO-07P GitHub | https://github.com/auto-07p/auto-07p | Source repository | AUTO source and examples | Fig. 3.10: medium | Reproduce periodic-orbit continuation examples or validate halo families | Toolchain setup and model translation cost | C |
| MATCONT | https://sourceforge.net/projects/matcont/ | MATLAB toolbox | Numerical continuation and bifurcation for ODEs/maps | Fig. 3.10: medium; Fig. 3.16/3.17: low | Periodic-orbit stability and bifurcation checks; education/demo value | Not a direct torus BVP replacement; MATLAB GUI/workflow | C |
| MATCONT manual | https://webspace.science.uu.nl/~kouzn101/NBA/ManualMatcontAug2019.pdf | PDF manual | MATCONT algorithms and usage | Fig. 3.10: medium | Reference for continuation singularities and bifurcation detection | General dynamical-systems focus; not CR3BP-specific | C |
| BifurcationKit.jl documentation | https://docs.sciml.ai/BifurcationKit/ | Julia package documentation | Large-scale continuation and bifurcation analysis | Fig. 3.16/3.17: medium for experimental route | Could prototype Newton-Krylov/PALC continuation for discretized torus equations in Julia | No built-in McCarthy-style invariant torus workflow; Julia stack adds maintenance cost | C |
| BifurcationKit.jl GitHub | https://github.com/bifurcationkit/BifurcationKit.jl | Julia source repository | PALC, Newton-Krylov, bifurcation tools | Fig. 3.16/3.17: medium | Inspect algorithms for robust continuation constraints and branch switching | Requires custom residual construction and cross-language validation | C |
| heyoka.py CR3BP periodic orbit notebook | https://bluescarni.github.io/heyoka.py/notebooks/Periodic%20orbits%20in%20the%20CR3BP.html | Python notebook | High-order Taylor integration, STM, periodic orbit correction | Fig. 3.10: high; Chapter 2/3 periodic seeds: high | Validate CR3BP propagation and STM accuracy; possible high-accuracy backend for local tests | Periodic orbit only; does not solve quasi-DRO torus bottleneck directly | B |
| heyoka.py pseudo-arclength CR3BP notebook | https://bluescarni.github.io/heyoka.py/notebooks/Pseudo%20arc-length%20continuation%20in%20the%20CR3BP.html | Python notebook | PALC for CR3BP periodic families | Fig. 3.10: medium; Fig. 3.16/3.17: medium | Reference for robust fold-crossing continuation implementation details | Current instruction is not to write a new continuation algorithm in this round | B |
| CR3BP MATLAB Library | https://github.com/JackCrusoe47/CR3BP_MATLAB_Library | GitHub repository | CR3BP equations, STM, monodromy, continuation examples | Fig. 3.10: medium; Chapter 4: low | Cross-check formulas and periodic-orbit routines | MATLAB reference only; not a project dependency | C |

## CR3BP / Astrodynamics Benchmark Resources

| resource_name | url | resource_type | topic | direct_usefulness | possible_project_use | limitations | priority |
|---|---|---|---|---|---|---|---|
| JPL Three-Body Periodic Orbits API documentation | https://ssd-api.jpl.nasa.gov/doc/periodic_orbits.html | API documentation | Poincare Catalog of Periodic Orbits; CR3BP families | Fig. 3.10: high for periodic seeds; Fig. 3.16/3.17: medium for DRO base validation | Machine-readable halo, Lyapunov, vertical, DRO periodic orbit checks; independent period/Jacobi/state validation | Periodic orbits only; no quasi-periodic torus families or McCarthy branch data | A |
| JPL Three-Body Periodic Orbits visualization tool | https://ssd.jpl.nasa.gov/tools/periodic_orbits.html | Web visualization tool | CR3BP periodic orbit catalog | Fig. 3.10: medium; Chapter 2/3: medium | Manual visual sanity checks for periodic families | JavaScript UI; less useful for automated reproduction than the API | B |
| JPL Earth-Moon DRO API query sample | https://ssd-api.jpl.nasa.gov/periodic_orbits.api?sys=earth-moon&family=dro&periodunits=d&periodmin=10&periodmax=20 | API endpoint | Earth-Moon DRO periodic family data | Fig. 3.16/3.17: medium | Validate the 2:1 resonant DRO base orbit period/Jacobi before quasi-DRO torus construction | Does not include out-of-plane quasi-DRO torus members | A |
| JPL Earth-Moon Halo API query pattern | https://ssd-api.jpl.nasa.gov/periodic_orbits.api?sys=earth-moon&family=halo&libr=1&branch=N | API endpoint pattern | Earth-Moon halo periodic family data | Fig. 3.10: high | Seed or validate period-q halo examples and monodromy quantities | Family conventions may differ from thesis examples; resonance selection still requires project logic | A |
| JPL Technical Report 32-1168 | https://ntrs.nasa.gov/api/citations/19680013800/downloads/19680013800.pdf | Historical PDF report | Earth-Moon CR3BP periodic orbits and tables | Fig. 3.10: low to medium; Chapter 2: medium | Historical benchmark for periodic-orbit family behavior and nomenclature | Old tables/normalizations; not aligned with McCarthy QPO figures | C |
| Grebow 2006 Purdue thesis, Generating Periodic Orbits in the CR3BP | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Masters/2006_Grebow.pdf | Thesis PDF URL / Purdue mirror candidate | Periodic orbit generation, differential correction | Fig. 3.10: medium | Method background for periodic orbit correction and continuation | Purdue direct PDF may have access issues; not QPO data | C |
| GMAT | https://software.nasa.gov/software/GSC-19097-1 | NASA software page | Mission design, optimization, navigation | Chapter 5: medium | High-fidelity trajectory cross-checks and mission-design context after CR3BP/BCR4BP baselines mature | Heavy external GUI/tool workflow; not needed for current Chapter 3 bottleneck | C |
| Orekit | https://www.orekit.org/ | Java library | Flight dynamics, propagation, frames, events | Chapter 5: medium | Frame/time/event infrastructure if high-fidelity checks move beyond current Python stack | Java ecosystem; no direct CR3BP torus continuation | C |
| poliastro | https://docs.poliastro.space/ | Python library documentation | Astrodynamics, propagation, Lambert, visualization | Chapter 5: low to medium | Auxiliary two-body/Lambert/visualization reference for transfer-baseline reporting | Current project already has core CR3BP/ephemeris code; poliastro is not a QPO solver | C |
| JuliaAstro CR3BP model documentation | https://juliaastro.org/GeneralAstrodynamics.jl/lib/AstrodynamicalModels/stable/CR3BP/ | Julia documentation | CR3BP equations and model setup | Chapter 2/3: low | Cross-language formula reference | Not a continuation or QPO resource | C |

## Chapter 5 Application Resources

| resource_name | url | resource_type | topic | direct_usefulness | possible_project_use | limitations | priority |
|---|---|---|---|---|---|---|---|
| NAIF SPICE Toolkit and kernels | https://naif.jpl.nasa.gov/naif/ | NASA toolkit and data portal | SPICE APIs, ephemerides, frames, geometry | Chapter 5: high | Authoritative route for Sun-Earth-Moon ephemeris, frame, eclipse, and line-of-sight computations | Requires careful kernel/frame/time management; does not solve torus continuation | A |
| NAIF generic kernels | https://naif.jpl.nasa.gov/naif/data_generic.html | Kernel archive | Generic SPK/PCK/LSK kernels including planetary ephemerides | Chapter 5: high | Source for DE ephemeris kernels and supporting frame/orientation data | Kernel choice affects reproducibility; must pin exact kernel versions | A |
| NAIF DE421 kernel announcement | https://naif.jpl.nasa.gov/pipermail/spice_announce/2008-March/000062.html | Announcement / kernel pointer | DE421 SPICE kernel availability | Chapter 5: medium | Context for current `data/raw/ephemeris/de421.bsp` usage and lunar frame decisions | Old announcement; modern work may prefer DE440/DE441 | B |
| NAIF lunar frame kernel readme | https://naif.jpl.nasa.gov/pub/naif/generic_kernels/fk/satellites/aareadme.txt | Text readme | Lunar PA/ME frames and DE421/DE440 associations | Chapter 5: high | Prevent frame mismatches in Earth-Moon/Sun-Earth-Moon scenes | Technical frame details; not a trajectory design method | A |
| Skyfield ephemeris loading guide | https://rhodesmill.org/skyfield/planets.html | Python documentation | Loading JPL ephemerides such as DE421 | Chapter 5: medium | Lightweight Python route to verify ephemeris state extraction | Auxiliary only; SPICE remains the authoritative high-fidelity path | C |
| McCarthy and Howell 2021 BCR4BP QPO paper | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2021_AAS_McCHow.pdf | Conference paper PDF | Sun-Earth-Moon BCR4BP quasi-periodic orbit families | Chapter 5: high | Main external reference before BCR4BP/ephemeris upgrades | Later than thesis and not identical to Chapter 5; no public branch data located | B |
| Quasi-Periodic Orbits in the Sun-Earth-Moon BCR4BP ResearchGate record | https://www.researchgate.net/publication/349506421_Quasi-Periodic_Orbits_in_the_Sun-Earth-Moon_Bicircular_Restricted_Four-Body_Problem | Paper record | BCR4BP quasi-periodic orbits | Chapter 5: medium | Backup discovery record if Purdue link changes | ResearchGate content may be partial; prefer Purdue PDF when available | C |
| Resonant quasi-periodic NRHOs in elliptic-circular four-body problem | https://hal.science/hal-04011123/document | PDF | NRHO/QPO four-body reference | Chapter 5: medium | Background for resonance, NRHO, and higher-fidelity quasi-periodic motion | Not McCarthy thesis data; different orbit family | C |
| Frontiers 2024, 2:1 resonant quasi-periodic DROs | https://www.frontiersin.org/journals/astronomy-and-space-sciences/articles/10.3389/fspas.2024.1352489/full | Journal article | 2:1 resonant quasi-periodic DROs in cislunar dynamics | Fig. 3.16/3.17: medium; Chapter 5: high | Modern comparison for quasi-DRO motivation, resonance, and post-McCarthy framing | Later work; should not be used to overwrite McCarthy target values | B |
| NASA GMAT | https://software.nasa.gov/software/GSC-19097-1 | Mission design software | High-fidelity mission analysis and optimization | Chapter 5: medium | Independent high-fidelity transfer/eclipsing sanity checks after the branch is valid | Tool integration overhead; not suitable for this documentation-only round | C |
| Orekit tutorials | https://www.orekit.org/doc-tutorials.html | Documentation | Flight-dynamics examples, Python-wrapped usage | Chapter 5: low to medium | Event and propagation examples for later validation harnesses | Does not provide QPO or BCR4BP continuation algorithms | C |

## Immediate Use Recommendations

1. Route A should start with the Hammer thesis record, local PDF, Purdue/Howell
   publication pages, and figure digitization. There is no confirmed public
   McCarthy branch data or official code, so the search should be treated as a
   finite discovery task rather than an assumption.
2. Route B should compare the current fixed-mapping invariant-curve formulation
   against Olikara/Howell 2010, Schilder/Osinga/Vogt 2005, and Tor/COCO. The
   bottleneck evidence favors a formulation change before increasing spectral
   order again.
3. Route C should rely on the current `figure_validation_table.csv`,
   `chapter3_quasi_dro_validation.md`, and `chapter4_manifold_validation.md`
   to prepare a defensible reproduction-status report while clearly preserving
   the partial-baseline label for Fig. 3.16 and Fig. 3.17.
