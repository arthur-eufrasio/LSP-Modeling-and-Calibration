import os
import re
import json
import glob
import numpy as np
import matplotlib.pyplot as plt
from scipy.interpolate import interp1d

# Try importing target curve loader or use fallback
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

    # Dynamically extract model key (e.g., 'lspModel_i0_p0')
    model_key = list(data.keys())[0]
    depth_data = data[model_key]["depth"]

    depth_data_y = np.array([point[0] for point in depth_data])
    simulated_stresses = np.array([point[1] for point in depth_data])

    # Interpolate simulated stresses over target depths
    sim_interp = interp1d(
        depth_data_y,
        simulated_stresses,
        kind='linear',
        bounds_error=False,
        fill_value=(simulated_stresses[0], simulated_stresses[-1]),
        assume_sorted=True
    )

    simulated_averages = []
    prev_depth = 0.0

    for current_depth in target_coords:
        eval_points = np.linspace(prev_depth, current_depth, 50)
        avg_simulated_stress = np.mean(sim_interp(eval_points))
        simulated_averages.append(avg_simulated_stress)
        prev_depth = current_depth

    simulated_averages = np.array(simulated_averages)
    mse = np.mean((simulated_averages - target_stresses) ** 2)
    return mse


def get_particle_files(data_folder, particle_id):
    """Retrieves and sorts all JSON files for a specific particle ID by iteration index."""
    pattern = os.path.join(data_folder, f'data_i*_p{particle_id}.json')
    files = glob.glob(pattern)

    particle_data = []
    regex = re.compile(rf'data_i(\d+)_p{particle_id}\.json$')

    for file_path in files:
        filename = os.path.basename(file_path)
        match = regex.search(filename)
        if match:
            iteration_idx = int(match.group(1))
            particle_data.append({
                'iteration': iteration_idx,
                'file_name': filename,
                'file_path': file_path
            })

    # Sort sequentially by iteration number
    particle_data.sort(key=lambda x: x['iteration'])
    return particle_data


def plot_particle_evolution(particle_id, iterations, mse_values):
    """Plots the MSE evolution curve for the given particle across iterations."""
    plt.figure(figsize=(10, 6))

    plt.plot(
        iterations, 
        mse_values, 
        marker='o', 
        linestyle='-', 
        color='#1f77b4', 
        linewidth=2, 
        markersize=6, 
        label=f'Particle {particle_id}'
    )

    # Highlight global minimum for this particle
    min_idx = np.argmin(mse_values)
    best_iteration = iterations[min_idx]
    best_mse = mse_values[min_idx]

    plt.scatter([best_iteration], [best_mse], color='red', s=100, zorder=5, label=f'Best MSE ({best_mse:.2f})')

    plt.xlabel('Iteration Number', fontsize=12)
    plt.ylabel('Mean Squared Error (MSE)', fontsize=12)
    plt.title(f'MSE Evolution across Iterations for Particle {particle_id}', fontsize=14, fontweight='bold')
    plt.grid(True, linestyle='--', alpha=0.6)
    plt.legend(fontsize=11)
    
    # Format x-axis ticks to integer values
    if len(iterations) > 0:
        step = 1 if len(iterations) <= 20 else len(iterations) // 10
        plt.xticks(np.arange(min(iterations), max(iterations) + 1, step))
        
    plt.tight_layout()
    plt.show()


def main(particle_id):
    data_folder = os.path.join('backend', 'data')
    target_profile_path = os.path.join('calibration', 'config', 'target_curve.csv')

    # Fallback check if backend/data doesn't exist directly
    if not os.path.exists(data_folder) and os.path.exists('data'):
        data_folder = 'data'

    # Load reference target curve
    target_coords, target_stresses = load_target_curve(target_profile_path)

    # Find files for selected particle
    particle_files = get_particle_files(data_folder, particle_id)

    if not particle_files:
        print(f"[ERROR] No data files found for particle ID {particle_id} in '{data_folder}'.")
        return

    print(f"\nProcessing {len(particle_files)} iteration files for Particle {particle_id}...\n")
    
    iterations = []
    mse_values = []

    print("=" * 60)
    print(f" MSE EVOLUTION FOR PARTICLE {particle_id} ".center(60, "="))
    print("=" * 60)
    print(f"{'Iteration':^12} | {'File Name':^25} | {'MSE Value':^15}")
    print("-" * 60)

    for item in particle_files:
        try:
            mse = calculate_file_mse(item['file_path'], target_coords, target_stresses)
            item['mse'] = mse
            iterations.append(item['iteration'])
            mse_values.append(mse)
            print(f"{item['iteration']:^12d} | {item['file_name']:^25} | {mse:15.4f}")
        except Exception as e:
            print(f"[WARNING] Could not process {item['file_name']}: {e}")

    print("=" * 60 + "\n")

    # Plot MSE evolution line chart
    plot_particle_evolution(particle_id, iterations, mse_values)


if __name__ == '__main__':
    # Change this global variable to set the target particle number
    PARTICLE_ID = 7

    main(PARTICLE_ID)