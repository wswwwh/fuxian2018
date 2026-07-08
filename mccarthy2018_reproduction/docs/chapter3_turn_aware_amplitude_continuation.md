# Chapter 3 Turn-Aware Amplitude Continuation

## Scope

This is an experimental continuation route after the monotone-rho Part 5
campaign reached a local turn. It keeps fixed mapping time and the residual,
Jacobi, phase, amplitude-growth, mapping-time, and condition gates. It replaces
the original rho-monotonicity gate with a turn-aware branch parameter:
`max_abs_z_km` must increase.

This artifact does not update Fig. 3.16 / Fig. 3.17 unless the minimum target is
reached and the turn-aware revalidation rows pass.

## Start

- Start member: `11`
- Start max abs z: `10272.2467117` km
- Start rho: `1.44414965748`
- Fixed mapping time: `14.74932760227518` days

## Outcome

- Final max abs z: `10293.2467117` km
- Target max abs z: `10320` km
- Target reached: `False`
- Accepted turn-aware steps: `11`
- Revalidation all passed: `True`
- Route status: `bounded_blocker_for_current_amplitude_chart`
- Stop reason: `no turn-aware acceptable amplitude step at stage 12`

## Accepted Steps

- `stage_1_step_2km`: max z `10274.2467117` km, dz `2` km, drho `-4.2419730617e-08`
- `stage_2_step_2km`: max z `10276.2467117` km, dz `2` km, drho `-4.3770190139e-08`
- `stage_3_step_2km`: max z `10278.2467117` km, dz `2` km, drho `-4.53805706346e-08`
- `stage_4_step_2km`: max z `10280.2467117` km, dz `2` km, drho `-4.7353111654e-08`
- `stage_5_step_2km`: max z `10282.2467117` km, dz `1.99999999999` km, drho `-4.98486834033e-08`
- `stage_6_step_2km`: max z `10284.2467117` km, dz `2` km, drho `-5.31928601166e-08`
- `stage_7_step_2km`: max z `10286.2467117` km, dz `2` km, drho `-5.79171468562e-08`
- `stage_8_step_2km`: max z `10288.2467117` km, dz `2` km, drho `-6.53394329753e-08`
- `stage_9_step_2km`: max z `10290.2467117` km, dz `2` km, drho `-7.91077787721e-08`
- `stage_10_step_2km`: max z `10292.2467117` km, dz `2` km, drho `-1.15881324758e-07`
- `stage_11_step_1km`: max z `10293.2467117` km, dz `0.999999999918` km, drho `-7.54124502844e-08`

## Output Files

- `data/computed/chapter3_turn_aware_amplitude_continuation.csv`
- `data/computed/chapter3_turn_aware_amplitude_revalidation.csv`
- `data/computed/chapter3_turn_aware_amplitude_states.npz`

## Interpretation

If this route reaches 10,500 km with revalidation, it supports replacing rho
monotonicity with a turn-aware branch coordinate for the high-amplitude
fixed-time family. If the route status is
`bounded_blocker_for_current_amplitude_chart`, the current amplitude chart is not
enough and the next attempt should change the continuation chart rather than
only shrinking the step size.
