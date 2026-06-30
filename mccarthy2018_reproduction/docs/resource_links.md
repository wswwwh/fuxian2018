# Resource Links And Access Log

Date checked: 2026-06-30.

This file records the resources requested in
`../计划与目标/codex_mccarthy2018_resource_learning_plan.md` and classifies how
each resource supports a Python reproduction of McCarthy 2018.

## Access Summary

| Resource | URL or local path | Access status | Type | Role for reproduction | Direct Python implementation support | Algorithms or results connected to it | Notes |
|---|---|---:|---|---|---:|---|---|
| McCarthy 2018 thesis, Hammer record | https://hammer.purdue.edu/articles/thesis/Characterization_of_Quasi-Periodic_Orbits_for_Applications_in_the_Sun-Earth_and_Earth-Moon_Systems/7423658 | Success | Thesis record | Official thesis landing page and metadata | No | Full McCarthy 2018 target scope | The page is accessible and identifies the Purdue thesis record. |
| McCarthy 2018 thesis, local PDF | `C:/Users/wwh20/Desktop/复现论文/2018_McCarthy_拟周期轨道.pdf` | Success | Local PDF | Primary source for chapter structure, figures, equations, and algorithm narrative | No | CR3BP, STM, correction, stroboscopic map, invariant curves, torus families, DG stability, applications | Local file has 137 PDF pages. Used for table of contents, figure list, and selected algorithm pages. |
| McCarthy 2018 Purdue Engineering PDF URL | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Masters/2018_McCarthy.pdf | Failed | PDF URL | Intended direct PDF mirror | No | Same as local thesis PDF | The URL redirected to a Purdue "site under construction" page during this check. Do not treat it as currently accessible. |
| Olikara and Howell 2010 AAS paper | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2010_AAS_OliHow.pdf | Success | Conference paper PDF | Method ancestor for stroboscopic maps and invariant tori | No | Natural parameterization, invariant curve discretization, torus invariance equation, continuation, mapping time, rotation angle | Use for algorithm structure, not for direct data tables. |
| Olikara 2010 Master's thesis | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Masters/2010_Olikara.pdf | Success | Thesis PDF | More detailed source behind Olikara and Howell methods | No | Initialization from center eigenspaces, invariant curve correction, continuation | Useful when McCarthy gives only a compact description. |
| McCarthy and Howell 2019 AAS paper | https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2019_AAS_McCHow.pdf | Success | Conference paper PDF | Application context after the 2018 thesis | No | QPO trajectory arcs, quasi-DRO eclipse strategy, NRHO transfers, trajectory design use cases | Use to interpret Chapter 5 goals. It does not replace the thesis. |
| JPL Three-Body Periodic Orbits API documentation | https://ssd-api.jpl.nasa.gov/doc/periodic_orbits.html | Success | API documentation | Independent periodic-orbit validation source | Yes, for validation data | Earth-Moon DRO, halo, Lyapunov, vertical, axial families; fields include state, Jacobi, period, stability | In-app browser also opened this page successfully with title "Three-Body Periodic Orbits API". |
| JPL periodic orbits visualization tool | https://ssd.jpl.nasa.gov/tools/periodic_orbits.html | Success | Web tool | Visual inspection and manual cross-checking | No | Same families as API, especially DRO and halo family context | Page shell is accessible but the tool body depends on JavaScript loading. Good for manual sanity checks, not an automated dependency. |
| JPL Earth-Moon DRO API query sample | https://ssd-api.jpl.nasa.gov/periodic_orbits.api?sys=earth-moon&family=dro&periodunits=d&periodmin=10&periodmax=20 | Success | API data | Direct machine-readable validation data | Yes, validation only | Initial state, Jacobi constant, period, stability index | Returned source "NASA/JPL Three-Body Periodic Orbits API", version 1.0, count 689. Fields: `x,y,z,vx,vy,vz,jacobi,period,stability`. |
| CR3BP MATLAB Library | https://github.com/JackCrusoe47/CR3BP_MATLAB_Library | Success | GitHub repository | Algorithm reference for CR3BP and periodic-orbit workflows | No, MATLAB reference only | STM, Jacobi, Lagrange points, differential correction, monodromy, characteristic values, stability, continuation, DRO examples | Repository contains `CR3BP/`, `conversions/`, `database/`, `examples/`. Do not make this a project dependency. |
| heyoka.py periodic orbits notebook | https://bluescarni.github.io/heyoka.py/notebooks/Periodic%20orbits%20in%20the%20CR3BP.html | Success | Python notebook | Python implementation reference for CR3BP + STM propagation | Yes, optional reference | CR3BP equations, Jacobi constant, 42-dimensional state+STM, correction and continuation around periodic orbits | Valuable for checking the current SciPy implementation and possible high-accuracy experiments. |
| heyoka.py pseudo-arclength notebook | https://bluescarni.github.io/heyoka.py/notebooks/Pseudo%20arc-length%20continuation%20in%20the%20CR3BP.html | Success | Python notebook | Python implementation reference for pseudo-arclength continuation | Yes, optional reference | Continuation tangent, arclength constraint, Newton correction for families | Use as a reference design; keep the main implementation NumPy/SciPy unless heyoka is explicitly adopted. |

## Tool Access Notes

- In-app browser access succeeded and opened the JPL API documentation.
- Chrome access failed because the Codex Chrome Extension backend was unavailable. No extension installation or repair was attempted.
- Windows Computer Use access succeeded for a read-only app-list check.

## Resource Interpretation Rules

- Do not invent an official McCarthy 2018 code repository.
- Treat the CR3BP MATLAB Library as a reference for algorithms and naming, not as a main dependency.
- Treat the JPL API as a periodic-orbit validation database. It does not provide McCarthy's quasi-periodic torus families.
- The local McCarthy PDF is the primary thesis text until the Purdue Engineering direct PDF URL becomes accessible again.
