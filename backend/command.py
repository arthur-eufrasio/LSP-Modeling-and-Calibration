import sys
import os
import json

os.chdir(os.getenv("BACKEND_PROJECT_PATH"))
sys.dont_write_bytecode = True

from run_simulation import Simulation
from run_extraction import OdbDataExtractor

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
        self.files_cae_dir_path = None

    def _create_directories(self):
        self.backend_project_path = os.getenv("BACKEND_PROJECT_PATH")
        self.log_dir_path = os.path.join(self.backend_project_path, "log")
        self.log_file_path = os.path.join(self.log_dir_path, "abaqus_log.txt")
        self.config_dir_path = os.path.join(self.backend_project_path, "model_config")
        self.data_dir_path = os.path.join(self.backend_project_path, "data")
        self.files_dir_path = os.path.join(self.backend_project_path, "files")
        self.files_inp_dir_path = os.path.join(self.files_dir_path, "inp")
        self.files_job_dir_path = os.path.join(self.files_dir_path, "job")
        self.files_cae_dir_path = os.path.join(self.files_dir_path, "cae")

        directories = [
            self.log_dir_path,
            self.config_dir_path,
            self.data_dir_path,
            self.files_dir_path,
            self.files_inp_dir_path,
            self.files_job_dir_path,
            self.files_cae_dir_path
        ]

        for directory in directories:
            if not os.path.exists(directory):
                os.makedirs(directory)

    def log(self, message, log_file_path):
        log_dir = os.path.dirname(log_file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        with open(log_file_path, "a") as f:
            f.write(message + "\n")

    def _get_all_config_files(self):
        """Retorna todos os arquivos com extensão .json na pasta model_config."""
        files = [
            os.path.join(self.config_dir_path, f)
            for f in os.listdir(self.config_dir_path)
            if f.endswith('.json')
        ]
        files.sort()
        return files

    def _read_config_file(self, config_file_path):
        with open(config_file_path, 'r') as file:
            return json.load(file)

    def _run_simulation(self, config_data, config_name):
        self.log("    [Simulation] Starting simulation for: {}".format(config_name), self.log_file_path)
        simulation = Simulation(config_data, self.data_dir_path)
        simulation.run()
        self.log("    [Simulation] Completed simulation for: {}".format(config_name), self.log_file_path)

    def _run_extraction(self, config_data, config_name):
        self.log("    [Extraction] Starting extraction for: {}".format(config_name), self.log_file_path)
        extraction = OdbDataExtractor(config_data, self.data_dir_path)
        extraction.run()
        self.log("    [Extraction] Completed extraction for: {}".format(config_name), self.log_file_path)

    def run(self):
        self._create_directories()
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)
        
        self.log("[Command] Starting execution...", self.log_file_path)

        config_files = self._get_all_config_files()

        if not config_files:
            self.log("[Command Warning] No .json configuration files found in model_config.", self.log_file_path)
            return

        for index, config_path in enumerate(config_files, start=1):
            config_name = os.path.basename(config_path)
            self.log("\n==================================================", self.log_file_path)
            self.log("[Batch] Processing {}/{} -> {}".format(index, len(config_files), config_name), self.log_file_path)
            self.log("==================================================", self.log_file_path)

            config_data = self._read_config_file(config_path)
            self._run_simulation(config_data, config_name)
            self._run_extraction(config_data, config_name)

        self.log("\n[Command] All simulations and extractions ended successfully.", self.log_file_path)

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