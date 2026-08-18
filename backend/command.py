# backend/command.py
import sys
import os
import json

# 1. Garante que o diretório 'backend' esteja no sys.path
current_script_dir = os.path.dirname(os.path.abspath(__file__))
if current_script_dir not in sys.path:
    sys.path.insert(0, current_script_dir)

# 2. Muda o diretório para o slot isolado
backend_project_path = os.environ.get("BACKEND_PROJECT_PATH", current_script_dir)
os.chdir(backend_project_path)
sys.dont_write_bytecode = True

from run_simulation import Simulation
from run_extraction import OdbDataExtractor

class Command:
    def __init__(self):
        self.backend_project_path = os.environ["BACKEND_PROJECT_PATH"]
        self.log_dir_path = os.path.join(self.backend_project_path, "log")
        self.log_file_path = os.path.join(self.log_dir_path, "abaqus_log.txt")
        self.config_dir_path = os.path.join(self.backend_project_path, "model_config")
        self.data_dir_path = os.path.join(self.backend_project_path, "data")
        self.files_dir_path = os.path.join(self.backend_project_path, "files")
        self.files_cae_dir_path = os.path.join(self.files_dir_path, "cae")
        self.files_inp_dir_path = os.path.join(self.files_dir_path, "inp")
        self.files_job_dir_path = os.path.join(self.files_dir_path, "job")

    def _create_directories(self):
        directories = [
            self.log_dir_path,
            self.config_dir_path,
            self.data_dir_path,
            self.files_dir_path,
            self.files_cae_dir_path,
            self.files_inp_dir_path,
            self.files_job_dir_path
        ]

        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def log(self, message):
        with open(self.log_file_path, "a") as f:
            f.write(message + "\n")

    def _read_model_config(self):
        config_file_path = os.path.join(self.config_dir_path, "model_config.json")
        with open(config_file_path, 'r') as file:
            config_data = json.load(file)
        return config_data

    def _run_simulation(self):
        self.log("    [Simulation] Starting simulation.")
        config_data = self._read_model_config()
        simulation = Simulation(config_data, self.data_dir_path)
        simulation.run()
        self.log("    [Simulation] The simulation was completed.")

    def _run_extraction(self):
        self.log("    [Extraction] Starting extraction.")
        config_data = self._read_model_config()
        extraction = OdbDataExtractor(config_data, self.data_dir_path)
        extraction.run()
        self.log("    [Extraction] The extraction was completed.")

    def run(self):
        self._create_directories()
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)
        
        self.log("[Command] Starting execution...")
        self._run_simulation()
        self._run_extraction()  
        self.log("[Command] End.")

if __name__ == "__main__":
    try:
        command = Command()
        command.run()
    except Exception as e:
        import traceback

        backend_project_path = os.environ.get("BACKEND_PROJECT_PATH", os.getcwd())
        log_dir = os.path.join(backend_project_path, "log")
        log_file_path = os.path.join(log_dir, "abaqus_log.txt")

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        with open(log_file_path, "a") as f:
            f.write("\n====================================================\n")
            f.write("[COMMAND ERROR] An exception occurred during execution:\n")
            traceback.print_exc(file=f)
            f.write("====================================================\n")
        sys.exit(1)