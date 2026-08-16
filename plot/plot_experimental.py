import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# Load data directly from the CSV file
file_path = r"calibration\config\target_curve.csv"
df = pd.read_csv(file_path, skipinitialspace=True)

# Build depth boundaries starting from the surface (z = 0.0 mm)
depth_edges = np.concatenate([[0.0], df["coord"].values])
stress_values = df["residual_stress"].values

# Calculate the midpoint of each depth increment
interval_midpoints = (depth_edges[:-1] + depth_edges[1:]) / 2

# Initialize figure and axes
fig, ax = plt.subplots(figsize=(6.5, 4), dpi=100)

# Plot curve with original colors (blue line, red markers)
ax.plot(
    interval_midpoints,
    stress_values,
    color="#1f77b4",
    linewidth=1.8,
    marker="o",
    markersize=5,
    markerfacecolor="#d62728",
    markeredgecolor="#d62728",
)

# Axis labels matching the reference style without title
ax.set_xlabel("Profundidade (mm)", fontsize=10)
ax.set_ylabel(r"$\sigma_r$ (MPa)", fontsize=10)

# Keep original limits and use the full solid grid style
ax.set_xlim(0, depth_edges[-1])
ax.set_ylim(-150, 0)

ax.grid(True, linestyle="-", color="gray", alpha=0.5, linewidth=0.7)

plt.tight_layout()

# Save the figure as an SVG vector file
output_svg_path = "target_curve.svg"
plt.savefig(output_svg_path, format="svg", bbox_inches="tight")

plt.show()