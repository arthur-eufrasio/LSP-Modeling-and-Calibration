import sys
import os
import json

os.chdir(os.getenv("BACKEND_PROJECT_PATH"))
sys.dont_write_bytecode = True

from run_simulation import Simulation

class Command:
    def __init__(self):
        self.backend_project_path = None
        self.log_dir_path = None
        self.log_file_path = None
        self.config_dir_path = None
        self.data_dir_path = None
        self.files_dir_path = None
        self.files_inp_dir_path = None
        self.files_job_dir_path = None

    def _create_directories(self):
        self.backend_project_path = os.getenv("BACKEND_PROJECT_PATH")
        self.log_dir_path = os.path.join(self.backend_project_path, "log")
        self.log_file_path = os.path.join(self.log_dir_path, "abaqus_log.txt")
        self.config_dir_path = os.path.join(self.backend_project_path, "model_config")
        self.data_dir_path = os.path.join(self.backend_project_path, "data")
        self.files_dir_path = os.path.join(self.backend_project_path, "files")
        self.files_inp_dir_path = os.path.join(self.files_dir_path, "inp")
        self.files_job_dir_path = os.path.join(self.files_dir_path, "job")

        if not os.path.exists(self.log_dir_path):
            os.makedirs(self.log_dir_path)

        if not os.path.exists(self.config_dir_path):
            os.makedirs(self.config_dir_path)

        if not os.path.exists(self.data_dir_path):
            os.makedirs(self.data_dir_path)

        if not os.path.exists(self.files_dir_path):
            os.makedirs(self.files_dir_path)

        if not os.path.exists(self.files_inp_dir_path):
            os.makedirs(self.files_inp_dir_path)

        if not os.path.exists(self.files_job_dir_path):
            os.makedirs(self.files_job_dir_path)

    def log(self, message, log_file_path):
        with open(log_file_path, "a") as f:
            f.write(message + "\n")

    def _read_model_config(self):
        config_file_path = os.path.join(self.config_dir_path, "model_config.json")
        with open(config_file_path, 'r') as file:
            config_data = json.load(file)
            
        return config_data

    def _run_simulation(self):
        self.log("    [Simulation] Starting simulation.", self.log_file_path)
        
        config_data = self._read_model_config()
        simulation = Simulation(config_data, self.data_dir_path)
        simulation.run()
        
        self.log("    [Simulation] The simulation was completed.", self.log_file_path)

    def run(self):
        self._create_directories()
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)
        
        self.log("[Command] Starting execution...", self.log_file_path)
        
        self._run_simulation()
        
        self.log("[Command] End.", self.log_file_path)

if __name__ == "__main__":
    try:
        command = Command()
        command.run()
    except Exception as e:
        import traceback

        backend_project_path = os.getenv("BACKEND_PROJECT_PATH")
        log_dir = os.path.join(backend_project_path, "log")
        log_file_path = os.path.join(log_dir, "abaqus_log.txt")

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        with open(log_file_path, "a") as f:
            f.write("\n====================================================\n")
            f.write("\n[COMMAND ERROR] An exception occurred during execution:\n")
            traceback.print_exc(file=f)
            f.write("\n====================================================\n")