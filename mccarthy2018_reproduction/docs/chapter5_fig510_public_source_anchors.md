# Chapter 5 Figure 5.10 public-source anchors

## Scope

Figure 5.10 is an autonomous Earth-Moon CR3BP calculation. An epoch is not
applicable to the published case. The repository's `2020-06-15` epoch belongs
only to the separate DE421-initialized BCR4BP robustness extension.

## Recoverable published anchors

The thesis gives two feasible transfers:

| case | departure impulse | arrival impulse | total | flight time |
|---:|---:|---:|---:|---:|
| 1 | 48.3 m/s | 32.2 m/s | 80.5 m/s | 23 day |
| 2 | 51.3 m/s | 35.3 m/s | 86.6 m/s | 12.4 day |

The official Purdue AAS 19-329 paper adds that the initial arcs come from a
constant-frequency-ratio quasi-NRHO family anchored to a periodic NRHO with
lunar perilune radius `8065 km` and frequency ratio `5.0305`. The Figure 5.10
arcs are feasible solutions and are not the later SQP local optima.

Primary sources:

- Purdue AAS 19-329: <https://engineering.purdue.edu/people/kathleen.howell.1/Publications/Conferences/2019_AAS_McCHow.pdf>
- Purdue dissertation record: <https://docs.lib.purdue.edu/dissertations/AAI30502018/>

## Fields still unavailable

- the selected quasi-NRHO torus member and its full 6D invariant curve;
- the two torus/NRHO intersection phases;
- departure and arrival 6D states for both cases;
- the differential-correction variable and constraint vectors;
- SQP bounds, tolerances, and complete optimum states.

Therefore the public material supports published-metric and locked-projection
reproduction, but not raw-state identity. Repository phases `0.82`, `0.18`, and
`0.75` remain project choices until independently recovered.
