# Chapter 3 Route B PALC Safeguard Sweep

## Scope

This diagnostic targets the smaller quasi-vertical sanity case that blocked a
stronger Route B fixed-time BVP/PALC claim. It does not target the Fig. 3.16 /
Fig. 3.17 10,500 km or 11,000 km gates, does not update any accepted branch CSV,
and does not update figure sources.

## Endpoint Residual Controls

- member 0: accepted `True`, map max `2.19829e-10`, condition `1.54802e+12`
- member 1: accepted `True`, map max `2.84975e-10`, condition `1.62533e+12`
- member 2: accepted `True`, map max `3.89785e-10`, condition `1.73939e+12`

All checked smaller-family endpoint members are reproducible by the current BVP
assembly. This means the smaller-family failure is not a basic residual
assembly failure.

## PALC Predictor And Parameter Sweep

- `existing_full_secant_current_parameters`: accepted `False`, map max `3.01013e-05`, amp error `-1.96868` km, rho error `0.0072307`, reason `maximum iterations reached`
- `z_state_rho_matched_current_parameters`: accepted `False`, map max `3.49969e-07`, amp error `-0.0283167` km, rho error `7.1506e-05`, reason `maximum iterations reached`
- `z_state_rho_matched_target_parameters`: accepted `True`, map max `8.06409e-09`, amp error `-0.00837994` km, rho error `2.20417e-05`, reason `none`
- `target_state_predictor_target_parameters`: accepted `True`, map max `3.89785e-10`, amp error `0` km, rho error `0`, reason `none`

The existing full-secant/current-parameter policy remains accepted
`False`. Its map residual max is
`3.01013e-05`.

The component-matched state/rho predictor with target mapping time and target
Jacobi is accepted `True` with map residual max
`8.06409e-09`.

The target-state control is accepted `True` with map residual
max `3.89785e-10`.

## Interpretation

Accepted PALC cases in this sweep: `2`.

The previous smaller-family PALC failure is best interpreted as a predictor and
external-parameter policy issue, not as proof that the BVP residual cannot
represent the known neighbor. In this family, using current-member mapping time
and a single full secant is too weak, while aligning the predictor with the
target member's mapping time and mean Jacobi restores the audit gates.

For the quasi-DRO bottleneck this does not justify a Fig. 3.16 / Fig. 3.17
update. It does justify the next implementation direction: promote mapping time
and continuation parameter handling into the local PALC formulation, or add a
bounded parameter-aware predictor before attempting any wider fixed-time
campaign.
