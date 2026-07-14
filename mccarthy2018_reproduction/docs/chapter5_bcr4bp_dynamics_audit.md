# Chapter 5 BCR4BP Dynamics Audit

## Purpose

This file validates the first high-fidelity interface layer: a bicircular
Sun-Earth-Moon dynamics kernel in the same normalized Earth-Moon rotating frame
used by the CR3BP code.

## Mean Parameters

- `mu`: `0.012150585609624`
- `sun_mass_parameter`: `328827.8707340966`
- `sun_distance`: `389.1724003642039`
- `sun_angular_rate`: `-0.9253083768906855`

## Gate Rows

- `C5-BCR4BP-CR3BP-REDUCTION`: status `pass`, metric `max_rhs_difference` = `0`, acceptance `true`
- `C5-BCR4BP-BARYCENTER-TIDE`: status `pass`, metric `barycenter_solar_acceleration_norm` = `0`, acceptance `true`
- `C5-BCR4BP-FINITE-RHS`: status `pass`, metric `finite_rhs_samples` = `9`, acceptance `true`
- `C5-BCR4BP-ROUTE-H-SHORT-PROPAGATION`: status `pass`, metric `route_h_short_propagation_state_span` = `0.04327160583983275`, acceptance `true`

## Decision

The BCR4BP dynamics kernel is available as a model-level building block. This
does not complete Chapter 5 high-fidelity reproduction: ephemeris-corrected
multiple shooting and optimized-transfer acceptance rows are still required
before promoted application figures can be claimed.
