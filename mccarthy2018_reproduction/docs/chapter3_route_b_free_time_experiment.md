# Chapter 3 Route B Free-Time Experiment

## Purpose

This file records the minimal Route B numerical prototype for the quasi-DRO
endpoint: fixed mean Jacobi, free mapping time, and free rotation angle. It is a
diagnostic branch experiment only; it does not update Figures 3.16 or 3.17 and
does not modify the accepted fixed-mapping-time CSV files.

## Relation To Route B Note

The implementation follows `docs/route_b_formulation_note.md`: unknowns are the
`N` curve states, mapping time `T`, and rotation angle `rho`; residuals are the
stroboscopic map equation, one mean-Jacobi residual, and one curve-tangent phase
condition. Amplitude is reported as an output metric, not enforced.

## Input Endpoint

- Source: `data/computed/chapter3_quasi_dro_palc_family.csv`
- Member: `10`
- Curve samples: `61`
- Endpoint mapping time: `14.74932760227518` days
- Endpoint rho: `1.443877875293695` rad
- Endpoint mean Jacobi: `2.922288411389487`
- Endpoint max abs z: `10164.02309965055` km

## Correction-Only Result

The correction-only reproduction `passed the Route B audit gates`.

- Corrected mapping time: `14.74932758029392` days
- Mapping time drift: `-2.198125770291881e-08` days
- Corrected rho: `1.44387788665864` rad
- Rho drift: `1.136494476305927e-08` rad
- Map residual norm: `1.690056425583955e-12`
- Curve Jacobi span: `7.061018436615996e-14`
- One-map phase return error: `1.367700919397098e-12`
- Ten-return Jacobi span: `3.108624468950438e-15`

## Small-Step Continuation Result

no accepted member exceeded 10,500 km.

- Accepted member exceeds 10,500 km: `False`
- Accepted member exceeds 11,000 km: `False`
- Last accepted/diagnostic mapping-time drift: `0.0003256706895538031` days
- Last accepted/diagnostic rho drift: `-6.298383797398444e-06` rad

## Interpretation

Any nonzero mapping-time drift means these rows are diagnostic free-time Route B
members, not constant-mapping-time reproductions. If correction-only passes but
small-step continuation does not cross 10,500 km, the local bottleneck remains
unresolved by this minimal mean-Jacobi/free-time/free-rho prototype.

This experiment neither imports rejected fixed-rotation candidates nor uses
digitized Figure 3.17 extrapolation.

## Next Action

stop; finite Route B small-step budget did not reach 10,500 km; try phase-condition/scaling refinement or a smaller-family sanity check
