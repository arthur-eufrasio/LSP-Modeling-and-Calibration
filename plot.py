import glob
import json
import os
import pickle
import re

import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import numpy as np


DATA_GLOB = os.path.join("backend", "data", "data_i*_p*.json")
TARGET_PKL = os.path.join("calibration", "config", "target_curve.pkl")


def _extract_indices_from_name(file_name):
    match = re.search(r"data_i(\d+)_p(\d+)\.json$", file_name)
    if not match:
        return None, None
    return int(match.group(1)), int(match.group(2))


def _load_target_spline(path):
    with open(path, "rb") as f:
        return pickle.load(f)


def _load_surface_profile(json_path):
    with open(json_path, "r") as f:
        data = json.load(f)

    top_key = next(iter(data))
    surface = data[top_key]["surface"]
    x = np.array([point[0] for point in surface], dtype=float)
    y = np.array([point[1] for point in surface], dtype=float)
    return x, y


def main():
    target_spline = _load_target_spline(TARGET_PKL)
    data_files = sorted(glob.glob(DATA_GLOB))

    if not data_files:
        raise FileNotFoundError(f"No files found in: {DATA_GLOB}")

    iterations_data = {}
    all_x = []
    all_y = []
    
    best_profile = None
    best_mse = float("inf")

    # Load data and find the best profile overall
    for file_path in data_files:
        file_name = os.path.basename(file_path)
        iteration, particle = _extract_indices_from_name(file_name)

        if iteration is None:
            continue

        x, y = _load_surface_profile(file_path)
        y_target = target_spline(x)
        mse = float(np.mean((y - y_target) ** 2))

        profile_data = {
            "particle": particle,
            "iteration": iteration,
            "x": x,
            "y": y,
            "mse": mse,
        }

        if iteration not in iterations_data:
            iterations_data[iteration] = []

        iterations_data[iteration].append(profile_data)

        # Track the absolute best particle
        if mse < best_mse:
            best_mse = mse
            best_profile = profile_data

        all_x.extend(x)
        all_y.extend(y)

    if not iterations_data or best_profile is None:
        raise RuntimeError("Could not load valid profiles.")

    sorted_iterations = sorted(iterations_data.keys())
    
    # Visual offset: if files start at i=0, display them starting at 1
    iter_offset = 1 if sorted_iterations[0] == 0 else 0
    particle_offset = 1 

    # ==========================================
    # COMMON FORMATTING FUNCTION
    # ==========================================
    x_min, x_max = min(all_x), max(all_x)
    y_min, y_max = min(all_y), max(all_y)

    x_target_plot = np.linspace(x_min, x_max, 400)
    y_target_plot = target_spline(x_target_plot)
    y_target_min, y_target_max = min(y_target_plot), max(y_target_plot)

    # Add a buffer to the Y-axis so the curves don't touch the edges
    y_min = min(y_min, y_target_min) - 50
    y_max = max(y_max, y_target_max) + 50

    def apply_common_formatting(fig, ax):
        # Fix the layout padding so the title doesn't get cut
        fig.subplots_adjust(top=0.88, bottom=0.12, left=0.1, right=0.95)
        
        ax.axhline(0, color="black", linewidth=0.8)
        # Lock limits so both plots show the exact same window frame
        ax.set_xlim(x_min, x_max)
        ax.set_ylim(y_min, y_max)
        ax.set_xlabel("Distance (mm)")
        ax.set_ylabel("Residual Stress (MPa)")
        ax.grid(True, linestyle=":", alpha=0.7)

    # ==========================================
    # PART 1: ANIMATION OF ALL ITERATIONS
    # ==========================================
    fig_anim, ax_anim = plt.subplots(figsize=(11, 6))
    apply_common_formatting(fig_anim, ax_anim)

    ax_anim.plot(
        x_target_plot,
        y_target_plot,
        color="black",
        linewidth=2.5,
        linestyle="--",
        label="Target (PKL)",
    )

    max_particles = max(len(particles) for particles in iterations_data.values())
    particle_lines = []
    for _ in range(max_particles):
        line, = ax_anim.plot([], [], alpha=0.8, linewidth=1.5, marker='.', markersize=4)
        particle_lines.append(line)

    title_text = ax_anim.set_title("", fontsize=14, fontweight="bold", pad=15)
    ax_anim.legend(loc="upper right")

    def update(frame_idx):
        iteration = sorted_iterations[frame_idx]
        particles = iterations_data[iteration]

        display_iter = iteration + iter_offset
        title_text.set_text(f"Evolution of Residual Stress - Iteration: {display_iter}")

        for i, line in enumerate(particle_lines):
            if i < len(particles):
                p_data = particles[i]
                display_part = p_data['particle'] + particle_offset
                line.set_data(p_data["x"], p_data["y"])
                line.set_label(f"Particle {display_part} | MSE: {p_data['mse']:.2f}")
            else:
                line.set_data([], [])
                line.set_label("_nolegend_")

        ax_anim.legend(loc="upper right")
        return particle_lines + [title_text]

    print("Generating animation...")
    ani = FuncAnimation(
        fig_anim, 
        update, 
        frames=len(sorted_iterations), 
        interval=1200, 
        repeat=False,
        blit=False
    )
    
    # Save the animation as a GIF
    gif_filename = "calibration_evolution.gif"
    print(f"Saving animation to '{gif_filename}'...")
    ani.save(gif_filename, writer="pillow")
    
    print("Playing animation... Close the window to see the best profile result.")
    plt.show() 

    # ==========================================
    # PART 2: STATIC PLOT FOR THE BEST PROFILE
    # ==========================================
    best_display_iter = best_profile['iteration'] + iter_offset
    best_display_part = best_profile['particle'] + particle_offset
    
    print(
        f"\nShowing Best Particle:\n"
        f"  Iteration: {best_display_iter} (Internal Index: {best_profile['iteration']})\n"
        f"  Particle:  {best_display_part} (Internal Index: {best_profile['particle']})\n"
        f"  MSE:       {best_profile['mse']:.6f}\n"
    )

    fig_best, ax_best = plt.subplots(figsize=(11, 6))
    apply_common_formatting(fig_best, ax_best)

    ax_best.plot(
        x_target_plot,
        y_target_plot,
        color="black",
        linewidth=2.5,
        linestyle="--",
        label="Target (PKL)",
    )

    ax_best.plot(
        best_profile["x"],
        best_profile["y"],
        color="red",
        linewidth=2.8,
        label=(
            f"Best Particle (i={best_display_iter}, p={best_display_part}) | "
            f"MSE: {best_profile['mse']:.4f}"
        ),
    )

    ax_best.set_title("Best Residual Stress Profile Found", fontsize=14, fontweight="bold", pad=15)
    ax_best.legend(loc="upper right")
    
    # Save the best profile as a PNG image
    png_filename = "best_profile.png"
    print(f"Saving best profile plot to '{png_filename}'...")
    fig_best.savefig(png_filename, dpi=300, bbox_inches="tight")
    
    plt.show()


if __name__ == "__main__":
    main()