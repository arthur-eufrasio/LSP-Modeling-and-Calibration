import os
import json
import pickle
import subprocess
import numpy as np
import pyswarms as ps
import sys
from utilities.clean_files import clean_files

sys.dont_write_bytecode = True


class PSOCalibrator:
    def __init__(self):
        # Paths configuration (relative to the root directory where the script is executed)
        self.abaqus_cmd_path = 'C:/SIMULIA/Abaqus/Commands/abaqus.bat'
        self.config_file_path = os.path.join('backend', 'model_config', 'model_config.json')
        self.data_file_path = os.path.join('backend', 'data', 'data.json')
        self.target_profile_path = os.path.join('calibration', 'config', 'target_curve.pkl')
        self.calibration_config_path = os.path.join('calibration', 'config', 'calibration_config.json')
        
        # Load the target calibration profile
        self.target_spline = self._load_target_profile()
        
        # Load PSO parameters from the JSON configuration file
        self._load_calibration_config()

    def _load_target_profile(self):
        """Loads the target cubic spline profile from the pickle file."""
        with open(self.target_profile_path, 'rb') as f:
            return pickle.load(f)

    def _load_calibration_config(self):
        """Loads the PSO configuration parameters from the JSON file."""
        with open(self.calibration_config_path, 'r') as f:
            config = json.load(f)

        # Convert the lists from JSON into numpy arrays for PySwarms
        self.bounds_min = np.array(config['pso_optimization_bounds']['bounds_min'])
        self.bounds_max = np.array(config['pso_optimization_bounds']['bounds_max'])
        self.bounds = (self.bounds_min, self.bounds_max)
        
        # Set PSO Hyperparameters
        self.options = config['pso_hyperparameters']
        self.dimensions = config['dimensions']
        self.n_particles = config['n_particles']
        self.n_iterations = config['n_iterations']

    def _update_model_config(self, particle, particle_index):
        """
        Updates the model_config.json file with the parameters from the current particle.
        Assuming particle indices correspond to Johnson-Cook parameters: [a, b, n]
        """
        with open(self.config_file_path, 'r') as file:
            config = json.load(file)

        if particle_index:
            config['lspModel']['modelBuilder']['particleNumber'] = particle_index

        config['lspModel']['modelBuilder']['material']['johnsonCook']['a'] = float(particle[0])
        config['lspModel']['modelBuilder']['material']['johnsonCook']['b'] = float(particle[1])
        config['lspModel']['modelBuilder']['material']['johnsonCook']['n'] = float(particle[2])
        
        with open(self.config_file_path, 'w') as file:
            json.dump(config, file, indent=4)

    def _run_abaqus_simulation(self):
        """Executes the Abaqus simulation via the command file."""
        os.environ["BACKEND_PROJECT_PATH"] = os.path.join(os.getcwd(), "backend")
        abaqus_command = f'"{self.abaqus_cmd_path}" cae noGUI="backend/command.py"'
        
        subprocess.run(
            abaqus_command, shell=True, check=True, capture_output=True, text=True
        )
        clean_files()

    def _evaluate_particle(self, particle, particle_index):
        """
        Runs the simulation for a single particle and calculates the MSE against the target spline.
        """
        try:
            self._update_model_config(particle, particle_index)
            self._run_abaqus_simulation()
            
            with open(self.data_file_path, 'r') as f:
                data = json.load(f)
                
            depth_data = data["lspModel"]["depth"]
            depth_x = np.array([point[0] for point in depth_data])
            simulated_stresses = np.array([point[1] for point in depth_data])
            
            # Evaluate the target spline at the simulated depth coordinates
            target_stresses = self.target_spline(depth_x)
            
            # Calculate Mean Squared Error
            mse = np.mean((simulated_stresses - target_stresses)**2)
            return mse
            
        except Exception as e:
            print(f"[ERROR] Simulation failed for particle {particle}: {e}")
            return 1e6  # High penalty for failed simulation

    def _objective_function(self, particles):
        """
        The objective function called by PySwarms to evaluate the entire swarm.
        """
        n_particles = particles.shape[0]
        costs = np.zeros(n_particles)
        
        for i in range(n_particles):
            print(f"--- Evaluating Particle {i + 1}/{n_particles} ---")
            costs[i] = self._evaluate_particle(particles[i], i)
            print(f"Cost (MSE): {costs[i]:.4f}\n")
            
        return costs

    def run(self):
        """Starts the Particle Swarm Optimization process."""
        print("Starting PSO Calibration...")
        optimizer = ps.single.GlobalBestPSO(
            n_particles=self.n_particles, 
            dimensions=self.dimensions, 
            options=self.options, 
            bounds=self.bounds
        )
        
        best_cost, best_pos = optimizer.optimize(
            self._objective_function, 
            iters=self.n_iterations
        )
        
        print("\n=== Calibration Finished ===")
        print(f"Best Cost (MSE): {best_cost}")
        print(f"Best Parameters: {best_pos}")
        
        # Run one final simulation using the best discovered parameters
        self._update_model_config(best_pos, particle_index=None)
        self._run_abaqus_simulation()
        print("Optimal model simulation saved to backend/data/data.json")