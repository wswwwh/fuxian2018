# Figure plan

> Draft status: evidence-bound internal methods draft; external literature and citations are intentionally pending verification.

- Registry SHA256: `B38099E93BB85AD4B97035D667A4AD5E6A74C1805B612EDEABC7AF6497C23EE5`
- Method table SHA256: `0B66A89B13926BAF90114741796EA1128AC39A6C62BB092B4A1018B97CDEB88B`
- Manifold table SHA256: `248A1F8CB8F958640D526CFFC2859AC3AEDF697BEE5BDAF78EBED95AD898FB8E`
- Figure manifest SHA256: `FE7147FC8FF4702C1EF6A86454AC45F21CACFD667542DEFD9E17303FC1DE040C`
- Source Git commit: `95a606ef75888fcef7f4d8cb2eedb120efc13b22`


All figures have 320-DPI PNG previews and vector PDF versions.  Captions must preserve research/reproduction boundaries.

## F1

- PDF: `../figures/fig_bundle_method_summary.pdf`
- Caption: Bundle residual, outcome counts, runtime/accuracy, and adjacent-phase continuity across families.

```latex
\begin{figure}[t]
    \centering
    \includegraphics[width=\linewidth]{figures/fig_bundle_method_summary.pdf}
    \caption{Bundle residual, outcome counts, runtime/accuracy, and adjacent-phase continuity across families. Best viewed in color.}
    \label{fig:f1}
\end{figure}
```

## F2

- PDF: `../figures/fig_resolution_convergence.pdf`
- Caption: Halo and vertical residual convergence, cross-N full-sheet distance, and principal-angle convergence.

```latex
\begin{figure}[t]
    \centering
    \includegraphics[width=\linewidth]{figures/fig_resolution_convergence.pdf}
    \caption{Halo and vertical residual convergence, cross-N full-sheet distance, and principal-angle convergence. Best viewed in color.}
    \label{fig:f2}
\end{figure}
```

## F3

- PDF: `../figures/fig_route_h_rho_control.pdf`
- Caption: Physical corrected-rho versus frozen legacy-DG member-68 control.

```latex
\begin{figure}[t]
    \centering
    \includegraphics[width=\linewidth]{figures/fig_route_h_rho_control.pdf}
    \caption{Physical corrected-rho versus frozen legacy-DG member-68 control. Best viewed in color.}
    \label{fig:f3}
\end{figure}
```

## F4

- PDF: `../figures/fig_manifold_method_metrics.pdf`
- Caption: Direction angle, normalized displacement distance, perturbation sensitivity, and residual-to-geometry relation.

```latex
\begin{figure}[t]
    \centering
    \includegraphics[width=\linewidth]{figures/fig_manifold_method_metrics.pdf}
    \caption{Direction angle, normalized displacement distance, perturbation sensitivity, and residual-to-geometry relation. Best viewed in color.}
    \label{fig:f4}
\end{figure}
```

## F5

- PDF: `../figures/fig_phase_continuity_profiles.pdf`
- Caption: Phase-resolved local residual and adjacent-phase angle at three family anchors.

```latex
\begin{figure}[t]
    \centering
    \includegraphics[width=\linewidth]{figures/fig_phase_continuity_profiles.pdf}
    \caption{Phase-resolved local residual and adjacent-phase angle at three family anchors. Best viewed in color.}
    \label{fig:f5}
\end{figure}
```

## F6

- PDF: `../figures/fig_halo_manifold_displacement_sheets.pdf`
- Caption: Normalized Halo N45 displacement sheets for pointwise eig, partial real Schur, and QR/SVD.

```latex
\begin{figure}[t]
    \centering
    \includegraphics[width=\linewidth]{figures/fig_halo_manifold_displacement_sheets.pdf}
    \caption{Normalized Halo N45 displacement sheets for pointwise eig, partial real Schur, and QR/SVD. Best viewed in color.}
    \label{fig:f6}
\end{figure}
```

Manifest: `research/invariant_bundles/figures/research_figure_manifest.csv`.  Figure hashes are checked by `generate_research_figures.py --check`.
