# Chapter 5 active geometry family independent rerun audit

The strict target pair was reached at accepted family member 468 and then
audited twice with zero additional members from the committed checkpoint.
Both reruns used the same explicit high-resolution command parameters:

```text
--additional-members 0 --max-relative-y-step 1.0e-3
--time-slices 129 --phase-samples 256 --max-z-correction-km 0
--max-correction-iterations 60 --predictor-scale-cap 0 --max-retries 1
--regularization 1e-7 --energy-residual-scale 1 --geometry-residual-scale 1
--correction-damping 1 --retarget-current-jacobi
--jacobi-target-offset 3e-8 --project-predictor-z
--smooth-preconditioner-sharpness 1e8 --validate-full-torus-progress
```

Both reruns produced accepted=468, full-torus max |y|=659439.431 km,
full-torus max |z|=939944.305 km, and `target_pair_accepted=True`.

| Artifact | SHA-256 (rerun 1 = rerun 2) |
| --- | --- |
| `data/computed/chapter5_sun_earth_l1_active_geometry_family_audit.csv` | `49566ABBB62AA2AE04324B10445350422250CA0C5E3428ADC9A915B44A0F0852` |
| `data/computed/chapter5_sun_earth_l1_active_geometry_family_checkpoint.npz` | `C0457C593D904151E094B3812CC4CA6ABE9C126B5E6DC3753A8B9E57B8399479` |
| `docs/chapter5_sun_earth_l1_active_geometry_family_audit.md` | `D02F3EA9639552FC4510C798428500B3E07B4426E9A413CE671025EDE7AE1044` |

The checkpoint state hash (SHA-256 over the ordered numeric checkpoint fields)
is `3719c735bfdf1cc67f2a69ecc209922721b215261720065051bd4ca5ae18d36e`.

