# Chapter 5 Optimized Transfer Audit

## Purpose

This audit closes the Chapter 5 optimization interface at the Route H/BCR4BP
source layer. It performs a deterministic grid search over accepted Route H
insertion phase and short transfer time, uses BCR4BP velocity correction to
satisfy the endpoint position defect, and ranks accepted transfers by delta-v.

## Acceptance

- Accepted optimized rows: `25` / `25`
- Position-defect threshold: `1e-09`
- Delta-v threshold: `1.0` m/s
- Best delta-v: `0.1374941742891632` m/s
- Best phase index: `0`
- Best normalized time of flight: `0.03`

## Top Accepted Rows

- rank `1` phase `0`, tof `0.03`: delta-v `0.1374941742891632` m/s, defect `1.454778958530722e-14`
- rank `5` phase `10`, tof `0.03`: delta-v `0.1386851776849954` m/s, defect `2.756222643054693e-14`
- rank `2` phase `20`, tof `0.03`: delta-v `0.1379470885382157` m/s, defect `2.758861371332324e-14`
- rank `3` phase `30`, tof `0.03`: delta-v `0.1381301699847316` m/s, defect `1.701455448191082e-14`
- rank `4` phase `40`, tof `0.03`: delta-v `0.1386011888148039` m/s, defect `2.593536238403362e-14`

## Decision

This is an auditable high-fidelity/optimization source-layer result, not a full
replacement of the thesis optimized transfer figures. It supplies accepted
optimized rows and a reproducible objective for downstream Chapter 5 figure
promotion.
