# Chapter 3 Route H Fixed-Time Energy Projection Probe

## Result

- Status: `fail`
- Target Jacobi: `2.9225000`
- Accepted homotopy steps: `9/10`
- Final mapping time: `14.74895263403876 day`
- Mapping-time error: `-3.749682e-04 day`
- Final mean Jacobi: `2.922499953211897`
- Final map residual: `3.766925e-08`
- Final Jacobi span: `1.436629e-12`
- Failure: `fixed-time energy correction exhausted the minimum time step`

## Interpretation

The initial state is a strict fixed-Jacobi solution with free mapping time. The
homotopy then moves mapping time toward the thesis fixed-time value while each STM
Newton correction simultaneously enforces map invariance, mean Jacobi, and phase.
Passing requires reaching the target time without relaxing the registered numerical
gates. The exploratory pointwise-Jacobi-span threshold is the Route H generator's
`2e-8`; promotion still requires spectral refinement below `1e-9`. This is a
projection probe for one Jacobi anchor, not yet the complete four-
anchor cold-start family.
