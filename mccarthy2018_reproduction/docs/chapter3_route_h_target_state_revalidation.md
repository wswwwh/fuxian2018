# Chapter 3 Route H Target-State Independent Revalidation

## Result

- Passed targets: `4/4`
- Total independently propagated curve nodes: `264`
- Worst endpoint map residual: `8.439373e-10`
- Worst endpoint Jacobi drift: `2.220446e-15`
- Worst initial curve Jacobi span: `3.958118e-10`

## Method

Every stored curve node is re-integrated for one mapping time with `rtol=2e-11`,
`atol=2e-13`, and `max_step=5e-3`. The endpoint is compared with an independently
constructed trigonometric rotation target. This audit does not read cached mapped
states or accept the Newton solver's own residual history.

The paper-precision target tolerance remains `5e-5` in Jacobi; numerical endpoint
map and Jacobi-drift gates are `2e-9` and `1e-9`, respectively.
