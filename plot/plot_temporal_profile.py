import os
import matplotlib.pyplot as plt

# Global typography and style configuration
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Liberation Serif"],
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 11,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.fontsize": 8.5,
        "figure.titlesize": 12,
        "svg.fonttype": "none",
        "mathtext.fontset": "stix",
    }
)


def plot_pulse_profile(output_folder: str = ".") -> None:
    """Plots the rounded pressure pulse profile matching the custom reference formatting."""
    raw_pulse_data = [
        (0.0, 0.0),
        (8.517, 0.925),
        (10.095, 0.996),
        (14.511, 0.978),
        (23.344, 0.511),
        (28.391, 0.409),
        (34.700, 0.349),
        (53.628, 0.253),
        (71.924, 0.201),
        (108.833, 0.121),
        (164.038, 0.049),
        (214.196, 0.003),
        (220.0, 0.0),
    ]

    time_values = [pt[0] for pt in raw_pulse_data]
    pressure_values = [pt[1] for pt in raw_pulse_data]

    fig, ax = plt.subplots(figsize=(8.0, 4.2), dpi=300)

    # Reference grid
    ax.grid(True, linestyle="--", linewidth=0.6, alpha=0.6, zorder=0, color="#d0d0d0")

    # Plot profile curve
    ax.plot(
        time_values,
        pressure_values,
        color="#083759",
        linewidth=2.0,
        marker="s",
        markersize=5.5,
        markeredgecolor="black",
        markeredgewidth=0.7,
        zorder=3,
    )

    # Axis labels, limits, and tick configuration
    ax.set_xlabel(r"Time $t$ [ns]")
    ax.set_ylabel(r"Normalized Pressure $P(t)/P_{\mathrm{peak}}$")

    ax.set_xlim(-3, 223)
    ax.set_ylim(-0.05, 1.12)
    ax.set_xticks(range(0, 221, 20))
    ax.set_yticks([0.0, 0.2, 0.4, 0.6, 0.8, 1.0])

    fig.tight_layout()

    output_path = os.path.join(output_folder, "laser_pulse_profile.svg")
    fig.savefig(output_path, format="svg", bbox_inches="tight")
    # plt.show()


if __name__ == "__main__":
    plot_pulse_profile()