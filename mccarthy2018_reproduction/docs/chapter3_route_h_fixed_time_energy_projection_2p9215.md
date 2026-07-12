# Chapter 3 Route H Fixed-Time Energy Projection Probe

## Result

- Status: `fail`
- Target Jacobi: `2.9215000`
- Accepted homotopy steps: `15/16`
- Final mapping time: `14.76213494614396 day`
- Mapping-time error: `1.280734e-02 day`
- Final mean Jacobi: `2.921499999966893`
- Final map residual: `1.933560e-09`
- Final Jacobi span: `9.596230e-10`
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
