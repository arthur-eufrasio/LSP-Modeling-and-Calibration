import os
import json
import glob
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Try importing the custom load_target_curve function from your project structure
try:
    from calibration.target_curve import load_target_curve
except ImportError:
    def load_target_curve(csv_path):
        """Fallback CSV loader if module import is not available directly."""
        data = np.loadtxt(csv_path, delimiter=',', skiprows=1)
        return data[:, 0], data[:, 1]


def calculate_file_mse(file_path, target_coords, target_stresses):
    """Calculates Mean Squared Error (MSE) for a single JSON data file."""
    with open(file_path, 'r') as f:
        data = json.load(f)

    # Get the dynamic model key (e.g., 'lspModel_i0_p0')
    model_key = list(data.keys())[0]
    depth_data = data[model_key]["depth"]

    depth_data_y = np.array([point[0] for point in depth_data])
    simulated_stresses = np.array([point[1] for point in depth_data])

    # Interpolate simulated stresses over depth
    sim_interp = interp1d(
        depth_data_y,
        simulated_stresses,
        kind='linear',
        bounds_error=False,
        fill_value=(simulated_stresses[0], simulated_stresses[-1]),
        assume_sorted=True
    )

    # Calculate average stress per depth interval
    simulated_averages = []
    prev_depth = 0.0

    for current_depth in target_coords:
        eval_points = np.linspace(prev_depth, current_depth, 50)
        avg_simulated_stress = np.mean(sim_interp(eval_points))
        simulated_averages.append(avg_simulated_stress)
        prev_depth = current_depth

    simulated_averages = np.array(simulated_averages)

    # Mean Squared Error calculation
    mse = np.mean((simulated_averages - target_stresses) ** 2)
    return mse


def main():
    # Paths configuration
    data_folder = os.path.join('backend', 'data')
    target_profile_path = os.path.join('calibration', 'config', 'target_curve.csv')

    # Load target reference curve
    target_coords, target_stresses = load_target_curve(target_profile_path)

    # Retrieve all JSON data files
    json_files = glob.glob(os.path.join(data_folder, '*.json'))

    if not json_files:
        print(f"No JSON files found in directory '{data_folder}'.")
        return

    results = []

    print(f"Processing {len(json_files)} data files...")
    for file_path in json_files:
        try:
            mse = calculate_file_mse(file_path, target_coords, target_stresses)
            file_name = os.path.basename(file_path)
            results.append({
                'file_name': file_name,
                'file_path': file_path,
                'mse': mse
            })
        except Exception as e:
            print(f"[WARNING] Could not process {file_path}: {e}")

    # Sort results by MSE ascending (lowest error first)
    results.sort(key=lambda x: x['mse'])

    # Select Top 10 lowest MSE
    top_10 = results[:10]

    # Print terminal output
    print("\n" + "=" * 50)
    print(" TOP 10 LOWEST MSE RANKING ".center(50, "="))
    print("=" * 50)
    for rank, item in enumerate(top_10, 1):
        print(f"Rank {rank:2d} | MSE: {item['mse']:12.4f} | File: {item['file_name']}")
    print("=" * 50 + "\n")

    # Plot top 10 ranking
    plot_ranking(top_10)


def plot_ranking(top_10_results):
    """Generates a bar chart ranking the top 10 models with the lowest MSE."""
    labels = [item['file_name'].replace('.json', '') for item in top_10_results]
    mse_values = [item['mse'] for item in top_10_results]

    plt.figure(figsize=(12, 6))
    bars = plt.barh(labels[::-1], mse_values[::-1], color='navy', edgecolor='black', alpha=0.8)

    plt.xlabel('Mean Squared Error (MSE)', fontsize=12)
    plt.ylabel('Particle Data File', fontsize=12)
    plt.title('Top 10 Lowest MSE Models', fontsize=14, fontweight='bold')
    plt.grid(axis='x', linestyle='--', alpha=0.6)

    # Add MSE text labels next to each bar
    for bar in bars:
        width = bar.get_width()
        plt.text(
            width + (max(mse_values) * 0.01),
            bar.get_y() + bar.get_height() / 2,
            f'{width:.4f}',
            va='center',
            ha='left',
            fontsize=10,
            fontweight='bold'
        )

    plt.tight_layout()
    plt.show()


if __name__ == '__main__':
    main()