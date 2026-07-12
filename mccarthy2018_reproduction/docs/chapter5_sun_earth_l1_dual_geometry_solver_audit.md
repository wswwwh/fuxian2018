# Chapter 5 dual-geometry solver audit

- Identity target metric: `1.885e-09`
- Perturbed target metric: `6.917e-09`
- Full-torus response to -0.1% strobe-y support: `dy=+53.790 km`, `dz=+26.648 km`
- Perturbed full-torus max |y|: `1117555.137` km
- Perturbed full-torus max |z|: `935690.100` km
- Target pair accepted: `false`

The regularized solver satisfies map, mean-energy, phase, and both smooth
geometry constraints below `1e-8`. However, reducing the stroboscopic curve's
y support does not reduce the propagated torus y maximum. The next revision
must constrain propagated time-slice support using STM sensitivity; the
stroboscopic support is retained only as a solver regression target.
