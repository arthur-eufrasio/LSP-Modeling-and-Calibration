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


def process_file_data(file_path, target_coords, target_stresses):
    """
    Calculates Mean Squared Error (MSE) and retrieves the depth/stress profiles.
    """
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
    
    return mse, depth_data_y, simulated_stresses


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
            mse, depth_y, sim_stresses = process_file_data(file_path, target_coords, target_stresses)
            file_name = os.path.basename(file_path)
            results.append({
                'file_name': file_name,
                'file_path': file_path,
                'mse': mse,
                'depth_y': depth_y,
                'sim_stresses': sim_stresses
            })
        except Exception as e:
            print(f"[WARNING] Could not process {file_path}: {e}")

    # Sort results by MSE ascending (lowest error first)
    results.sort(key=lambda x: x['mse'])

    # Select Top 10 and Top 5 datasets
    top_10 = results[:10]
    top_5 = results[:5]

    # Print terminal ranking output
    print("\n" + "=" * 50)
    print(" TOP 10 LOWEST MSE RANKING ".center(50, "="))
    print("=" * 50)
    for rank, item in enumerate(top_10, 1):
        print(f"Rank {rank:2d} | MSE: {item['mse']:12.4f} | File: {item['file_name']}")
    print("=" * 50 + "\n")

    # Figure 1: Top 10 MSE Ranking Bar Chart
    plot_ranking(top_10)

    # Figure 2: Target Curve vs Top 5 Simulated Profiles
    plot_profiles(target_coords, target_stresses, top_5)

    # Display both figures simultaneously
    plt.show()


def plot_ranking(top_10_results):
    """Generates Figure 1: Horizontal bar chart ranking the top 10 models with lowest MSE."""
    plt.figure(1, figsize=(10, 6))
    labels = [item['file_name'].replace('.json', '') for item in top_10_results]
    mse_values = [item['mse'] for item in top_10_results]

    bars = plt.barh(labels[::-1], mse_values[::-1], color='navy', edgecolor='black', alpha=0.8)

    plt.xlabel('Mean Squared Error (MSE)', fontsize=12)
    plt.ylabel('Particle Data File', fontsize=12)
    plt.title('Top 10 Lowest MSE Models', fontsize=14, fontweight='bold')
    plt.grid(axis='x', linestyle='--', alpha=0.6)

    # Add numerical labels next to each bar
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


def plot_profiles(target_coords, target_stresses, top_5_results):
    """Generates Figure 2: Target profile vs Top 5 best simulated stress curves."""
    plt.figure(2, figsize=(10, 6))

    # Plot target curve
    plt.plot(target_coords, target_stresses, 'k--', linewidth=2.5, label='Target Profile')

    # Color palette for top 5 curves
    colors = ['#1f77b4', '#ff7f0e', '#2ca02c', '#d62728', '#9467bd']

    # Plot top 5 simulated curves
    for idx, item in enumerate(top_5_results):
        file_label = item['file_name'].replace('.json', '')
        legend_label = f"Rank {idx + 1}: {file_label} (MSE: {item['mse']:.2f})"
        plt.plot(item['depth_y'], item['sim_stresses'], color=colors[idx], linewidth=1.8, label=legend_label)

    plt.xlabel('Depth (mm)', fontsize=12)
    plt.ylabel('Residual Stress (MPa)', fontsize=12)
    plt.title('Target vs Top 5 Simulated Profiles', fontsize=14, fontweight='bold')
    plt.legend(fontsize=10, loc='best')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.tight_layout()


if __name__ == '__main__':
    main()