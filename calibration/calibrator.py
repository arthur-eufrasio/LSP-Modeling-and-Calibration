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
        self.abaqus_cmd_path = 'C:/SIMULIA/Abaqus/Commands/abaqus.bat'
        self.config_file_path = os.path.join('backend', 'model_config', 'model_config.json')
        self.data_file_path = None
        self.target_profile_path = os.path.join('calibration', 'config', 'target_curve.pkl')
        self.calibration_config_path = os.path.join('calibration', 'config', 'calibration_config.json')
        
        self.target_spline = self._load_target_profile()
        
        self._load_calibration_config()

    def _load_target_profile(self):
        with open(self.target_profile_path, 'rb') as f:
            return pickle.load(f)

    def _load_calibration_config(self):
        with open(self.calibration_config_path, 'r') as f:
            config = json.load(f)

        self.bounds_min = np.array(config['pso_optimization_bounds']['bounds_min'])
        self.bounds_max = np.array(config['pso_optimization_bounds']['bounds_max'])
        self.bounds = (self.bounds_min, self.bounds_max)
        
        self.options = config['pso_hyperparameters']
        self.dimensions = config['dimensions']
        self.n_particles = config['n_particles']
        self.n_iterations = config['n_iterations']

    def _update_model_config(self, particle, particle_index, iteration_index):
        with open(self.config_file_path, 'r') as file:
            config = json.load(file)

        if particle_index is not None:
            config['lspModel']['modelBuilder']['particleNumber'] = particle_index
        
        if iteration_index is not None:
            config['lspModel']['modelBuilder']['iterationNumber'] = iteration_index

        config['lspModel']['modelBuilder']['material']['johnsonCook']['a'] = float(particle[0])
        config['lspModel']['modelBuilder']['material']['johnsonCook']['b'] = float(particle[1])
        config['lspModel']['modelBuilder']['material']['johnsonCook']['n'] = float(particle[2])
        
        with open(self.config_file_path, 'w') as file:
            json.dump(config, file, indent=4)

    def _run_abaqus_simulation(self):
        os.environ["BACKEND_PROJECT_PATH"] = os.path.join(os.getcwd(), "backend")
        abaqus_command = f'"{self.abaqus_cmd_path}" cae noGUI="backend/command.py"'
        
        subprocess.run(
            abaqus_command, shell=True, check=True, capture_output=True, text=True
        )
        clean_files()

    def _evaluate_particle(self, particle, particle_index):
        try:
            self._update_model_config(particle, particle_index, self.current_iteration)
            self._run_abaqus_simulation()

            data_file_name = f'data_i{self.current_iteration}_p{particle_index}.json'
            self.data_file_path = os.path.join('backend', 'data', data_file_name)
            with open(self.data_file_path, 'r') as f:
                data = json.load(f)
            
            data_key_name = f"lspModel_i{self.current_iteration}_p{particle_index}"
            surface_data = data[data_key_name]["surface"]
            surface_data_x = np.array([point[0] for point in surface_data])
            simulated_stresses = np.array([point[1] for point in surface_data])
            
            target_stresses = self.target_spline(surface_data_x)
            
            mse = np.mean((simulated_stresses - target_stresses)**2)
            return mse
            
        except Exception as e:
            print(f"[ERROR] Simulation failed for particle {particle}: {e}")
            return 1e6  

    def _objective_function(self, particles):
        n_particles = particles.shape[0]
        costs = np.zeros(n_particles)
        
        print(f"\n=== Iteration {self.current_iteration + 1} ===")
        for i in range(n_particles):
            print(f"--- Evaluating Particle {i + 1}/{n_particles} ---")
            costs[i] = self._evaluate_particle(particles[i], i)
            print(f"Cost (MSE): {costs[i]:.4f}\n")
        
        self.current_iteration += 1

        return costs

    def run(self):
        print("Starting PSO Calibration...")
        optimizer = ps.single.GlobalBestPSO(
            n_particles=self.n_particles, 
            dimensions=self.dimensions, 
            options=self.options, 
            bounds=self.bounds
        )

        self.current_iteration = 0

        best_cost, best_pos = optimizer.optimize(
            self._objective_function, 
            iters=self.n_iterations
        )
        
        print("\n=== Calibration Finished ===")
        print(f"Best Cost (MSE): {best_cost}")
        print(f"Best Parameters: {best_pos}")