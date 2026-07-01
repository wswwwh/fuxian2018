# Future Work Plan

This plan formalizes the next phase without starting new numerical algorithms
in this documentation round.

## Route A: McCarthy Original Data / Digitization

### objective

Find or reconstruct McCarthy 2018 original numerical data sufficiently to
compare the current reproduction against the thesis at branch/table level.

### required inputs

- McCarthy 2018 thesis PDF and Purdue Hammer record.
- Purdue / Howell publication pages.
- Related McCarthy and Howell AAS papers.
- Existing `docs/external_reproduction_resources.md`.
- High-resolution thesis figure images or digitization tools if raw data remain
  unavailable.

### tasks

1. Recheck Purdue Hammer and Purdue library pages for attachments or metadata
   beyond the PDF.
2. Search for exact figure captions, branch names, quasi-DRO mapping time,
   `14.75 days`, and McCarthy/Howell related materials.
3. Record negative evidence explicitly if no appendix, code, or branch data is
   found.
4. Digitize Fig. 3.16 and Fig. 3.17 only after confirming no raw branch data is
   public.
5. Compare digitized values against the accepted corrected branch and proxy
   trends.

### success criteria

- Original branch data or reliable digitized curves are linked and documented;
  or
- a bounded negative search is documented clearly enough to justify Route C
  reporting and Route B formulation work.

### risks

- Original data may not be public.
- Digitization may be too low resolution for strict numerical comparison.
- Related papers may show application figures without exposing thesis branch
  tables.

### stop condition

Stop when either original data are found, or the negative search has checked
the main Purdue/Hammer/Howell/AAS/public-repository routes and no new evidence
appears.

## Route B: quasi-DRO formulation replacement

### objective

Replace or augment the current fixed-mapping-time invariant-curve formulation
so the quasi-DRO continuation can handle the 10,000-11,000 km bottleneck.

### required inputs

- Current accepted quasi-DRO branch and bottleneck diagnostics.
- Olikara/Howell invariant curve method.
- Schilder/Osinga/Vogt torus continuation reference.
- Tor/COCO Fourier-collocation BVP resources.
- A written method note defining residual equations, continuation variables,
  phase constraints, and acceptance thresholds.

### tasks

1. Freeze the current accepted branch as the baseline comparison target.
2. Define the new residual equations before coding.
3. Decide whether continuation variables are fixed mapping time, fixed
   rotation, fixed energy/Jacobi, pseudo-arclength, or a torus BVP parameter set.
4. Define phase constraints that remove parameterization ambiguity.
5. Define acceptance thresholds for residual, Jacobi span, phase consistency,
   Fourier tail, singular values, and multi-return drift.
6. Prototype on a smaller known torus family before returning to quasi-DRO.
7. Attempt to pass 10,500 km and 11,000 km only after the prototype passes
   audit gates.

### success criteria

- At least one accepted high-amplitude quasi-DRO member exceeds 10,500 km and
  11,000 km with residual/Jacobi/phase evidence comparable to the current
  accepted branch; and
- Fig. 3.16 / Fig. 3.17 can be updated without relying on rejected candidates or
  grey proxy trends.

### risks

- Implementation cost is high.
- COCO/Tor is MATLAB-based while the current project is Python-first.
- The formulation may reveal that the thesis used branch conventions not yet
  captured in the current code.
- Higher spectral order alone may not solve a parameterization or Newton-basin
  failure.

### stop condition

Do not start coding until the formulation note exists. Stop a prototype if it
cannot reproduce a smaller known torus family with strict audit gates.

## Route C: paper-level reproduction report and opening/report preparation

### objective

Turn the current 54-figure coverage and audits into a defensible reproduction
report package for group meeting, master's opening report, or paper-preparation
use.

### required inputs

- `data/computed/figure_validation_table.csv`
- `docs/reproduction_report/main_report.md`
- `docs/reproduction_report/figure_status_appendix.md`
- `docs/reproduction_report/numerical_audit_appendix.md`
- `docs/reproduction_report/proxy_usage_appendix.md`
- `docs/external_reproduction_resources.md`
- `docs/stage_report_reproduction_status.md`
- `docs/next_reproduction_roadmap.md`

### tasks

1. Keep the figure status appendix synchronized with
   `figure_validation_table.csv`.
2. Convert the main report into a slide outline or manuscript outline if needed.
3. Add a concise figure-status table for group presentation.
4. Prepare a limitations section emphasizing incomplete McCarthy numerical
   equivalence.
5. Decide whether Route A evidence is sufficient for a report-only milestone or
   whether Route B must become the next research task.

### success criteria

- The report can be read independently and explains what is reproduced, what is
  baseline/proxy, and what remains missing.
- Fig. 3.16 and Fig. 3.17 are clearly labeled partial physical-consistency
  baselines.
- Chapter 5 is clearly labeled as baseline/proxy until the Chapter 3 quasi-DRO
  branch is reliable.

### risks

- The report may be mistaken for a claim of complete McCarthy 2018 numerical
  reproduction unless the classification language is kept explicit.
- Proxy figures may be visually persuasive but numerically incomplete.
- Without original data, some comparisons remain qualitative or digitized.

### stop condition

Route C is complete when the report package is internally consistent, the README
points readers to the package, and the remaining gaps are explicit enough to
support a decision between Route A and Route B.
