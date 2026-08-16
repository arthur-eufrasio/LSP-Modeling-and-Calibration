import os
import json
import subprocess
import numpy as np
import pyswarms as ps
import sys
from scipy.interpolate import interp1d

from calibration.target_curve import load_target_curve

sys.dont_write_bytecode = True


class PSOCalibrator:
    def __init__(self):
        self.abaqus_cmd_path = 'C:/SIMULIA/Abaqus/Commands/abaqus.bat'
        self.config_file_path = os.path.join('backend', 'model_config', 'model_config.json')
        self.data_file_path = None
        self.target_profile_path = os.path.join('calibration', 'config', 'target_curve.csv')
        self.calibration_config_path = os.path.join('calibration', 'config', 'calibration_config.json')
        
        self._ensure_backend_directories()
        self.target_coords, self.target_stresses = self._load_target_profile()
        self._load_calibration_config()

    def _ensure_backend_directories(self):
        backend_path = os.path.join(os.getcwd(), 'backend')
        required_dirs = [
            os.path.join(backend_path, 'data'),
            os.path.join(backend_path, 'log'),
            os.path.join(backend_path, 'files'),
            os.path.join(backend_path, 'files', 'cae'),
            os.path.join(backend_path, 'files', 'inp'),
            os.path.join(backend_path, 'files', 'job'),
            os.path.join(backend_path, 'model_config')
        ]
        for directory in required_dirs:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def _load_target_profile(self):
        return load_target_curve(self.target_profile_path)

    def _load_calibration_config(self):
        with open(self.calibration_config_path, 'r') as f:
            config = json.load(f)

        bounds_config = config['pso_optimization_bounds']
        self.parameter_names = list(bounds_config.keys())
        self.bounds_min = np.array([bounds_config[name]['min'] for name in self.parameter_names], dtype=float)
        self.bounds_max = np.array([bounds_config[name]['max'] for name in self.parameter_names], dtype=float)
        self.bounds = (self.bounds_min, self.bounds_max)
        
        self.options = config['pso_hyperparameters']
        self.dimensions = len(bounds_config)
        self.n_particles = config['n_particles']
        self.n_iterations = config['n_iterations']

        self.w_max = config['w_max']
        self.w_min = config['w_min']

    def _set_nested_model_value(self, container, parameter_name, value):
        if not isinstance(container, dict):
            return False

        if parameter_name in container and not isinstance(container[parameter_name], dict):
            container[parameter_name] = float(value)
            return True

        for nested_value in container.values():
            if isinstance(nested_value, dict) and self._set_nested_model_value(nested_value, parameter_name, value):
                return True

        return False

    def _update_model_config(self, particle, particle_index, iteration_index):
        with open(self.config_file_path, 'r') as file:
            config = json.load(file)

        if particle_index is not None:
            config['lspModel']['modelBuilder']['particleNumber'] = particle_index
        
        if iteration_index is not None:
            config['lspModel']['modelBuilder']['iterationNumber'] = iteration_index

        model_builder = config['lspModel']['modelBuilder']
        for parameter_name, parameter_value in zip(self.parameter_names, particle):
            if not self._set_nested_model_value(model_builder, parameter_name, parameter_value):
                raise KeyError(f"Parameter '{parameter_name}' not found in model configuration.")
        
        with open(self.config_file_path, 'w') as file:
            json.dump(config, file, indent=4)

    def _run_abaqus_simulation(self):
        backend_path = os.path.join(os.getcwd(), "backend")
        os.environ["BACKEND_PROJECT_PATH"] = backend_path
        abaqus_command = f'"{self.abaqus_cmd_path}" cae noGUI="backend/command.py"'
        
        log_dir = os.path.join(backend_path, "log")
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        stdout_path = os.path.join(log_dir, "subprocess_stdout.log")
        stderr_path = os.path.join(log_dir, "subprocess_stderr.log")

        MAX_SIMULATION_TIME = 600 

        try:
            with open(stdout_path, "w") as out_file, open(stderr_path, "w") as err_file:
                subprocess.run(
                    abaqus_command, 
                    shell=True, 
                    check=True, 
                    stdout=out_file, 
                    stderr=err_file, 
                    text=True,
                    timeout=MAX_SIMULATION_TIME
                )
        except subprocess.TimeoutExpired:
            print(f"\n[WARNING] Abaqus simulation exceeded {MAX_SIMULATION_TIME} seconds. Killing process...")
            raise RuntimeError("Simulation timed out due to severe element distortion or hanging.")
        except subprocess.CalledProcessError as e:
            print(f"\n[ERROR] Abaqus failed with return code {e.returncode}.")
            raise
        finally:
            from utilities.clean_files import clean_files
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
            depth_data = data[data_key_name]["depth"]
            depth_data_y = np.array([point[0] for point in depth_data])
            simulated_stresses = np.array([point[1] for point in depth_data])
            
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
            
            for current_depth in self.target_coords:
                eval_points = np.linspace(prev_depth, current_depth, 50)
                avg_simulated_stress = np.mean(sim_interp(eval_points))
                
                simulated_averages.append(avg_simulated_stress)
                prev_depth = current_depth
                
            simulated_averages = np.array(simulated_averages)
            mse = float(np.mean((simulated_averages - self.target_stresses)**2))

            # Store parameters and MSE inside the particle JSON file
            parameters_dict = {name: float(val) for name, val in zip(self.parameter_names, particle)}
            data[data_key_name]["parameters"] = parameters_dict
            data[data_key_name]["mse"] = mse

            with open(self.data_file_path, 'w') as f:
                json.dump(data, f, indent=4)

            return mse
            
        except Exception as e:
            print(f"[ERROR] Simulation failed for particle {particle}: {e}")
            return 1e6  

    def _objective_function(self, particles):
        current_w = self.w_max - ((self.w_max - self.w_min) * (self.current_iteration / self.n_iterations))
        self.optimizer.options['w'] = current_w

        n_particles = particles.shape[0]
        costs = np.zeros(n_particles)
        
        print(f"\n=== Iteration {self.current_iteration + 1}/{self.n_iterations} (w = {current_w:.4f}) ===")
        for i in range(n_particles):
            print(f"--- Evaluating Particle {i + 1}/{n_particles} ---")
            costs[i] = self._evaluate_particle(particles[i], i)
            print(f"Cost (MSE): {costs[i]:.4f}\n")
        
        self.current_iteration += 1

        return costs

    def run(self):
        print("Starting PSO Calibration...")
        self.optimizer = ps.single.GlobalBestPSO(
            n_particles=self.n_particles, 
            dimensions=self.dimensions, 
            options=self.options, 
            bounds=self.bounds
        )

        self.current_iteration = 0

        best_cost, best_pos = self.optimizer.optimize(
            self._objective_function, 
            iters=self.n_iterations
        )
        
        print("\n=== Calibration Finished ===")
        print(f"Best Cost (MSE): {best_cost}")
        print(f"Best Parameters: {best_pos}")