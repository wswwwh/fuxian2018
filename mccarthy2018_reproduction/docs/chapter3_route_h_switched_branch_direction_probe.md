# Chapter 3 Route H Switched-Branch Direction Probe

## Result

- Status: `bounded_no_descent_direction`
- Fold smallest singular value: `1.818175e-10`
- Fold spectral gap: `8.844159e+03`
- Accepted direction probes: `4/8`
- Accepted Jacobi-descent probes: `0`
- Best local descent: N/A

## Interpretation

Two corrected roots are initialized on opposite sides of the strongly separated
fold null direction. Each root is then corrected at positive and negative rotation-
number offsets. A descent direction must pass the strict map, phase, and pointwise-
Jacobi gates and lower mean Jacobi by more than `1e-10`; smaller changes are treated
as fold-level numerical ambiguity.

A passing row identifies a local branch direction worth continuing, but it does not
yet prove coverage of the four Fig. 3.16 Jacobi anchors. That requires a persistent,
checkpointed continuation with target insertion and independent revalidation.
