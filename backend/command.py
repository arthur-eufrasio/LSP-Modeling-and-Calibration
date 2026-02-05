import sys
import os
import json

os.chdir(os.getenv("BACKEND_PROJECT_PATH"))
sys.dont_write_bytecode = True

from ModelBuilder import ModelBuilder

class Command:
    def __init__(self):
        self.backend_project_path = os.getenv("BACKEND_PROJECT_PATH")
        self.log_file_path = os.path.join(self.backend_project_path, "log", "abaqus_log.txt")
        self.config_dir_path = None
        self.data_dir_path = None

    def run(self):
        if os.path.exists(self.log_file_path):
            os.remove(self.log_file_path)
        
        self.log("[Command] Starting execution...", self.log_file_path)
        
        self.create_paths()
        self.run_model_builder()
        
        self.log("[Command] End.", self.log_file_path)

    def log(self, message, log_file_path):
        log_directory = os.path.dirname(log_file_path)
        if not os.path.exists(log_directory):
            os.makedirs(log_directory)

        with open(log_file_path, "a") as f:
            f.write(message + "\n")

    def create_paths(self):
        self.config_dir_path = os.path.join(os.path.dirname(self.backend_project_path), "backend/model_config")
        self.data_dir_path = os.path.join(os.path.dirname(self.backend_project_path), "backend/data")
        
        self.log("[Command] Paths created successfully.", self.log_file_path)
        self.log("       - Config Path: " + self.config_dir_path, self.log_file_path)
        self.log("       - Data Path: " + self.data_dir_path, self.log_file_path)

    def read_config_data(self):
        config_file_path = os.path.join(self.config_dir_path, "model_config.json")
        
        with open(config_file_path, 'r') as file:
            config_data = json.load(file)
            
        return config_data

    def run_model_builder(self):
        self.log("[Command] Beginning extraction...", self.log_file_path)
        
        config_data = self.read_config_data()
        model_builder = ModelBuilder(config_data, self.data_dir_path)
        model_builder.run()
        
        self.log("       [Extraction] The extraction was completed.", self.log_file_path)

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