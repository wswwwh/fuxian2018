# Chapter 3 Route H Fixed-Time Energy Projection Probe

## Result

- Status: `fail`
- Target Jacobi: `2.9212000`
- Accepted homotopy steps: `12/13`
- Final mapping time: `14.79941724015211 day`
- Mapping-time error: `5.008964e-02 day`
- Final mean Jacobi: `2.921199999966733`
- Final map residual: `1.883856e-09`
- Final Jacobi span: `9.791878e-10`
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
