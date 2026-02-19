import json
import os
from abaqus import session
from abaqusConstants import *
from odbAccess import openOdb


class OdbDataExtractor:
    def __init__(self, model_config, path_data_dir):
        self.fullConfig = model_config
        self.odbName = str(self.fullConfig.keys()[0])
        self.modelBuilder = self.fullConfig[self.odbName]['modelBuilder']
        self.odbExtractor = self.fullConfig[self.odbName]['odbExtractor']
        self.extractedData = {}
        self.pathDataDir = path_data_dir
        self.backendPath = os.path.dirname(self.pathDataDir)
        self.logFilePath = os.path.join(self.backendPath, "log", "abaqus_log.txt")
        
    def log(self, msg, log_file_path):
        log_dir = os.path.dirname(log_file_path)
        if not os.path.exists(log_dir):
            os.makedirs(log_dir)
        log_path = os.path.join(log_dir, "abaqus_log.txt")

        with open(log_path, "a") as f:
            f.write(msg + "\n")
            f.flush()

    def run(self):
        self.process_odb(self.odbName, self.odbExtractor, self.modelBuilder)
        self.save_to_json()

    def process_odb(self, odb_name, odb_config, model_config):
        self.log("      - Processing ODB: {}...".format(odb_name), self.logFilePath)

        odb_path = os.path.join(self.backendPath, "files", "job", "{}.odb".format(odb_name))
        self.odb = openOdb(path=odb_path)
        session.viewports['Viewport: 1'].setValues(displayedObject=self.odb)

        step_name = str(odb_config["stepName"])
        last_frame_index = len(self.odb.steps[step_name].frames) - 1

        surface_point_path = odb_config["surfacePointPath"]
        height_model = model_config["geometry"]["heightFiniteCube"] + model_config["geometry"]["infiniteBorder"]
        surface_point_path[0][1] = height_model
        surface_point_path[1][1] = height_model

        depth_point_path = odb_config["depthPointPath"]
        depth_point_path[0][1] = height_model

        path_obj_name = "surface_path_{}".format(odb_name)
        path_points = tuple(tuple(p) for p in surface_point_path)
        surface_path = session.Path(
                name=path_obj_name,
                type=POINT_LIST,
                expression=path_points
            )
        
        path_obj_name = "depth_path_{}".format(odb_name)
        path_points = tuple(tuple(p) for p in depth_point_path)
        depth_path = session.Path(
                name=path_obj_name,
                type=POINT_LIST,
                expression=path_points
            )
        
        self.extractedData[odb_name] = {}
    
        xy_data_obj = session.XYDataFromPath(
            name="temp_xy_data",
            path=surface_path,
            frame=last_frame_index,
            step=1,
            includeIntersections=True,
            shape=UNDEFORMED,
            labelType=TRUE_DISTANCE,
            variable=('S', INTEGRATION_POINT, ((COMPONENT, 'S11'),)),
            pathStyle=PATH_POINTS
        )
        self.extractedData[odb_name]['surface'] = xy_data_obj.data

        xy_data_obj = session.XYDataFromPath(
            name="temp_xy_data",
            path=depth_path,
            frame=last_frame_index,
            step=1,
            includeIntersections=True,
            shape=UNDEFORMED,
            labelType=TRUE_DISTANCE,
            variable=('S', INTEGRATION_POINT, ((COMPONENT, 'S11'),)),
            pathStyle=PATH_POINTS
        )
        self.extractedData[odb_name]['depth'] = xy_data_obj.data
        
    def save_to_json(self):
        self.log("      - Saving data to JSON...")
        output_path = os.path.join(self.pathDataDir, "data.json")

        with open(output_path, "w") as f:
            json.dump(self.extractedData, f, indent=4)

        self.log("      - File saved: {}".format(output_path))
