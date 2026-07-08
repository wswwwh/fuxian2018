# Chapter 3 Free-Time To Fixed-Time Projection Audit

## Scope

This audit starts from accepted high-amplitude free-time quasi-DRO states and
tries to project them to the McCarthy fixed mapping time while preserving the
source max-|z| amplitude through an explicit target-amplitude row.

It is diagnostic only and does not update Fig. 3.16 / Fig. 3.17.

## Configuration

- Minimum source amplitude: `10500.0` km
- Max candidates: `6`
- Fixed mapping time: `14.74932760227518` days
- Minimum target: `10500.0` km

## Outcome

- Rows evaluated: `6`
- Accepted fixed-time projections above 10,500 km: `0`
- Best projected max abs z: `11302.49205040196` km

## Rows

- `free_time_fixed_T_projection_01` from `free_time_parameter_aware_forward_from_5_6`: source `11302.5101159` km -> projected `11302.4920504` km, accepted `False`, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`
- `free_time_fixed_T_projection_02` from `bounded_05_E_amplitude_monitor_large_step`: source `11107.5414922` km -> projected `11107.5883755` km, accepted `False`, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`
- `free_time_fixed_T_projection_03` from `bounded_04_E_amplitude_monitor_large_step`: source `10968.3958868` km -> projected `10968.3965063` km, accepted `False`, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`
- `free_time_fixed_T_projection_04` from `bounded_03_E_amplitude_monitor_large_step`: source `10826.9007503` km -> projected `10826.8932663` km, accepted `False`, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`
- `free_time_fixed_T_projection_05` from `bounded_02_E_amplitude_monitor_large_step`: source `10681.8698257` km -> projected `10681.8664715` km, accepted `False`, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`
- `free_time_fixed_T_projection_06` from `bounded_01_E_amplitude_monitor_large_step`: source `10530.5957829` km -> projected `10530.5944393` km, accepted `False`, failed `gate_1_residual; gate_2_jacobi; gate_3_phase`

## Interpretation

An accepted row would be a candidate for independent branch continuation and
figure-source review. Rejected rows show that high-amplitude free-time states do
not survive this fixed-time target-amplitude projection under the current
corrector and audit gates.
