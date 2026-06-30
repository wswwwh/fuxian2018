# Figure Consistency Review Against McCarthy 2018

Review date: 2026-06-30.

Compared:

- Generated figures: `outputs/figures_png/fig_*.png`
- Thesis reference crops: `outputs/reference_pages/*_reference.png`
- Existing side-by-side contact sheets:
  `outputs/comparison_contact_sheets/*_comparison.png`
- Automated metric output:
  `outputs/figure_qa/figure_similarity_metrics.csv`
- Chapter montages:
  `outputs/figure_qa/chapter2_comparison_montage.png`
  `outputs/figure_qa/chapter3_comparison_montage.png`
  `outputs/figure_qa/chapter4_comparison_montage.png`
  `outputs/figure_qa/chapter5_comparison_montage.png`

Important: the automated metrics are only triage signals. The reference crops
come from thesis figures with different fonts, captions, whitespace, rendering,
and sometimes page context, so exact pixel similarity is not the right pass
criterion. The useful criterion here is visual structure, plotted object type,
view angle, axes, scale, labels, and qualitative/numerical trend.

## Overall Conclusion

The generated figure set is complete, but it is not yet fully consistent with
the original thesis figures.

- 54 generated PNG figures exist.
- 54 reference crops exist.
- 54 side-by-side comparison contact sheets exist.
- A subset is visually close enough for first-pass reproduction or explanatory
  use.
- Many numerical Chapter 3-5 figures are better described as local numerical
  baselines or proxy/trend reproductions, not exact thesis figure matches.
- The largest inconsistencies are in the quasi-periodic manifold/application
  figures and in several figures where the same concept is plotted with a
  different viewpoint, layout, or data source.

## Close Or Acceptable First-Pass Matches

These figures are broadly consistent in visual intent and structure, though not
pixel-identical:

| Figures | Notes |
|---|---|
| 2.1, 2.2 | Geometry schematics are close in structure and labels. |
| 2.9, 2.10 | Shooting and multiple-shooting schematics match the intended method diagrams. |
| 2.11 | Lyapunov initial guess vs corrected solution is close in concept and layout. |
| 2.12 | Continuation schematic is close enough for first-pass use. |
| 2.13 | Jupiter-Europa Lyapunov/halo/vertical families are visually close, with different camera/label polish. |
| 2.15 | Stability-index trend is close in shape and scale. |
| 3.3 | Seven-point invariant-curve map is close in concept and panel structure. |
| 5.2, 5.3 | Eclipse and line-of-sight geometry schematics are close. |

## Partially Consistent, Needs Visual Or Numerical Tuning

These figures show the right topic, but differ visibly in layout, camera,
scaling, density, curve placement, or quantitative trend:

| Figures | Main difference |
|---|---|
| 2.4, 2.5, 2.6 | ZVC/interior-region views are similar concepts, but 2.6 has a different layout and crop balance from the thesis. |
| 2.7, 2.8 | Linear mode/Lissajous content is present, but viewpoint and axes differ strongly. |
| 2.14 | Stable/unstable manifold family is present, but the branch density and shape differ from the thesis. |
| 3.1, 3.2, 3.4 | Torus schematics are conceptually close, but not the same camera/annotation layout. |
| 3.5-3.9 | Constant-energy QPO family figures show the intended objects/trends, but not exact thesis appearance; axes, view and parameter curves need tuning. |
| 3.12-3.17 | Constant-frequency and quasi-DRO outputs are in the right category, but should remain labelled local numerical/trend reproductions until validated against thesis values. |
| 4.1, 4.2 | DG/eigenstructure and stability-index ideas are present, but plot scale and visual structure differ. |
| 5.1, 5.4-5.8, 5.10-5.12 | Application figures are same theme but use local baselines/proxy elements; not exact thesis reproduction. |

## Clearly Inconsistent Or High-Priority Fixes

These figures do not yet match the original thesis well enough:

| Figure | Issue |
|---|---|
| 2.3 | Thesis figure is a geometric equilibrium-point diagram; generated figure is a coordinate scatter plot. It is physically valid but visually not consistent. |
| 2.6 | Multi-system ZVC comparison has the right systems but a substantially different layout, scale and cropping. |
| 3.10 | Period-q halo examples are present, but viewpoint, orbit scale and layout differ markedly. |
| 3.11 | Poincare map/central orbit figure has different geometry and panel balance. |
| 4.3-4.6 | Quasi-periodic manifold surfaces have different sheet shape, expansion and viewpoint from the thesis. |
| 4.7-4.8 | Manifold comparison figures are clearly different in global shape and presentation. |
| 5.9 | NRHO/torus-intersection geometry does not match the thesis layout closely. |
| 5.13 | Heat-map field pattern differs substantially from the thesis reference. |
| 5.14 | LEO-to-L1 transfer geometry differs strongly in 3D and projection panels. |

## Recommended Fix Order

1. Fix easy visual mismatches first: 2.3 and 2.6.
2. Re-tune Chapter 2 camera/axis choices: 2.7, 2.8, 2.14.
3. Validate and then re-render Chapter 3 core QPO figures: 3.5-3.17, especially 3.10, 3.11, 3.16, 3.17.
4. Recompute or clearly label Chapter 4 manifold figures as proxy until the DG/manifold workflow reproduces thesis-scale sheets.
5. Treat Chapter 5 as application baselines for now. Exact matching likely requires recovered initial conditions, ephemeris assumptions, and transfer optimization details that are not fully explicit in the thesis.

## Bottom Line

The current outputs are useful as a complete first-pass reproduction framework,
but they should not be described as fully consistent with the original paper.
They are best described as:

- close first-pass schematics for several Chapter 2 and Chapter 5 geometry
  figures,
- physically consistent or trend-level reproductions for many Chapter 2-3
  numerical figures,
- proxy/local-baseline reproductions for many Chapter 4-5 advanced figures.
