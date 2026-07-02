# Chapter 3 Integrated Breakthrough Strategy for 10,500 km Quasi-DRO Bottleneck

## 👋 Introduction for Codex

This document outlines a **complete, integrated approach** to break through the 10,500 km quasi-DRO continuation bottleneck. The strategy combines three proven techniques from earlier Route B diagnostics into a single coherent campaign.

**Current status:**
- Fixed-time endpoint: **10,164 km** (member 10, rho = 1.4439, N=61)
- Target: **≥10,500 km** (minimum), ideally **11,000 km**
- Why we're stuck: NOT a physics problem, but a **parameterization and Newton basin issue**
- Why we know it's solvable: Parameter-aware PALC reached **11,302 km** in free-time mode

---

## 🔍 Part 1: Root Cause Analysis – Why Are We Stuck at 10,164 km?

### The Evidence

1. **Free-time PALC succeeded beyond 11,000 km:**
   - By releasing the mapping-time constraint, parameter-aware PALC reached `max_abs_z = 11,302.5 km`
   - Residual was excellent: `5.28e-12`
   - **Conclusion:** The physics allows solutions beyond 10,500 km

2. **Fixed-time projection of free-time member gave 10,274 km:**
   - Projection of the 11,302 km free-time candidate back to fixed mapping-time → `10,274.98 km`
   - Residual: `1.21e-11` (high quality)
   - **Conclusion:** High-amplitude fixed-time solutions exist nearby

3. **Bounded substeps proved Newton basin issue:**
   - Single large step from member 10 → failure (full secant prediction overshoots)
   - Same step split into 3 micro-steps → success (each sub-step lands in Newton basin)
   - **Conclusion:** The Newton corrector CAN solve high-amplitude orbits, but INITIAL GUESS QUALITY is critical

### The Root Problem

At `rho ≈ 1.44388` (near current endpoint), three factors conspire:

1. **Small Newton Basin**
   - The nonlinear map near rho~1.444 is tightly curved
   - Newton's method requires initial guess within ~0.01 rho distance to converge
   - Current full-secant predictor ignores mapping-time constraint → overshoots → lands outside basin

2. **Mapping-Time Constraint Mismatch**
   - McCarthy fixed mapping-time to `14.74932760227518` days
   - When we do full-secant PALC, we treat this as a free variable (implicitly)
   - The Jacobian system has a "missing" mapping-time row → rank deficiency and ill-conditioning
   - Condition number explodes to `~1e10`

3. **Predictor Strategy Failure**
   - Current PALC uses pure state-space secant: `state_new = state_old + α * (state_old - state_prev)`
   - This ignores physical constraints:
     - Mapping-time should stay fixed
     - Mean Jacobi should change smoothly
     - Rho increment should be bounded
   - Result: Overshooting in high-amplitude region

### Why Three Earlier Diagnostics Succeeded

| Experiment | What Worked | Why |
|-----------|------------|-----|
| **Parameter-aware PALC** | Reached 11,302 km (free-time) | Predictor explicitly controlled rho and Jacobi increments; state interpolation respected constraints |
| **Bounded substeps** | Recovered 8→9; added 1.5 km | Small steps → each lands in Newton basin; midpoint checks catch failures early |
| **Two-phase overditioned** | Improved condition from 1e10 to 1e8 | Explicit phase-gauge handling + explicit mapping-time row prevented artificial rank loss |

---

## 💡 Part 2: The Integrated Solution – Three Components Working Together

### Component 1: Parameter-Aware Predictor (Replaces Full Secant)

**Current approach (fails):**
```
state_new = state_old + secant_direction × step_size
```
→ Ignores constraints → overshoots Newton basin

**New approach (constrained prediction):**
```
1. Input: prev_state, prev_rho, target_rho_increment (e.g., +0.00005 rad)
2. Key constraint: Mapping-time stays FIXED at 14.74932760227518 days
3. Prediction strategy:
   a) Interpolate state based on rho change (not blind extrapolation)
   b) Scale amplitudes proportionally to rho
   c) Preserve phase structure
   d) If Fourier tail is large, apply spectral lifting
4. Output: predicted_state that respects all constraints
```

**Why this works:**
- Keeps initial guess **close to true solution** → within Newton basin
- Respects **physics constraint** (fixed mapping-time)
- Avoids **overshooting** near tightly curved regions

**Pseudocode:**
```python
def parameter_aware_predictor(
    prev_state,
    prev_rho,
    prev_mean_jacobi,
    target_rho_increment,      # e.g., 0.00005 rad
    mapping_time_fixed         # 14.74932760227518 days
):
    """
    Replace full-secant with constrained interpolation.
    
    Key idea: Instead of treating state as pure continuation variable,
    constrain it via rho increment + physical continuity.
    """
    
    # Linear interpolation weight (damped, not full secant)
    alpha = target_rho_increment / (expected_max_rho_change)
    alpha = min(alpha, 0.1)  # Never extrapolate >10% of prev step
    
    # Predicted state via controlled interpolation
    # (details: scale Fourier amplitudes by rho change, preserve phases)
    predicted_state = prev_state + alpha * smooth_interpolation(prev_state)
    
    # Apply spectral lifting if needed (Fourier tail too large)
    if fourier_tail_energy(predicted_state) > threshold:
        predicted_state = lift_to_higher_fourier(predicted_state, N_new=71)
    
    target_rho = prev_rho + target_rho_increment
    target_mean_jacobi = prev_mean_jacobi  # Hold constant to first order
    
    return predicted_state, target_rho, target_mean_jacobi
```

### Component 2: Bounded Substep Advancement (Guarantees Newton Convergence)

**Current approach (fails):**
```
Attempt: prev_member → target_member (single large rho step)
Newton fails to converge → stop
```

**New approach (divide and conquer):**
```
Step from prev_member to target_member:
  1. Divide target rho_increment into 3 equal pieces
  2. Substep 1: prev → intermediate_1 (rho += delta/3)
  3. Substep 2: intermediate_1 → intermediate_2 (rho += delta/3)
  4. Substep 3: intermediate_2 → target (rho += delta/3)
  
Each substep uses:
  - Parameter-aware predictor (small increment → tighter Newton basin)
  - Two-phase conditioning (better conditioning)
  - Multiple gates (catch failures early)
  
If any substep fails:
  - Diagnostic: which substep failed? why?
  - Decision: reduce further, or stop branch?
```

**Why this works:**
- **Reduces Newton basin requirement by ~3x** (mathematically proven for well-conditioned systems)
- **Proven effective**: Route B used this to recover 8→9 step
- **Natural stopping point**: Early exit if branch terminates
- **Diagnostic value**: Tells us exactly where branch ends

**Pseudocode:**
```python
def bounded_substep_advancement(
    current_member,
    target_rho_delta=0.00005,      # Total rho change
    max_substeps=3,
    mapping_time_fixed=14.74932760227518
):
    """
    Advance via micro-steps instead of single large step.
    """
    current = current_member
    substep_size = target_rho_delta / max_substeps
    
    for i_substep in range(max_substeps):
        target_rho = current.rho + substep_size
        
        # Use parameter-aware predictor for this micro-step
        guess_state = parameter_aware_predictor(
            prev_state=current.state,
            prev_rho=current.rho,
            prev_mean_jacobi=current.mean_jacobi,
            target_rho_increment=substep_size,
            mapping_time_fixed=mapping_time_fixed
        )
        
        # Solve fixed-time BVP with two-phase conditioning
        result = solve_fixed_time_bvp(
            initial_guess=guess_state,
            target_rho=target_rho,
            fixed_mapping_time=mapping_time_fixed,
            fourier_order=61,
            assembly_convention="two_phase_overdetermined"
        )
        
        # Check gates (residual, Jacobi, phase, etc.)
        gates = check_audit_gates(result, current)
        if not gates['all_pass']:
            return None  # Substep failed; branch ends or needs adjustment
        
        current = result
    
    return current
```

### Component 3: Two-Phase Overdetermined Conditioning (Fixes Ill-Conditioning)

**Current problem:**
- One-phase PALC system: `rank_deficient` due to missing explicit mapping-time row
- Condition number: `~4.8e10` (extremely ill-conditioned)
- Result: Newton's method converges slowly or fails

**New approach (explicit two-phase system):**
```
Phase 1: Map closure equations
  - Residual for each Fourier component (state must satisfy stroboscopic map)
  - Jacobi constant constraint (mean or pointwise)
  - Rotation angle (rho) constraint
  Total: ~360 equations

Phase 2: PALC constraint
  - (state - state_prev) · tangent_direction = arc_length
  - Explicit pseudo-arclength continuation equation
  Total: 1 equation

Full system: 361 equations, 367 unknowns → overdetermined, full rank
Solve via least-squares (SVD or QR decomposition)
```

**Why this works:**
- **Explicit mapping-time handling**: Phase 1 includes map closure with fixed mapping-time
- **Rank-full system**: Overdetermined system is rank-full (no artificial deficiency)
- **Better conditioning**: Condition number improves from `1e10 → 1e8`
- **Newton converges faster**: Better Jacobian → faster corrections

**Key insight**: Route B diagnostics showed conditioning improved dramatically under `two_phase_overdetermined` convention.

---

## 🎯 Part 3: How the Three Components Integrate

```
                    ┌─────────────────────────────────┐
                    │  Start: Member 10 at 10,164 km  │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Set target: rho +0.00005   │
                    │  (parameter-aware knows:     │
                    │   - mapping_time is fixed    │
                    │   - mean_jacobi is constant) │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼───────────────────┐
                    │  Bounded Substeps: 3 pieces      │
                    │  ├─ Substep 1: rho +delta/3      │
                    │  │  ├─ Use parameter-aware      │
                    │  │  │  predictor                 │
                    │  │  ├─ Solve with two-phase      │
                    │  │  └─ Check gates               │
                    │  ├─ Substep 2: rho +delta/3      │
                    │  │  (same as above)              │
                    │  └─ Substep 3: rho +delta/3      │
                    │     (same as above)              │
                    └──────────────┬───────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  All substeps passed?        │
                    │  ├─ YES → new current member │
                    │  │        (now at ~10,169 km) │
                    │  └─ NO  → diagnostic report  │
                    │           (branch blocked?)   │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Repeat: target rho +0.00005 │
                    │  (now: 10,169 → 10,174 km)   │
                    │  Continue until:              │
                    │  ├─ 10,500 km (must reach)    │
                    │  ├─ 11,000 km (stretch goal)  │
                    │  └─ Some gate fails           │
                    └──────────────┬──────────────┘
                                   │
                    ┌──────────────▼──────────────────┐
                    │  Adaptive Fourier (if needed)   │
                    │  If Newton fails:               │
                    │  ├─ Lift N: 61 → 71            │
                    │  ├─ Retry substep              │
                    │  └─ Continue                    │
                    └──────────────┬──────────────────┘
                                   │
                    ┌──────────────▼──────────────┐
                    │  Final: Member N at ≥10,500 │
                    │  All gates passed.          │
                    │  SUCCESS!                    │
                    └──────────────────────────────┘
```

---

## ✅ Part 4: Audit Gates – Quality Assurance for Every Step

To ensure every accepted member is a true McCarthy reproduction, we apply **7 independent gates**:

### Gate 1: Map Residual
```
Requirement: map_residual_max < 1e-9
Why: Stroboscopic map closure must be satisfied to high precision
Current member 10: 7.89e-10 ✓
```

### Gate 2: Jacobi Constant
```
Requirement: 
  - curve mean Jacobi span < 1e-10
  - one-map Jacobi drift < 1e-9
  - ten-return Jacobi span < 1e-14
Why: Jacobi constant is conserved in CR3BP; drift indicates integration error
Current member 10: all pass ✓
```

### Gate 3: Phase Return Error
```
Requirement: phase_return_error < 1e-10
Why: Phase should close exactly after one map return
Current member 10: 2.12e-10 ✓
```

### Gate 4: Rotation Monotonicity
```
Requirement: rho > prev_member.rho (strictly increasing)
Why: Continuation parameter must be monotone; otherwise branch loops
```

### Gate 5: Amplitude Growth
```
Requirement: max_z >= prev_max_z - 1.0 km (within 1 km tolerance)
Why: Don't accept solutions that regress in amplitude
```

### Gate 6: Mapping-Time Integrity
```
Requirement: abs(mapping_time - 14.74932760227518) < 1e-10 days
Why: McCarthy fixed mapping-time; must hold exactly
```

### Gate 7: Jacobian Conditioning (Diagnostic)
```
Requirement: condition_number < 1e9 (WARNING if exceeded, not hard gate)
Why: Extremely ill-conditioned systems are numerically unreliable
Route B result: improved to ~1e8 with two-phase ✓
```

**Logic:**
```python
def check_audit_gates(candidate, prev_member):
    """
    Returns dict with 7 boolean results.
    Candidate ACCEPTED only if gates 1–6 all pass.
    Gate 7 is diagnostic only (generates WARNING if failed).
    """
    results = {
        'gate_1_residual': candidate.map_residual_max < 1e-9,
        'gate_2_jacobi': (
            candidate.jacobi_mean_span < 1e-10 and
            candidate.jacobi_one_map_drift < 1e-9 and
            candidate.jacobi_ten_return_span < 1e-14
        ),
        'gate_3_phase': candidate.phase_return_error < 1e-10,
        'gate_4_rho_monotone': candidate.rho > prev_member.rho,
        'gate_5_amplitude': candidate.max_z >= prev_member.max_z - 1.0,
        'gate_6_mapping_time': abs(candidate.mapping_time - 14.74932760227518) < 1e-10,
        'gate_7_condition': candidate.condition_number < 1e9
    }
    
    results['all_pass'] = all([
        results['gate_1_residual'],
        results['gate_2_jacobi'],
        results['gate_3_phase'],
        results['gate_4_rho_monotone'],
        results['gate_5_amplitude'],
        results['gate_6_mapping_time']
    ])
    
    return results
```

---

## 📋 Part 5: Step-by-Step Implementation Plan for Codex

### Phase 0: Preparation (0.5 day)
- [ ] Review existing Route B code:
  - `scripts/run_chapter3_route_b_parameter_aware_palc.py` (predictor logic)
  - `scripts/run_chapter3_route_b_bvp_palc_stabilization.py` (two-phase system)
  - `scripts/prototype_chapter3_route_b_bvp_palc_neighborhood.py` (bounded substeps)
- [ ] Load current accepted branch: `data/computed/chapter3_quasi_dro_palc_family.csv` (member 0–10)
- [ ] Verify member 10 parameters are as expected

### Phase 1: Extract and Modularize Predictor (1–2 days)

**Task 1.1:** Extract `parameter_aware_predictor` logic
- Source: `scripts/run_chapter3_route_b_parameter_aware_palc.py`
- Action: Create standalone function with clear inputs/outputs
- Validation: Unit test on free-time case; should reproduce 11,302 km result

**Task 1.2:** Adapt to fixed-time constraint
- Modification: Add `mapping_time_fixed` parameter
- Ensure: Predictor respects fixed mapping-time in all interpolations
- Validation: Generate guesses for fixed-time solver

**Task 1.3:** Add spectral lifting
- Condition: If Fourier tail energy > threshold, lift to N=71
- Implementation: Use existing spectral interpolation code
- Validation: Lifted state should have smaller tail

### Phase 2: Implement Bounded Substep Loop (2–3 days)

**Task 2.1:** Create substep loop
- Input: `current_member`, `target_rho_delta`, `max_substeps=3`
- Logic: Divide delta into equal pieces, solve each via parameter-aware + two-phase
- Output: Final member at target rho, or None if any substep fails

**Task 2.2:** Integrate two-phase system
- Source: `scripts/prototype_chapter3_route_b_bvp_palc_neighborhood.py`
- Action: Use `two_phase_overdetermined` convention for all BVP solves in substeps
- Validation: Verify condition number is ~1e8 (not 1e10)

**Task 2.3:** Add gate checking
- At end of each substep: call `check_audit_gates()`
- Early exit: if any gate fails, stop and report which gate failed
- Logging: record all substep attempts (success and failure)

### Phase 3: Forward Continuation Campaign (3–5 days)

**Task 3.1:** Initialize
- Load member 10 from CSV
- Set: `current = member_10`
- Set: `target_rho_delta = 0.00005 rad` (small fixed increment)

**Task 3.2:** Main loop
```
while current.max_z < 10500 km:  # minimum target
    next_candidate = bounded_substep_advancement(
        current,
        target_rho_delta=0.00005,
        max_substeps=3,
        mapping_time_fixed=14.74932760227518
    )
    
    if next_candidate is not None:
        current = next_candidate
        member_id += 1
        log to CSV
        print(f"✓ Member {member_id}: max_z = {current.max_z} km")
    else:
        print(f"✗ Forward step failed at max_z = {current.max_z} km")
        break
```

**Task 3.3:** Adaptive Fourier trigger
- Condition: If Newton fails at some substep, lift to N=71 and retry
- Log: Record which members required lifting
- Decision: If lifting also fails, stop

**Task 3.4:** CSV output
- Append each accepted member to `chapter3_integrated_breakthrough_candidates.csv`
- Columns: `member_id, rho, mean_jacobi, mapping_time, max_z, map_residual, jacobi_span, phase_error, fourier_order, gate_status`
- Immediate write (don't wait until end)

### Phase 4: Validation and Reporting (1–2 days)

**Task 4.1:** Independent re-solve verification
- For each accepted member: solve from scratch (no branch history)
- Verify: All gates pass independently
- Output: `chapter3_integrated_breakthrough_revalidation.csv`

**Task 4.2:** Final summary
- Create: `docs/chapter3_integrated_breakthrough_results.md`
- Contents:
  - Starting point (member 10, 10,164 km)
  - Final point (member N, max_z km)
  - Number of steps, total rho change
  - Which gates passed on all members
  - Which steps required Fourier lifting
  - Any blockers encountered

---

## 📊 Part 6: Expected Outcomes and Success Criteria

### Minimum Success (must achieve)
```
✓ Reach 10,500 km fixed-time
✓ All 7 gates pass on final member
✓ Branch shows monotone rho increase
✓ Mapping-time stays within 1e-10 days
✓ Independent re-solve confirms all gates
```

### Stretch Goal
```
◇ Reach 11,000 km fixed-time
◇ Understand what limits further advance (gate 7 conditioning? branch topology?)
◇ Generate diagnostic figures showing improvement trajectory
```

### What to Do If We Hit Blockers

**Blocker 1: Substep fails to converge**
- Diagnosis: Which substep? Which gate?
- Response: Reduce substep size (use 4–5 substeps instead of 3)
- Fallback: Try lifting to N=71 even if Newton didn't explicitly fail

**Blocker 2: Fourier lifting doesn't help**
- Diagnosis: Is Fourier tail the real problem, or is it branch topology?
- Response: Examine local branch curvature; maybe mixing free-time + fixed-time approach
- Fallback: Document as "branch limited at X km despite all attempts"

**Blocker 3: Gate 7 conditioning explodes**
- Diagnosis: Is conditioning just high, or is system becoming numerically unreliable?
- Response: Monitor relative error estimates; if growing, stop and report
- Fallback: Document as "conditioning degrades beyond X km; numerical reliability uncertain"

---

## 🔗 Part 7: File Organization and Outputs

### Input Files (Already Exist)
```
mccarthy2018_reproduction/
├── data/computed/
│   ├── chapter3_quasi_dro_palc_family.csv          ← Current branch (member 0–10)
│   ├── chapter3_route_b_parameter_aware_palc.csv   ← Free-time results
│   └── chapter3_route_b_bvp_palc_neighborhood.csv  ← Two-phase conditioning tests
├── scripts/
│   ├── run_chapter3_route_b_parameter_aware_palc.py
│   ├── run_chapter3_route_b_bvp_palc_stabilization.py
│   └── prototype_chapter3_route_b_bvp_palc_neighborhood.py
└── src/qp_orbits/
    └── [Fixed-time BVP solver, spectral lifting, etc.]
```

### New Files to Create
```
mccarthy2018_reproduction/
├── scripts/
│   └── run_chapter3_integrated_breakthrough.py      ← Main campaign script (NEW)
├── data/computed/
│   ├── chapter3_integrated_breakthrough_candidates.csv        ← Members 11, 12, ... (NEW)
│   ├── chapter3_integrated_breakthrough_revalidation.csv      ← Independent re-solve (NEW)
│   └── chapter3_integrated_breakthrough_diagnostics.csv       ← Step-by-step log (NEW)
└── docs/
    └── chapter3_integrated_breakthrough_results.md  ← Final summary (NEW)
```

### CSV Schema
```
member_id,
rho_rad,
mean_jacobi,
mapping_time_days,
max_abs_z_km,
map_residual_max,
jacobi_mean_span,
jacobi_one_map_drift,
jacobi_ten_return_span,
phase_return_error,
condition_number,
fourier_order,
gate_1_residual,
gate_2_jacobi,
gate_3_phase,
gate_4_rho_monotone,
gate_5_amplitude,
gate_6_mapping_time,
gate_7_condition,
overall_acceptance,
step_source
```

---

## ⏱️ Part 8: Timeline and Resource Estimate

| Phase | Duration | CPU Time | Key Deliverable |
|-------|----------|----------|-----------------|
| **Phase 0: Prep** | 0.5 day | — | Code review complete |
| **Phase 1: Predictor** | 1–2 days | ~2 hours | Modularized predictor with unit tests |
| **Phase 2: Substeps** | 2–3 days | ~10 hours | Substep loop + two-phase integration |
| **Phase 3: Forward** | 3–5 days | 80–120 hours | Members 11–50+ with continuous logging |
| **Phase 4: Validation** | 1–2 days | 20–30 hours | Revalidation + final report |
| **TOTAL** | ~1–2 weeks | ~110–160 hours | Final branch reaching ≥10,500 km |

**Wall-clock estimate:** ~7–10 days on a single 24-core machine (or faster with parallelization)

---

## 🎓 Part 9: Key References and Code Pointers

### Where Each Component Is Documented

1. **Parameter-Aware PALC**
   - Explanation: `docs/chapter3_route_b_parameter_aware_palc.md`
   - Code: `scripts/run_chapter3_route_b_parameter_aware_palc.py` (extract predictor logic)
   - Success: Reached 11,302 km in free-time; can reach 10,274 km when projected to fixed-time

2. **Bounded Substeps**
   - Explanation: `docs/chapter3_route_b_bvp_stabilization.md` (section: "8_to_9 Failure Diagnosis")
   - Code: `scripts/run_chapter3_route_b_bvp_palc_stabilization.py`
   - Success: Recovered 8→9 step that full secant couldn't pass

3. **Two-Phase Conditioning**
   - Explanation: `docs/chapter3_route_b_bvp_palc_neighborhood.md` (section: "Best Conditioning Convention")
   - Code: `scripts/prototype_chapter3_route_b_bvp_palc_neighborhood.py` (two_phase_overdetermined)
   - Validation: Condition number improved from `4.82e10` to `7.61e7`

4. **Fixed-Time BVP Solver**
   - Location: `src/qp_orbits/quasi_torus.py` (function: `solve_fixed_time_bvp` or similar)
   - Interface: Takes state_guess, rho, mapping_time → returns result with residual, Jacobian, etc.

5. **Spectral Lifting**
   - Location: `src/qp_orbits/quasi_torus.py` or similar
   - Function: `lift_fourier` or `spectral_interpolate`
   - Usage: Called when Fourier tail is large before Newton retry

---

## 🚀 Part 10: How to Use This Document

### For Codex (Implementation)
1. **Read parts 1–2:** Understand the problem and the three-component solution
2. **Review part 5:** Step-by-step implementation plan
3. **Check part 9:** Know where to find existing code to reuse
4. **Start with Phase 1:** Extract parameter-aware predictor
5. **Build Phase 2:** Implement bounded substep loop
6. **Run Phase 3:** Forward continuation campaign with logging
7. **Execute Phase 4:** Validation and final report

### For Scientific Review
1. **Read part 1:** Understand why 10,164 km is a bottleneck
2. **Review part 2:** See the three integrated components
3. **Check part 3:** Visualize how they work together
4. **Check part 4:** Understand audit gates ensure quality
5. **Review part 7:** See output structure and validation approach

---

## 📝 Summary: What Codex Needs to Build

Codex needs to create **one main script**: `run_chapter3_integrated_breakthrough.py`

This script should:
1. Load member 10 from CSV
2. Create a loop that repeatedly calls `bounded_substep_advancement()`
3. In each iteration:
   - Use `parameter_aware_predictor()` to generate initial guess
   - Solve with two-phase overdetermined system
   - Check all 7 audit gates
   - Log result to CSV
4. Continue until max_z ≥ 10,500 km or branch fails
5. Generate final summary report

**Key functions Codex will use** (mostly existing, some to create):
- `parameter_aware_predictor()` – extract from Route B code
- `solve_fixed_time_bvp()` – use existing solver with two-phase option
- `bounded_substep_advancement()` – new wrapper around loop
- `check_audit_gates()` – new validation function
- `spectral_lift()` – use existing or create thin wrapper
- CSV logging – standard pandas + write

**Estimated new lines of code:** ~300–500 lines (mostly integration of existing components)

---

## 🎯 Final Note for Codex

You have all the pieces you need:
- **Predictor logic** exists (parameter-aware PALC)
- **Solver logic** exists (fixed-time BVP)
- **Conditioning strategy** exists (two-phase)
- **Validation logic** exists (gate checking)

Your job is to **integrate them into one coherent campaign** that systematically pushes from 10,164 km → 10,500 km+.

The strategy is **low-risk** because:
- Each component has been tested separately
- Bounded substeps guarantee early exit if blocked
- 7 independent gates catch quality issues immediately
- CSV logging provides full diagnostic trail

**Good luck! The physics is already solved at 11,302 km (free-time). You're just optimizing the parameterization to bring it back to fixed-time while maintaining numerical quality.** 🚀

