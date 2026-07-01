# Next Reproduction Roadmap

This roadmap defines the next phase after the current 54-figure first-pass
coverage, Fig. 3.10 audit, Chapter 4 DG manifold audit, and Chapter 3 quasi-DRO
bottleneck diagnosis. It deliberately does not continue the current
fixed-mapping-time quasi-DRO trial-and-error loop, does not modify Fig. 3.10,
does not continue Chapter 4, and does not start Chapter 5 numerical upgrades.

## Current Decision Point

The accepted Chapter 3 quasi-DRO branch reaches only:

- `rho = 1.443877875293695 rad`
- `max_abs_z = 10164.02309965055 km`

No accepted member exceeds 10,500 km or 11,000 km. Raising the curve order from
`N=41` to `N=61` reduces Fourier tail energy but does not move the accepted
branch past 10,164.02309965055 km. Fixed-rotation and fixed-mean-Jacobi/free-rho
experiments can generate higher-amplitude candidates, but those candidates fail
the residual/Jacobi/phase audit. The most likely issue is a local
parameterization or Newton-basin failure in the fixed-mapping-time formulation
near rho about 1.44388.

Fig. 3.16 and Fig. 3.17 therefore remain partial physical-consistency baselines,
not full numerical reproductions.

## Route A: Continue Searching For McCarthy Original Data

### Goal

Find original branch data, initial states, tables, high-resolution figures,
appendices, author-provided materials, or reliable figure digitization sources
for McCarthy 2018.

### Best resources

- Purdue Hammer thesis record:
  https://hammer.purdue.edu/articles/thesis/Characterization_of_Quasi-Periodic_Orbits_for_Applications_in_the_Sun-Earth_and_Earth-Moon_Systems/7423658
- Local thesis PDF:
  `C:/Users/wwh20/Desktop/复现论文/2018_McCarthy_拟周期轨道.pdf`
- Purdue Howell publication pages and related McCarthy/Howell AAS papers.
- Existing project resource log:
  `docs/resource_links.md`
- New resource inventory:
  `docs/external_reproduction_resources.md`
- JPL Three-Body Periodic Orbits API for independent periodic-orbit baselines:
  https://ssd-api.jpl.nasa.gov/doc/periodic_orbits.html

### Suitable for solving

- Fig. 3.10: identify exact period-q halo branch choices, initial states, and
  view/scale if available.
- Fig. 3.16 / Fig. 3.17: recover original quasi-DRO rho, amplitude, Jacobi, and
  mapping-time branch data if any public table exists.
- Chapter 4: compare manifold topology, terminal bounds, and visual scale
  against thesis figures.
- Chapter 5: clarify which quasi-DRO member and ephemeris assumptions were used
  for application scenes.

### Work plan

1. Recheck Hammer, Purdue library, and Purdue Engineering links for attachments
   beyond the thesis PDF.
2. Search by exact figure captions, "quasi-DRO", "14.75 days", "McCarthy
   Howell 2019", and "constant mapping time quasi-DRO".
3. Record negative findings explicitly: no appendix, no public CSV, no official
   GitHub, no slide deck, if still true.
4. Digitize Fig. 3.16 / Fig. 3.17 only if original data remain unavailable.
5. Compare digitized curves against current corrected branch and proxy trends.

### Risks

- The original data may not be public.
- Figures may have insufficient resolution for precise digitization.
- Related AAS papers may reuse thesis concepts without exposing branch data.
- Contacting authors may be necessary but is outside an automated reproduction
  workflow.

### Stop condition

Route A is complete for the next phase when the project has either:

- located original data/materials and linked them in
  `docs/external_reproduction_resources.md`, or
- documented a defensible negative search and moved to digitization/reporting.

## Route B: Replace The Quasi-DRO Continuation Formulation

### Goal

Move away from the current fixed-mapping invariant-curve correction as the only
high-amplitude quasi-DRO route. Candidate replacements are Fourier/collocation
torus BVP formulations, COCO/Tor-style continuation, or another continuation
setup that can handle branch folds and local parameterization failures more
robustly.

### Best resources

- Olikara and Howell 2010 invariant torus method:
  https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2010_AAS_OliHow.pdf
- Schilder, Osinga, Vogt 2005 torus continuation:
  https://epubs.siam.org/doi/10.1137/040611240
- Tor toolbox paper:
  https://arxiv.org/abs/2012.13256
- Tor toolbox repository:
  https://github.com/mingwu-li/torus_collocation
- COCO:
  https://sourceforge.net/p/cocotools/wiki/Home/
- heyoka.py CR3BP continuation notebooks:
  https://bluescarni.github.io/heyoka.py/notebooks/Pseudo%20arc-length%20continuation%20in%20the%20CR3BP.html

### Suitable for solving

- The 10,000-11,000 km quasi-DRO bottleneck.
- Distinguishing a real physical branch issue from a fixed-mapping-time
  parameterization failure.
- Building a more defensible high-amplitude Fig. 3.16 / Fig. 3.17 reproduction.
- Later Chapter 5 quasi-DRO scenes, but only after the CR3BP branch is accepted.

### Work plan

1. Freeze the current branch and diagnostics as baseline evidence.
2. Write a short method comparison note before coding:
   invariant curve shooting vs Fourier/collocation torus BVP vs fixed-rotation
   or fixed-energy continuation.
3. Prototype on a smaller known torus family before returning to quasi-DRO.
4. Define strict acceptance gates before any figure upgrade:
   map/BVP residual, Jacobi span, phase consistency, Fourier tail, singular
   value conditioning, and multi-return drift.
5. Only after passing 11,000 km with accepted members, update Fig. 3.16 /
   Fig. 3.17 data sources.

### Risks

- Implementation cost is high.
- COCO/Tor is MATLAB-based while the project is Python-first.
- Translating CR3BP equations, phase constraints, and Jacobi constraints into a
  torus BVP may take longer than the remaining thesis-report timeline.
- A formulation change may reveal that original McCarthy branch conventions
  differ from the current interpretation of mapping time, phase, or amplitude.

### Stop condition

Route B should not start as ad hoc code changes. It becomes active only after a
written method note defines:

- residual equations,
- continuation variables,
- phase constraints,
- acceptance thresholds,
- comparison target against current `max_abs_z = 10164.02309965055 km`.

## Route C: Finish A Paper-Level Reproduction Report First

### Goal

Prepare a thesis/group-meeting/paper-ready reproduction report that is honest
about reproduction levels instead of waiting for exact McCarthy numerical
equivalence everywhere.

### Classification scheme

Each figure should be assigned one of:

- numerical reproduction: computed numerical quantities directly support the
  figure and residuals are acceptable.
- physical-consistency baseline: the physical mechanism and local computation
  are valid, but the figure is not original-data equivalent.
- local overlay: the figure includes corrected local numerical evidence over a
  shape-match or proxy visual reference.
- proxy: schematic or trend geometry used to communicate structure, not a
  validated reproduction.

### Suitable for solving

- Master's opening report or group meeting presentation.
- A reproducibility appendix explaining what has and has not been reproduced.
- Project management: prevents Chapter 5 work from being built on rejected
  quasi-DRO candidates.
- Immediate documentation of Fig. 3.16 / Fig. 3.17 as partial physical-
  consistency baselines.

### Work plan

1. Use `data/computed/figure_validation_table.csv` as the source of truth for
   figure status.
2. Summarize the key audits:
   Fig. 3.10, Chapter 4 DG manifold, Chapter 3 quasi-DRO extension/PALC/
   bottleneck diagnostics.
3. Build a figure-status appendix listing each figure, data source, residual
   evidence, proxy usage, and next action.
4. State clearly that Fig. 3.16 and Fig. 3.17 are partial physical-consistency
   baselines, not full numerical reproductions.
5. Explain why Chapter 5 should remain a baseline/proxy layer until the
   high-amplitude quasi-DRO family is accepted.

### Risks

- The report cannot claim complete McCarthy 2018 reproduction.
- Some readers may expect exact original branch data; the report must explain
  why current evidence is still scientifically useful.
- Proxy figures must be labelled consistently to avoid overclaiming.

### Stop condition

Route C is complete when the project has a report package that includes:

- objective and scope,
- figure-by-figure reproduction status,
- numerical audit summaries,
- external resource inventory,
- next-step decision between Route A and Route B.

## Recommended Next Phase

The recommended sequence is:

1. Route C first: finish the reproduction-status report while the current
   evidence is fresh.
2. Route A in parallel: continue a bounded search for original McCarthy data and
   digitizable high-quality sources.
3. Route B only after the report defines the research question and acceptance
   gates for a formulation replacement.

This sequence preserves the value of the completed 54-figure coverage and avoids
spending more time on the already diagnosed fixed-mapping-time bottleneck before
the next formulation is chosen deliberately.
