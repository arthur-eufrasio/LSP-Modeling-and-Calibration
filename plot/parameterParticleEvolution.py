import os
import re
import json
import glob
import numpy as np
import matplotlib.pyplot as plt


def get_particle_parameters(file_path):
    """
    Reads the parameter values for the particle from the JSON file.
    Supports either a list of values or a dictionary of named parameters.
    """
    with open(file_path, 'r') as f:
        data = json.load(f)

    model_key = list(data.keys())[0]
    
    # Access parameters directly by key
    params_data = data[model_key]['parameters']
    
    if isinstance(params_data, dict):
        return params_data  # {param_name: value}
    elif isinstance(params_data, list):
        return {f'Param {i+1}': val for i, val in enumerate(params_data)}
    else:
        raise ValueError(f"Unexpected format for parameters in {file_path}")


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


def plot_parameters_grid(particle_id, iterations, param_history):
    """
    Plots an individual subplot for each of the 8 parameters across iterations.
    """
    param_names = list(param_history.keys())
    num_params = len(param_names)

    # Configure 2x4 grid layout for 8 parameters
    nrows, ncols = 2, 4
    fig, axes = plt.subplots(nrows, ncols, figsize=(18, 9), sharex=True)
    axes = axes.flatten()

    colors = plt.cm.tab10(np.linspace(0, 1, num_params))

    for idx in range(nrows * ncols):
        ax = axes[idx]
        if idx < num_params:
            param_name = param_names[idx]
            values = param_history[param_name]

            ax.plot(
                iterations,
                values,
                marker='o',
                linestyle='-',
                color=colors[idx],
                linewidth=1.8,
                markersize=4,
                label=param_name
            )

            ax.set_title(f'{param_name}', fontsize=11, fontweight='bold')
            ax.grid(True, linestyle='--', alpha=0.6)
            ax.tick_params(labelsize=10)
            
            # Show initial and final values in legend
            ax.legend(
                [f"Init: {values[0]:.3g}\nFinal: {values[-1]:.3g}"], 
                loc='best', 
                fontsize=8, 
                framealpha=0.8
            )
        else:
            # Hide any unused subplots
            fig.delaxes(ax)

    # Set common x-axis label for bottom row
    for ax in axes[-ncols:]:
        ax.set_xlabel('Iteration Number', fontsize=11)

    fig.suptitle(
        f'Parameter Trajectories Across Iterations (Particle {particle_id})', 
        fontsize=15, 
        fontweight='bold'
    )
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
    param_history = {}

    for item in particle_files:
        try:
            params = get_particle_parameters(item['file_path'])
            iterations.append(item['iteration'])

            # Initialize parameter lists on first iteration
            for key, val in params.items():
                if key not in param_history:
                    param_history[key] = []
                param_history[key].append(val)

        except Exception as e:
            print(f"[WARNING] Could not process {item['file_name']}: {e}")

    if not param_history:
        print("[ERROR] No valid parameter data could be extracted.")
        return

    print(f"Successfully loaded {len(param_history)} parameters across {len(iterations)} iterations.")
    
    # Plot parameter curves
    plot_parameters_grid(particle_id, iterations, param_history)


if __name__ == '__main__':
    PARTICLE_ID = 11
    main(PARTICLE_ID)