import os
import json
import shutil
import subprocess
import queue
import concurrent.futures
import numpy as np
import pyswarms as ps
import sys
import time
from scipy.interpolate import interp1d

from calibration.target_curve import load_target_curve

sys.dont_write_bytecode = True


class PSOCalibrator:
    def __init__(self, n_workers=5, cpus_per_job=1):
        """
        n_workers    -> quantas simulacoes Abaqus rodam ao mesmo tempo
        cpus_per_job -> quantas CPUs cada simulacao usa (numCPUs/numDomains)

        Regra pratica: n_workers * cpus_per_job ~= nucleos disponiveis.
        O ponto otimo entre esses dois numeros depende de como o Abaqus/Explicit
        escala nesse modelo especifico -- vale rodar um pequeno benchmark
        (mesma particula com 1, 2, 4, 8 CPUs) e comparar tempo de parede
        antes de fixar os valores.
        """
        self.abaqus_cmd_path = 'C:/SIMULIA/Abaqus/Commands/abaqus.bat'
        self.template_config_path = os.path.join('backend', 'model_config', 'model_config.json')
        self.target_profile_path = os.path.join('calibration', 'config', 'target_curve.csv')
        self.calibration_config_path = os.path.join('calibration', 'config', 'calibration_config.json')

        self.n_workers = n_workers
        self.cpus_per_job = cpus_per_job

        available_cores = os.cpu_count() or 1
        if n_workers * cpus_per_job > available_cores:
            print(f"[WARNING] n_workers ({n_workers}) x cpus_per_job ({cpus_per_job}) = "
                  f"{n_workers * cpus_per_job} > {available_cores} nucleos disponiveis.")

        self.slot_paths = []
        self.slot_pool = queue.Queue()
        self._setup_worker_slots()

        self.target_coords, self.target_stresses = self._load_target_profile()
        self._load_calibration_config()

    def _setup_worker_slots(self):
        """Cria um diretorio 'backend_slot_N' isolado por worker, cada um com sua
        propria arvore model_config/data/log/files. command.py, run_simulation.py
        e run_extraction.py continuam centralizados em 'backend/' e NAO sao
        copiados -- so o diretorio de trabalho (BACKEND_PROJECT_PATH) muda."""
        for slot_id in range(self.n_workers):
            backend_path = os.path.join(os.getcwd(), f'backend_slot_{slot_id}')
            self._ensure_backend_directories(backend_path)

            slot_config_path = os.path.join(backend_path, 'model_config', 'model_config.json')
            shutil.copy(self.template_config_path, slot_config_path)

            self.slot_paths.append(backend_path)
            self.slot_pool.put(slot_id)

    def _ensure_backend_directories(self, backend_path):
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

    def _update_model_config(self, slot_id, particle, particle_index, iteration_index):
        config_path = os.path.join(self.slot_paths[slot_id], 'model_config', 'model_config.json')
        with open(config_path, 'r') as file:
            config = json.load(file)

        config['lspModel']['modelBuilder']['particleNumber'] = particle_index
        config['lspModel']['modelBuilder']['iterationNumber'] = iteration_index
        config['lspModel']['modelBuilder']['job']['numCPUs'] = self.cpus_per_job

        model_builder = config['lspModel']['modelBuilder']
        for parameter_name, parameter_value in zip(self.parameter_names, particle):
            if not self._set_nested_model_value(model_builder, parameter_name, parameter_value):
                raise KeyError(f"Parameter '{parameter_name}' not found in model configuration.")

        with open(config_path, 'w') as file:
            json.dump(config, file, indent=4)

    def _run_abaqus_simulation(self, slot_id):
        backend_path = self.slot_paths[slot_id]
        backend_source_dir = os.path.abspath('backend')
        command_script_path = os.path.join(backend_source_dir, 'command.py')

        env = os.environ.copy()
        env["BACKEND_PROJECT_PATH"] = backend_path
        env["BACKEND_SOURCE_DIR"] = backend_source_dir
        env["PYTHONPATH"] = backend_source_dir + os.pathsep + os.getcwd() + os.pathsep + env.get("PYTHONPATH", "")

        abaqus_command = f'"{self.abaqus_cmd_path}" cae noGUI="{command_script_path}"'

        log_dir = os.path.join(backend_path, "log")
        stdout_path = os.path.join(log_dir, "subprocess_stdout.log")
        stderr_path = os.path.join(log_dir, "subprocess_stderr.log")

        MAX_SIMULATION_TIME = 600

        try:
            with open(stdout_path, "w") as out_file, open(stderr_path, "w") as err_file:
                subprocess.run(
                    abaqus_command,
                    shell=True,
                    check=True,
                    cwd=backend_path,
                    stdout=out_file,
                    stderr=err_file,
                    text=True,
                    env=env,
                    timeout=MAX_SIMULATION_TIME
                )
        except subprocess.TimeoutExpired:
            print(f"[WARNING][slot {slot_id}] Abaqus excedeu {MAX_SIMULATION_TIME}s. Encerrando.")
            raise RuntimeError("Simulation timed out due to severe element distortion or hanging.")
        except subprocess.CalledProcessError as e:
            error_details = ""
            if os.path.exists(stderr_path):
                with open(stderr_path, "r") as f:
                    error_details = f.read().strip()
            if not error_details and os.path.exists(stdout_path):
                with open(stdout_path, "r") as f:
                    lines = f.readlines()
                    error_details = "".join(lines[-10:]).strip()
            
            print(f"[ERROR][slot {slot_id}] Abaqus falhou com codigo {e.returncode}. Motivo: {error_details}")
            raise
        finally:
            try:
                from utilities.clean_files import clean_files
                clean_files(backend_path)
            except ImportError:
                try:
                    from clean_files import clean_files
                    clean_files(backend_path)
                except Exception:
                    pass

    def _evaluate_particle(self, particle, particle_index, slot_id):
        try:
            self._update_model_config(slot_id, particle, particle_index, self.current_iteration)
            self._run_abaqus_simulation(slot_id)

            data_file_name = f'data_i{self.current_iteration}_p{particle_index}.json'
            data_file_path = os.path.join(self.slot_paths[slot_id], 'data', data_file_name)

            with open(data_file_path, 'r') as f:
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
                simulated_averages.append(np.mean(sim_interp(eval_points)))
                prev_depth = current_depth

            simulated_averages = np.array(simulated_averages)
            mse = float(np.mean((simulated_averages - self.target_stresses) ** 2))

            parameters_dict = {name: float(val) for name, val in zip(self.parameter_names, particle)}
            data[data_key_name]["parameters"] = parameters_dict
            data[data_key_name]["mse"] = mse

            with open(data_file_path, 'w') as f:
                json.dump(data, f, indent=4)

            return mse

        except Exception as e:
            print(f"[ERROR] Simulacao falhou para a particula {particle} (slot {slot_id}): {e}")
            return 1e6

    def _evaluate_particle_with_slot(self, particle, particle_index):
        """Pega um slot livre da fila (bloqueia se todos estiverem ocupados),
        roda a particula nele, e devolve o slot ao final -- garante que dois
        workers nunca usem o mesmo diretorio ao mesmo tempo."""
        slot_id = self.slot_pool.get()
        try:
            return self._evaluate_particle(particle, particle_index, slot_id)
        finally:
            self.slot_pool.put(slot_id)

    def _objective_function(self, particles):
        current_w = self.w_max - ((self.w_max - self.w_min) * (self.current_iteration / self.n_iterations))
        self.optimizer.options['w'] = current_w

        n_particles = particles.shape[0]
        costs = np.zeros(n_particles)

        print(f"\n=== Iteracao {self.current_iteration + 1}/{self.n_iterations} (w = {current_w:.4f}) ===")
        print(f"    Avaliando {n_particles} particulas com {self.n_workers} workers "
              f"({self.cpus_per_job} CPUs cada)")

        with concurrent.futures.ThreadPoolExecutor(max_workers=self.n_workers) as executor:
            future_to_index = {
                executor.submit(self._evaluate_particle_with_slot, particles[i], i): i
                for i in range(n_particles)
            }
            for future in concurrent.futures.as_completed(future_to_index):
                i = future_to_index[future]
                costs[i] = future.result()
                print(f"    Particula {i + 1}/{n_particles} -> MSE = {costs[i]:.4f}")

        self.current_iteration += 1
        return costs

    def run(self):
        print("Starting PSO Calibration (parallel)...")
        start_time = time.perf_counter()

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

        total_time = time.perf_counter() - start_time
        mins, secs = divmod(total_time, 60)
        hours, mins = divmod(mins, 60)

        print("\n=== Calibration Finished ===")
        print(f"Best Cost (MSE): {best_cost}")
        print(f"Best Parameters: {best_pos}")
        print(f"=== Time - {int(hours):02d}h {int(mins):02d}m {secs:05.2f}s ({total_time:.2f}s total) ===")