# -*- coding: utf-8 -*-
import sys
import os
import json

os.chdir(os.getenv("BACKEND_PROJECT_PATH", None))
sys.dont_write_bytecode = True

from ModelBuilder import ModelBuilder

from abaqus import *
from abaqusConstants import *
from part import *
from step import *
from material import *
from section import *
from assembly import *
from interaction import *
from mesh import *
from visualization import *
from connectorBehavior import *


class Command:
    def __init__(self):
        self.backendProjectPath = os.getenv("BACKEND_PROJECT_PATH", None)
        self.logFilePath = os.path.join(self.backendProjectPath, "log", "abaqus_log.txt")
        
        if os.path.exists(self.logFilePath):
            os.remove(self.logFilePath)
        self.log("[Command] Iniciando execução...\n", self.logFilePath)

        self.create_paths()
        self.start_extractor()

        self.log("[Command] End.", self.logFilePath)

    def log(self, msg, log_file_path):
        log_dir = os.path.dirname(log_file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, "abaqus_log.txt")

        with open(log_path, "a") as f:
            f.write(msg + "\n")
            f.flush()

    def create_paths(self):
        self.backend_project_path = os.getenv("BACKEND_PROJECT_PATH", None)

        self.path_dir_config = os.path.join(
            os.path.dirname(self.backend_project_path), "backend/model_config"
        )
        self.path_data_dir = os.path.join(
            os.path.dirname(self.backend_project_path), "backend/data"
        )

        self.log("[Command] The paths to the directories were successfully created.", self.logFilePath)
        self.log("       - Extraction Directory Config Path: " + self.path_dir_config, self.logFilePath)
        self.log("       - Extraction Directory Data Path: " + self.path_data_dir, self.logFilePath)

    def read_data(self):
        path_model_config = os.path.join(
            self.path_dir_config, "model_config.json"
        )

        with open(path_model_config, 'r') as file:
            model_config = json.load(file)

        return model_config

    def start_extractor(self):
        self.log("[Command] Beggining extraction....", self.logFilePath)

        model_config = self.read_data()
        modelBuilder = ModelBuilder(model_config, self.path_data_dir)
        modelBuilder.run()

        self.log("       [Extraction] The extraction was completed.", self.logFilePath)


if __name__ == "__main__":
    try:
        model = Command()
    except Exception as e:
        import traceback

        backend_project_path = os.getenv("BACKEND_PROJECT_PATH", None)
        log_dir = os.path.join(backend_project_path, "log")
        log_file_path = os.path.join(backend_project_path, "log", "abaqus_log.txt")

        if not os.path.exists(log_dir):
            os.makedirs(log_dir)

        with open(log_file_path, "a") as f:
            f.write("\n====================================================\n")
            f.write("\n[COMMAND ERROR] An exception occurred during execution:\n")
            traceback.print_exc(file=f)
            f.write("\n====================================================\n")

