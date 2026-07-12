# Chapter 3 Route H Fixed-Time Energy Projection Probe

## Result

- Status: `pass`
- Target Jacobi: `2.9221000`
- Accepted homotopy steps: `5/5`
- Final mapping time: `14.74932760227518 day`
- Mapping-time error: `0.000000e+00 day`
- Final mean Jacobi: `2.922099999989426`
- Final map residual: `4.576107e-10`
- Final Jacobi span: `8.813839e-12`
- Failure: `N/A`

## Interpretation

The initial state is a strict fixed-Jacobi solution with free mapping time. The
homotopy then moves mapping time toward the thesis fixed-time value while each STM
Newton correction simultaneously enforces map invariance, mean Jacobi, and phase.
Passing requires reaching the target time without relaxing the registered numerical
gates. The exploratory pointwise-Jacobi-span threshold is the Route H generator's
`2e-8`; promotion still requires spectral refinement below `1e-9`. This is a
projection probe for one Jacobi anchor, not yet the complete four-
anchor cold-start family.
