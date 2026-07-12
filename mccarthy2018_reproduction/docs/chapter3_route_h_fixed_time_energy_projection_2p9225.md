# Chapter 3 Route H Fixed-Time Energy Projection Probe

## Result

- Status: `fail`
- Target Jacobi: `2.9225000`
- Accepted homotopy steps: `11/12`
- Spectral lifts: `2`
- Final curve samples: `81`
- Final mapping time: `14.74895761337353 day`
- Mapping-time error: `-3.699889e-04 day`
- Final mean Jacobi: `2.922499854295125`
- Final map residual: `2.215236e-06`
- Final Jacobi span: `1.447731e-11`
- Failure: `fixed-time energy correction exhausted the minimum time step and maximum samples N=81`
- Final curve-state artifact: `data\computed\chapter3_route_h_fixed_time_energy_states_2p9225.csv`

## Interpretation

The initial state is a strict fixed-Jacobi solution with free mapping time. The
homotopy then moves mapping time toward the thesis fixed-time value while each STM
Newton correction simultaneously enforces map invariance, mean Jacobi, and phase.
Passing requires reaching the target time without relaxing the registered numerical
gates. The exploratory pointwise-Jacobi-span threshold is the Route H generator's
`2e-8`; promotion still requires spectral refinement below `1e-9`. This is a
projection probe for one Jacobi anchor, not yet the complete four-
anchor cold-start family.
