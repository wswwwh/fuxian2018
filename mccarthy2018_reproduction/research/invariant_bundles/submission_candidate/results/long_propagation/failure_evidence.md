# Stage H4 boundary and retry evidence

- Non-accepted final rows retained: 4
- Superseded initial attempts retained: 4

- h4_long_stable_em_halo_12p40_n45 / ordered_partial_real_schur_tracking / sign=1: boundary - sampled_secondary_physical_radius_crossing (secondary minimum 997.672 km)
- h4_long_stable_em_halo_12p40_n45 / qr_svd_shifted_cocycle_iteration / sign=1: boundary - sampled_secondary_physical_radius_crossing (secondary minimum 997.672 km)
- h4_long_stable_em_vertical_12p66_n57 / ordered_partial_real_schur_tracking / sign=-1: boundary - sampled_secondary_physical_radius_crossing (secondary minimum 1481.301 km)
- h4_long_stable_em_vertical_12p66_n57 / qr_svd_shifted_cocycle_iteration / sign=-1: boundary - sampled_secondary_physical_radius_crossing (secondary minimum 1481.301 km)

Every initial high-drift close-approach attempt is retained in
long_propagation_attempts.csv. A tighter retry improves numerical
conservation but does not erase the physical-radius boundary.
