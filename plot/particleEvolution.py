import os
import re
import json
import glob
import numpy as np
import matplotlib.pyplot as plt


def get_particle_mse(file_path):
    """Reads the precomputed MSE directly from the JSON file."""
    with open(file_path, 'r') as f:
        data = json.load(f)

    model_key = list(data.keys())[0]
    return data[model_key]["mse"]


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

    if not os.path.exists(data_folder) and os.path.exists('data'):
        data_folder = 'data'

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
            mse = get_particle_mse(item['file_path'])
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
    PARTICLE_ID = 11
    main(PARTICLE_ID)