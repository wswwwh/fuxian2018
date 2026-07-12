# Chapter 3 Route H Fixed-Time Energy Projection Probe

## Result

- Status: `pass`
- Target Jacobi: `2.9212000`
- Accepted homotopy steps: `37/37`
- Spectral lifts: `4`
- Final curve samples: `105`
- Final mapping time: `14.74932760227518 day`
- Mapping-time error: `0.000000e+00 day`
- Final mean Jacobi: `2.921199999991476`
- Final map residual: `8.439739e-10`
- Final Jacobi span: `3.958118e-10`
- Failure: `N/A`
- Final curve-state artifact: `data\computed\chapter3_route_h_fixed_time_energy_states_2p9212.csv`

## Interpretation

The initial state is a strict fixed-Jacobi solution with free mapping time. The
homotopy then moves mapping time toward the thesis fixed-time value while each STM
Newton correction simultaneously enforces map invariance, mean Jacobi, and phase.
Passing requires reaching the target time without relaxing the registered numerical
gates. The exploratory pointwise-Jacobi-span threshold is the Route H generator's
`2e-8`; promotion still requires spectral refinement below `1e-9`. This is a
projection probe for one Jacobi anchor, not yet the complete four-
anchor cold-start family.
