# Chapter 3 Multi-Coordinate PALC Probe

## Scope

This diagnostic tests a full-vector PALC chart seeded from the archived
turn-aware amplitude states. It is the first probe of the proposed
multi-coordinate continuation route and does not update Fig. 3.16 / Fig. 3.17.

## Outcome

- Attempts: `6`
- Accepted PALC steps: `6`
- Best solved max abs z: `10293.657330703607` km

## Rows

- `pair_1_scale_0.25`: solved max z `10293.4022423` km, dz `0.155530642831` km, accepted `True`, failed ``
- `pair_1_scale_0.5`: solved max z `10293.5225618` km, dz `0.275850124021` km, accepted `True`, failed ``
- `pair_1_scale_1`: solved max z `10293.6573307` km, dz `0.41061899992` km, accepted `True`, failed ``
- `pair_2_scale_0.25`: solved max z `10292.6088142` km, dz `0.362102453202` km, accepted `True`, failed ``
- `pair_2_scale_0.5`: solved max z `10292.9194695` km, dz `0.672757758331` km, accepted `True`, failed ``
- `pair_2_scale_1`: solved max z `10293.3859916` km, dz `1.13927988196` km, accepted `True`, failed ``

## Interpretation

Accepted rows would justify promoting this chart into a longer continuation
campaign with independent revalidation. If all rows fail residual/Jacobi/phase
or fail to increase amplitude, the simple full-vector PALC chart is not enough
to escape the current 10,293 km fixed-time frontier.
