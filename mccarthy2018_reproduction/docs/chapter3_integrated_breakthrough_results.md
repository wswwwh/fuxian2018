# Chapter 3 Integrated Breakthrough Results

## Scope

This run follows `docs/chapter3_integrated_breakthrough_strategy.md` Part 5:
parameter-aware prediction, bounded substeps, fixed-time two-phase solves, and
seven audit gates. Gate 7 is treated as a required pass in this campaign.

## Start

- Member: `10`
- Max abs z: `10164.0230997` km
- Rho: `1.44387787529`
- Fixed mapping time: `14.74932760227518` days

## Accepted Campaign Members

- member `11`: max z `10272.2467117` km, rho `1.44414965748`, source `bootstrap_fixed_time_projection`
- member `12`: max z `10271.3713848` km, rho `1.44414967144`, source `palc_native_3_substeps`

## Outcome

- Final accepted max z: `10271.3713848` km
- Best accepted max z: `10272.2467117` km
- Best attempted max z: `10275.769272440339` km
- Minimum target 10,500 km reached: `False`
- Stretch target 11,000 km reached: `False`
- Final accepted gate passes: `gate_1_residual, gate_2_jacobi, gate_3_phase, gate_4_rho_monotone, gate_5_amplitude, gate_6_mapping_time, gate_7_condition`
- Independent revalidation all passed: `False`
- Stop reason: `accepted forward step decreased amplitude from 10272.2467117 km to 10271.3713848 km`

## Recent Diagnostics

- `macro_1_attempt_1`: max z `10275.769272440339`, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`
- `macro_1_attempt_2`: max z `10275.322693202035`, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`
- `macro_1_attempt_3`: max z `10271.459516388064`, failed ``
- `macro_1_attempt_4`: max z `10271.379945605224`, failed ``
- `macro_1_attempt_5`: max z `10271.37138476799`, failed ``

## Output Files

- `data/computed/chapter3_integrated_breakthrough_candidates.csv`
- `data/computed/chapter3_integrated_breakthrough_revalidation.csv`
- `data/computed/chapter3_integrated_breakthrough_diagnostics.csv`

## Interpretation

This artifact is an integrated campaign audit. It does not update Fig. 3.16 or
Fig. 3.17 unless the minimum 10,500 km target and all seven gates are achieved
and independently revalidated.

The rho-target retry rows show whether explicit rotation targeting can push the
amplitude upward. Those rows are not accepted unless the residual, Jacobi, phase,
monotonicity, mapping-time, and condition gates all pass.
