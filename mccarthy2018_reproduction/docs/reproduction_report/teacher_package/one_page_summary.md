# One Page Summary

The project reproduces the McCarthy 2018 quasi-periodic-orbit thesis at an
engineering-audit level: all 54 target figures have generated outputs, and each
figure is tracked by data source, residual/Jacobi evidence, proxy usage, and a
next action in `data/computed/figure_validation_table.csv`.

The most important recent update is Chapter 3 Route H. The accepted
fixed-mapping quasi-DRO source branch now reaches `14573.10318409037` km,
with `30` accepted rows above 10,500 km and
`29` above 11,000 km. Fig. 3.16 and Fig. 3.17 now use this
Route H source layer rather than the older local-only 10,164 km endpoint.

This does not mean the whole thesis has been fully numerically reproduced.
Original McCarthy branch data, appendix tables, and author code are still not
available in the repository. Several Chapter 4 and Chapter 5 figures remain
source-layer, baseline, local-overlay, or proxy-context results. The correct
claim is: the repository now has a stronger audited source layer for the hard
Chapter 3 quasi-DRO figures, while full-thesis equivalence remains a bounded
future-work target.
