import os
import json
import pickle
import subprocess
import numpy as np
import pyswarms as ps
from utilities.clean_files import clean_files

class PSOCalibrator:
    def __init__(self):
        # Paths configuration (relative to the root directory where the script is executed)
        self.abaqus_cmd_path = r'C:\SIMULIA\Abaqus\Commands\abaqus.bat'
        self.config_file_path = os.path.join('backend', 'model_config', 'model_config.json')
        self.data_file_path = os.path.join('backend', 'data', 'data.json')
        self.target_profile_path = os.path.join('calibration', 'martin_senai_rs_profile.pkl')
        
        # Load the target calibration profile
        self.target_spline = self._load_target_profile()
        
        # PSO Optimization Bounds (Example limits for Johnson-Cook: a, b, n)
        self.bounds_min = np.array([100.0, 200.0, 0.1])
        self.bounds_max = np.array([500.0, 800.0, 0.9])
        self.bounds = (self.bounds_min, self.bounds_max)
        
        # PSO Hyperparameters
        self.options = {'c1': 0.5, 'c2': 0.3, 'w': 0.9}
        self.dimensions = 3
        self.n_particles = 5
        self.n_iterations = 10

    def _load_target_profile(self):
        """Loads the target cubic spline profile from the pickle file."""
        with open(self.target_profile_path, 'rb') as f:
            return pickle.load(f)

    def _update_model_config(self, particle):
        """
        Updates the model_config.json file with the parameters from the current particle.
        Assuming particle indices correspond to Johnson-Cook parameters: [a, b, n]
        """
        with open(self.config_file_path, 'r') as file:
            config = json.load(file)
            
        config['lspModel01']['modelBuilder']['material']['johnsonCook']['a'] = float(particle[0])
        config['lspModel01']['modelBuilder']['material']['johnsonCook']['b'] = float(particle[1])
        config['lspModel01']['modelBuilder']['material']['johnsonCook']['n'] = float(particle[2])
        
        with open(self.config_file_path, 'w') as file:
            json.dump(config, file, indent=4)

    def _run_abaqus_simulation(self):
        """Executes the Abaqus simulation via the command file."""
        os.environ["BACKEND_PROJECT_PATH"] = os.path.join(os.getcwd(), "backend")
        abaqus_command = f'"{self.abaqus_cmd_path}" cae startup="backend/command.py"'
        
        subprocess.run(
            abaqus_command, shell=True, check=True, capture_output=True, text=True
        )
        clean_files()

    def _evaluate_particle(self, particle):
        """
        Runs the simulation for a single particle and calculates the MSE against the target spline.
        """
        try:
            self._update_model_config(particle)
            self._run_abaqus_simulation()
            
            with open(self.data_file_path, 'r') as f:
                data = json.load(f)
                
            depth_data = data["lspModel01"]["depth"]
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
            costs[i] = self._evaluate_particle(particles[i])
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
        self._update_model_config(best_pos)
        self._run_abaqus_simulation()
        print("Optimal model simulation saved to backend/data/data.json")