# Chapter 3 Multi-Coordinate PALC Continuation

## Scope

This is a short continuation audit for the full-vector PALC chart seeded from
the turn-aware amplitude endpoint. It is diagnostic only and does not update
Fig. 3.16 / Fig. 3.17.

## Outcome

- Attempts: `8`
- Accepted steps: `2`
- Final max abs z: `10293.6651411` km
- Stop reason: `no acceptable PALC step at stage 3`

## Rows

- `stage_1_scale_1`: z `10293.6573307` km, dz `0.41061899992` km, accepted `True`, failed ``
- `stage_2_scale_1`: z `10293.4763365` km, dz `-0.18099420523` km, accepted `False`, failed `turn_gate_4_amplitude_monotone`
- `stage_2_scale_0.5`: z `10293.6376145` km, dz `-0.0197161644955` km, accepted `False`, failed `turn_gate_4_amplitude_monotone`
- `stage_2_scale_0.25`: z `10293.6651411` km, dz `0.00781036049011` km, accepted `True`, failed ``
- `stage_3_scale_1`: z `10293.6360002` km, dz `-0.0291408505364` km, accepted `False`, failed `turn_gate_4_amplitude_monotone`
- `stage_3_scale_0.5`: z `10293.654987` km, dz `-0.0101540809992` km, accepted `False`, failed `turn_gate_4_amplitude_monotone`
- `stage_3_scale_0.25`: z `10293.6611677` km, dz `-0.00397335979505` km, accepted `False`, failed `turn_gate_4_amplitude_monotone`
- `stage_3_scale_0.1`: z `10293.6638166` km, dz `-0.00132446761199` km, accepted `False`, failed `turn_gate_4_amplitude_monotone`

## Interpretation

This chart can step beyond the target-amplitude endpoint, but the local
amplitude gain collapses rapidly. If it stalls with only amplitude-monotonicity
failures, the next chart must change the continuation direction or add a more
explicit multi-coordinate constraint rather than only shrinking the PALC scale.
