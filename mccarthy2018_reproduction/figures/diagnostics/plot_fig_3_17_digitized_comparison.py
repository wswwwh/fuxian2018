from pathlib import Path

import matplotlib.pyplot as plt
import pandas as pd


ROOT = Path(__file__).resolve().parents[2]
DIGITIZED = ROOT / "data" / "digitized" / "fig_3_17_digitized_points.csv"
BRANCH = ROOT / "data" / "computed" / "chapter3_quasi_dro_palc_validation.csv"
OUT = ROOT / "outputs" / "diagnostics" / "fig_3_17_digitized_comparison.png"


def numeric(series: pd.Series) -> pd.Series:
    return pd.to_numeric(series.replace("N/A", pd.NA), errors="coerce")


def main() -> None:
    digitized = pd.read_csv(DIGITIZED)
    branch = pd.read_csv(BRANCH).sort_values("rotation_angle_rad")

    amp = digitized[digitized["series"] == "amplitude_proxy_reference"].copy()
    jac = digitized[digitized["series"] == "jacobi_proxy_reference"].copy()
    amp["z_amplitude_km"] = numeric(amp["z_amplitude_km"])
    jac["jacobi"] = numeric(jac["jacobi"])

    endpoint = branch.iloc[branch["max_abs_z_km"].idxmax()]

    fig, axes = plt.subplots(1, 2, figsize=(10.5, 4.2), constrained_layout=True)

    ax = axes[0]
    ax.plot(
        branch["rotation_angle_rad"],
        branch["max_abs_z_km"],
        "o-",
        color="#1f77b4",
        label="accepted corrected branch",
        markersize=4,
    )
    ax.plot(
        amp["rho_rad"],
        amp["z_amplitude_km"],
        "s",
        color="#d95f02",
        label="digitized Fig. 3.17 trend",
        markersize=4,
    )
    ax.axhline(10500, color="#9e9e9e", linestyle="--", linewidth=1, label="10,500 km")
    ax.axhline(11000, color="#616161", linestyle=":", linewidth=1.2, label="11,000 km")
    ax.plot(
        [endpoint["rotation_angle_rad"]],
        [endpoint["max_abs_z_km"]],
        marker="*",
        color="#b2182b",
        markersize=11,
        label="accepted endpoint",
    )
    ax.set_xlabel(r"Rotation angle $\rho$ [rad]")
    ax.set_ylabel("Z-amplitude [km]")
    ax.set_title("Amplitude trend")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)

    ax = axes[1]
    ax.plot(
        branch["rotation_angle_rad"],
        branch["mean_jacobi"],
        "o-",
        color="#1f77b4",
        label="accepted corrected branch",
        markersize=4,
    )
    ax.plot(
        jac["rho_rad"],
        jac["jacobi"],
        "s",
        color="#d95f02",
        label="digitized Fig. 3.17 trend",
        markersize=4,
    )
    ax.plot(
        [endpoint["rotation_angle_rad"]],
        [endpoint["mean_jacobi"]],
        marker="*",
        color="#b2182b",
        markersize=11,
        label="accepted endpoint",
    )
    ax.set_xlabel(r"Rotation angle $\rho$ [rad]")
    ax.set_ylabel("Jacobi constant")
    ax.set_title("Jacobi trend")
    ax.grid(True, alpha=0.25)
    ax.legend(fontsize=8)

    fig.suptitle("Fig. 3.17 digitized reference trend vs current corrected branch")
    OUT.parent.mkdir(parents=True, exist_ok=True)
    fig.savefig(OUT, dpi=200)
    plt.close(fig)
    print(OUT)


if __name__ == "__main__":
    main()
