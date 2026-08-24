import glob
import json
import os
import re
import matplotlib.pyplot as plt

# Global style configuration
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


def apply_legend_style(ax: plt.Axes, title: str = "Tamanho do Elemento") -> None:
    """Applies standardized publication-quality styling to the legend."""
    ax.legend(
        title=title,
        loc="best",
        frameon=True,
        edgecolor="black",
        facecolor="white",
        framealpha=0.9,
        fancybox=False,
        borderaxespad=1.2,
        borderpad=0.6,
    )


def extract_element_size(filename: str) -> int | None:
    """Extracts the integer element size immediately following 'mesh_' in the filename."""
    match = re.search(r"mesh_(\d+)", filename)
    if match:
        return int(match.group(1))
    return None


def plot_depth_stress_profile(folder_path: str) -> None:
    """Loads stress profiles from JSON files containing 'mesh_' and plots residual stress across depth."""
    fig, ax = plt.subplots(figsize=(8.0, 4.5), dpi=300)

    # Reference grid and zero line
    ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6, zorder=0)
    ax.axhline(0, color="gray", linewidth=0.8, linestyle=":", zorder=1)

    search_pattern = os.path.join(folder_path, "*mesh_*.json")
    json_files = glob.glob(search_pattern)

    # Filter files that contain the 'mesh_<number>' pattern
    valid_files = [f for f in json_files if extract_element_size(os.path.basename(f)) is not None]

    # Sort files numerically by extracted element size
    valid_files.sort(key=lambda path: extract_element_size(os.path.basename(path)))

    for file_path in valid_files:
        filename = os.path.basename(file_path)
        ele_size = extract_element_size(filename)

        with open(file_path, "r", encoding="utf-8") as file:
            data = json.load(file)

        # Detect the model key
        candidate_keys = [f"mesh_{ele_size}_model", f"{ele_size}_model", f"mesh_{ele_size}"]
        model_name = next((k for k in candidate_keys if k in data), next(iter(data.keys()), None))

        if model_name is None or "depth" not in data[model_name]:
            print(f"Warning: Depth data not found in {filename}. Skipping.")
            continue

        depth_data = data[model_name]["depth"]
        depth_x = [point[0] for point in depth_data]
        depth_y = [point[1] for point in depth_data]

        # Plot depth curves
        ax.plot(
            depth_x,
            depth_y,
            markersize=4.0,
            marker="o",
            markeredgecolor="black",
            markeredgewidth=0.5,
            linewidth=1.5,
            linestyle="-",
            label=rf"${ele_size}\,\mu\mathrm{{m}}$",
            zorder=3,
        )

    # Rótulo do eixo X com a informação de r = 0.75 mm e rótulo do eixo Y (sem título principal)
    ax.set_xlabel(r"Profundidade em $r = 0.75\,\mathrm{mm}$ [$\mathrm{mm}$]")
    ax.set_ylabel(r"Tensão Residual $\sigma_r$ [$\mathrm{MPa}$]")

    apply_legend_style(ax, title="Tamanho do Elemento")

    fig.tight_layout()
    fig.savefig(
        os.path.join(folder_path, "lsp_residual_stress_depth_r075.svg"),
        format="svg",
        bbox_inches="tight",
    )


if __name__ == "__main__":
    target_folder = "C:/Users/arthu/Desktop/arthur/git/LSP-Modeling-and-Calibration/backend/data/"
    plot_depth_stress_profile(target_folder)