# Teacher Package README

## Current Status

This package summarizes the current McCarthy 2018 reproduction state. The
project has one engineered output for all 54 target figures and auditable CSV
evidence for the main numerical layers, but it should not be described as a
complete numerical equivalence reproduction of the full thesis.

Route H is now the current Chapter 3 quasi-DRO source-layer result:

- accepted Route H validation rows: `30`
- best fixed-time quasi-DRO max abs z: `14573.10318409037` km
- rows above 10,500 km: `30`
- rows above 11,000 km: `29`
- max map residual: `6.469474407020314e-10`
- max one-map Jacobi drift: `7.760059261840979e-11`

## Recommended Reading Order

1. `one_page_summary.md`
2. `key_results_table.md`
3. `../figure_status_appendix.md`
4. `../proxy_usage_appendix.md`
5. `../qa_for_group_meeting.md`

## Boundaries

- Do not call the whole repository a complete McCarthy 2018 numerical reproduction.
- Do not treat digitized Fig. 3.17 or faint reference trends as raw branch data.
- Do not describe Route H Chapter 4/5 source-layer artifacts as full replacement
  for every original thesis figure.
- Use `data/computed/figure_validation_table.csv` and
  `data/computed/mccarthy2018_staged_goal_gate_status.csv` as the current
  machine-readable status sources.
