import glob
import json
import os
import pickle
import re

import matplotlib.pyplot as plt
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
        raise FileNotFoundError(f"Nenhum arquivo encontrado em: {DATA_GLOB}")

    profiles = []
    best_profile = None
    best_mse = float("inf")

    for file_path in data_files:
        file_name = os.path.basename(file_path)
        iteration, particle = _extract_indices_from_name(file_name)

        if iteration is None:
            continue

        x, y = _load_surface_profile(file_path)
        y_target = target_spline(x)
        mse = float(np.mean((y - y_target) ** 2))

        profile = {
            "path": file_path,
            "iteration": iteration,
            "particle": particle,
            "x": x,
            "y": y,
            "mse": mse,
        }
        profiles.append(profile)

        if mse < best_mse:
            best_mse = mse
            best_profile = profile

    if not profiles or best_profile is None:
        raise RuntimeError("Não foi possível carregar perfis válidos.")

    fig, ax = plt.subplots(figsize=(11, 6))

    for profile in profiles:
        ax.plot(profile["x"], profile["y"], color="gray", alpha=0.22, linewidth=1)

    x_target_plot = np.linspace(np.min(best_profile["x"]), np.max(best_profile["x"]), 400)
    y_target_plot = target_spline(x_target_plot)
    ax.plot(
        x_target_plot,
        y_target_plot,
        color="black",
        linewidth=2.5,
        linestyle="--",
        label="Target (PKL)",
    )

    ax.plot(
        best_profile["x"],
        best_profile["y"],
        color="red",
        linewidth=2.8,
        label=(
            f"Melhor partícula: i={best_profile['iteration']} p={best_profile['particle']} "
            f"| MSE={best_profile['mse']:.4f}"
        ),
    )

    ax.axhline(0, color="black", linewidth=0.8)
    ax.set_xlabel("Distância (mm)")
    ax.set_ylabel("Tensão Residual (MPa)")
    ax.set_title("Perfis de Tensão Residual (todas as partículas)")
    ax.grid(True, linestyle=":", alpha=0.7)
    ax.legend()
    plt.tight_layout()

    print(f"Total de perfis plotados: {len(profiles)}")
    print(
        "Melhor partícula: "
        f"iteração={best_profile['iteration']} "
        f"partícula={best_profile['particle']} "
        f"MSE={best_profile['mse']:.6f}"
    )

    plt.show()


if __name__ == "__main__":
    main()