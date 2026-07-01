"""Bounded Chapter 3 quasi-DRO PALC continuation diagnostic."""

from __future__ import annotations

import sys
from pathlib import Path

PROJECT_ROOT = Path(__file__).resolve().parents[1]
SRC = PROJECT_ROOT / "src"
if str(SRC) not in sys.path:
    sys.path.insert(0, str(SRC))

from qp_orbits.constants import SYSTEMS
from qp_orbits.corrected_dro_family import (
    _audit_values,
    _correction_from_member,
    _is_tight_fixed_mapping_correction,
    _member_from_correction,
    _palc_candidate_status,
    _palc_log_row,
    load_corrected_dro_family_csv,
    write_chapter3_quasi_dro_palc_family,
    write_chapter3_quasi_dro_palc_log,
    write_chapter3_quasi_dro_validation,
)
from qp_orbits.quasi_torus import (
    _fixed_mapping_pseudo_arclength_geometry,
    _lift_dro_fixed_mapping_correction,
    _trigonometric_interpolation_matrix,
    stroboscopic_curve_fixed_mapping_pseudo_arclength_correction,
    stroboscopic_curve_fixed_rotation_correction,
    stroboscopic_dro_invariant_curve_seed,
)


def main() -> None:
    system = SYSTEMS["earth_moon"]
    length_unit = system.length_unit_km or 1.0
    time_unit = system.time_unit_days or 1.0
    x0 = 1.0 - system.mu - 73800.0 / length_unit
    initial_ydot = 0.53
    initial_half_period = 14.75 / (2.0 * time_unit)

    extended_path = PROJECT_ROOT / "data" / "computed" / "chapter3_corrected_dro_fixed_mapping_family_extended.csv"
    family_path = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_family.csv"
    validation_path = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_validation.csv"
    log_path = PROJECT_ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_log.csv"

    family = list(load_corrected_dro_family_csv(extended_path))
    sources = ["original_local" if member.member < 5 else "accepted_extended" for member in family]
    logs: list[dict[str, str]] = []
    source_mapping_time_days = family[-1].mapping_time_days

    prev_m, cur_m = family[-2], family[-1]
    prev = _correction_from_member(
        prev_m,
        system,
        x0=x0,
        initial_ydot=initial_ydot,
        initial_half_period=initial_half_period,
    )
    cur = _correction_from_member(
        cur_m,
        system,
        x0=x0,
        initial_ydot=initial_ydot,
        initial_half_period=initial_half_period,
    )

    _, _, _, natural = _fixed_mapping_pseudo_arclength_geometry(prev, cur)
    for idx, frac in enumerate((0.15, 0.075), start=1):
        step = natural * frac
        try:
            candidate = stroboscopic_curve_fixed_mapping_pseudo_arclength_correction(
                prev,
                cur,
                step_size=step,
                max_iterations=4,
                tolerance=1e-8,
                constraint_tolerance=1e-10,
                max_step=0.03,
                max_rotation_step=0.003,
            )
            member, audit_row, monotone, accepted, reason = _palc_candidate_status(
                candidate,
                cur_m,
                system,
                source_mapping_time_days=source_mapping_time_days,
            )
        except Exception as exc:  # noqa: BLE001 - log numerical failures verbatim.
            candidate = None
            audit_row = None
            monotone = None
            accepted = False
            reason = str(exc)
        logs.append(
            _palc_log_row(
                attempt_id=f"palc_N41_small_step_{idx}",
                attempt_type="fixed_mapping_palc",
                source_previous_member=prev_m.member,
                source_current_member=cur_m.member,
                family_source="palc",
                target_rho=None,
                step_size=step,
                step_fraction_of_secant=frac,
                curve_samples=41,
                lifted_from_samples=None,
                target_samples=41,
                correction=candidate,
                system=system,
                source_mapping_time_days=source_mapping_time_days,
                converged=candidate is not None,
                accepted=accepted,
                rotation_monotone=monotone,
                audit_row=audit_row,
                failure_reason=reason,
                next_action=(
                    "accepted into PALC family"
                    if accepted
                    else "halve step and retry"
                    if idx == 1
                    else "try N=61 spectral lifting"
                ),
            )
        )
        if accepted and candidate is not None:
            family.append(_member_from_correction(len(family), candidate, system))
            sources.append("palc")
            prev, cur = cur, candidate
            prev_m, cur_m = family[-2], family[-1]
            break

    lifted_anchors: dict[str, object] = {}
    for label, source_member, source_correction in (
        ("previous", prev_m, prev),
        ("current", cur_m, cur),
    ):
        try:
            lifted = _lift_dro_fixed_mapping_correction(
                source_correction,
                x0=x0,
                samples=61,
                initial_ydot=initial_ydot,
                initial_half_period=initial_half_period,
                max_iterations=4,
                map_tolerance=1e-8,
                max_step=0.03,
            )
            quick = _is_tight_fixed_mapping_correction(lifted, system)
            if quick:
                lifted_anchors[label] = lifted
            audit_row = None
            audited = False
            if quick:
                audit_row, audited = _audit_values(
                    _member_from_correction(source_member.member, lifted, system),
                    system,
                )
            reason = "" if quick and audited else "spectral lift failed residual/Jacobi or audit threshold"
            logs.append(
                _palc_log_row(
                    attempt_id=f"lift_{label}_member_{source_member.member}_N61",
                    attempt_type="spectral_lift",
                    source_previous_member=prev_m.member,
                    source_current_member=cur_m.member,
                    family_source=sources[source_member.member],
                    target_rho=None,
                    step_size=None,
                    step_fraction_of_secant=None,
                    curve_samples=source_member.states.shape[0],
                    lifted_from_samples=source_member.states.shape[0],
                    target_samples=61,
                    correction=lifted,
                    system=system,
                    source_mapping_time_days=source_mapping_time_days,
                    converged=True,
                    accepted=bool(quick and audited),
                    rotation_monotone=None,
                    audit_row=audit_row,
                    failure_reason=reason,
                    next_action=(
                        "use as N=61 PALC anchor"
                        if quick and audited
                        else "record N=61 lift failure; try fixed-rotation fallback"
                    ),
                )
            )
        except Exception as exc:  # noqa: BLE001 - log numerical failures verbatim.
            logs.append(
                _palc_log_row(
                    attempt_id=f"lift_{label}_member_{source_member.member}_N61",
                    attempt_type="spectral_lift",
                    source_previous_member=prev_m.member,
                    source_current_member=cur_m.member,
                    family_source=sources[source_member.member],
                    target_rho=None,
                    step_size=None,
                    step_fraction_of_secant=None,
                    curve_samples=source_member.states.shape[0],
                    lifted_from_samples=source_member.states.shape[0],
                    target_samples=61,
                    correction=None,
                    system=system,
                    source_mapping_time_days=source_mapping_time_days,
                    converged=False,
                    accepted=False,
                    rotation_monotone=None,
                    audit_row=None,
                    failure_reason=str(exc),
                    next_action="record N=61 lift failure; try fixed-rotation fallback",
                )
            )

    if "previous" in lifted_anchors and "current" in lifted_anchors:
        lifted_prev = lifted_anchors["previous"]
        lifted_cur = lifted_anchors["current"]
        _, _, _, lifted_natural = _fixed_mapping_pseudo_arclength_geometry(
            lifted_prev,
            lifted_cur,
        )
        lifted_step = 0.10 * lifted_natural
        try:
            candidate = stroboscopic_curve_fixed_mapping_pseudo_arclength_correction(
                lifted_prev,
                lifted_cur,
                step_size=lifted_step,
                max_iterations=3,
                tolerance=1e-8,
                constraint_tolerance=1e-10,
                max_step=0.03,
                max_rotation_step=0.002,
            )
            member, audit_row, monotone, accepted, reason = _palc_candidate_status(
                candidate,
                cur_m,
                system,
                source_mapping_time_days=source_mapping_time_days,
            )
        except Exception as exc:  # noqa: BLE001 - log numerical failures verbatim.
            candidate = None
            audit_row = None
            monotone = None
            accepted = False
            reason = str(exc)
        logs.append(
            _palc_log_row(
                attempt_id="palc_N61_lifted_small_step_1",
                attempt_type="fixed_mapping_palc",
                source_previous_member=prev_m.member,
                source_current_member=cur_m.member,
                family_source="palc_lifted_N61",
                target_rho=None,
                step_size=lifted_step,
                step_fraction_of_secant=0.10,
                curve_samples=61,
                lifted_from_samples=41,
                target_samples=61,
                correction=candidate,
                system=system,
                source_mapping_time_days=source_mapping_time_days,
                converged=candidate is not None,
                accepted=accepted,
                rotation_monotone=monotone,
                audit_row=audit_row,
                failure_reason=reason,
                next_action=(
                    "accepted into PALC family"
                    if accepted
                    else "N=61 PALC candidate rejected; try fixed-rotation fallback"
                ),
            )
        )
        if accepted and candidate is not None:
            family.append(_member_from_correction(len(family), candidate, system))
            sources.append("palc_lifted_N61")
            prev, cur = lifted_cur, candidate
            prev_m, cur_m = family[-2], family[-1]

    fallback_prev, fallback_cur = prev, cur
    fallback_prev_m, fallback_cur_m = prev_m, cur_m
    for target_rho in (1.4445, 1.4455, 1.4465, 1.4480, 1.4500):
        try:
            seed = stroboscopic_dro_invariant_curve_seed(
                system.mu,
                x0=x0,
                initial_ydot=initial_ydot,
                initial_half_period=initial_half_period,
                vertical_amplitude=1e-4,
                samples=fallback_cur.corrected_states.shape[0],
                curve_samples=max(4 * fallback_cur.corrected_states.shape[0], 120),
            )
            fraction = (target_rho - fallback_cur.rotation_angle_rad) / (
                fallback_cur.rotation_angle_rad - fallback_prev.rotation_angle_rad
            )
            interpolation = _trigonometric_interpolation_matrix(
                fallback_prev.seed.phases,
                fallback_cur.seed.phases,
            )
            previous_states = interpolation @ fallback_prev.corrected_states
            initial_states = fallback_cur.corrected_states + fraction * (
                fallback_cur.corrected_states - previous_states
            )
            candidate = stroboscopic_curve_fixed_rotation_correction(
                seed,
                target_rotation_angle_rad=target_rho,
                initial_states=initial_states,
                phase_reference_states=initial_states,
                max_iterations=3,
                tolerance=1e-8,
                phase_tolerance=1e-10,
                max_step=0.03,
                max_state_step=1e-3,
            )
            member, audit_row, monotone, accepted, reason = _palc_candidate_status(
                candidate,
                fallback_cur_m,
                system,
                source_mapping_time_days=source_mapping_time_days,
            )
        except Exception as exc:  # noqa: BLE001 - log numerical failures verbatim.
            candidate = None
            audit_row = None
            monotone = None
            accepted = False
            reason = str(exc)
        logs.append(
            _palc_log_row(
                attempt_id=f"fixed_rotation_rho_{target_rho:.4f}",
                attempt_type="fixed_rotation_fallback",
                source_previous_member=fallback_prev_m.member,
                source_current_member=fallback_cur_m.member,
                family_source="fixed_rotation_fallback",
                target_rho=target_rho,
                step_size=target_rho - fallback_cur.rotation_angle_rad,
                step_fraction_of_secant=None,
                curve_samples=fallback_cur.corrected_states.shape[0],
                lifted_from_samples=None,
                target_samples=fallback_cur.corrected_states.shape[0],
                correction=candidate,
                system=system,
                source_mapping_time_days=source_mapping_time_days,
                converged=candidate is not None,
                accepted=accepted,
                rotation_monotone=monotone,
                audit_row=audit_row,
                failure_reason=reason,
                next_action=(
                    "accepted into PALC family"
                    if accepted
                    else "candidate rejected; continue Chapter 3 bottleneck diagnosis"
                ),
            )
        )
        if accepted and candidate is not None:
            family.append(_member_from_correction(len(family), candidate, system))
            sources.append("fixed_rotation_fallback")
            fallback_prev, fallback_cur = fallback_cur, candidate
            fallback_prev_m, fallback_cur_m = family[-2], family[-1]
            if family[-1].max_abs_z_km > 11000.0:
                break

    write_chapter3_quasi_dro_palc_family(family_path, tuple(family), tuple(sources))
    write_chapter3_quasi_dro_validation(validation_path, tuple(family), system)
    write_chapter3_quasi_dro_palc_log(log_path, tuple(logs))
    print(
        len(family),
        len(logs),
        f"{family[-1].rotation_angle_rad:.16g}",
        f"{family[-1].max_abs_z_km:.16g}",
        f"{family[-1].mean_jacobi:.16g}",
    )


if __name__ == "__main__":
    main()
