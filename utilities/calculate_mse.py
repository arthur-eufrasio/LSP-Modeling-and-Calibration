import glob
import json
import os
import numpy as np
import pandas as pd

# 1. Resolução dinâmica dos caminhos
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_folder = os.path.join(base_dir, "backend", "data")
target_file = os.path.join(base_dir, "target_curve.csv")

if not os.path.exists(data_folder):
    data_folder = "C:/Users/arthu/Desktop/arthur/git/LSP-Modeling-and-Calibration/backend/data/"
if not os.path.exists(target_file):
    target_file = "C:/Users/arthu/Desktop/arthur/git/LSP-Modeling-and-Calibration/target_curve.csv"

# 2. Carregar curva alvo experimental (target)
target_df = pd.read_csv(target_file)
exp_depth_ends = target_df.iloc[:, 0].values.astype(float)
exp_stresses = target_df.iloc[:, 1].values.astype(float)
edges = np.insert(exp_depth_ends, 0, 0.0)

# 3. Carregar primeira curva do primeiro JSON
search_pattern = os.path.join(data_folder, "*_stress_profile.json")
json_files = sorted(glob.glob(search_pattern))

if not json_files:
    raise FileNotFoundError(f"Nenhum arquivo encontrado em {data_folder} com o padrão '{search_pattern}'")

with open(json_files[0], "r", encoding="utf-8") as f:
    data = json.load(f)

first_model_name = next(iter(data))
depth_data = np.array(data[first_model_name]["depth"])
sim_depths = depth_data[:, 0]
sim_stresses = depth_data[:, 1]

# 4. Cálculo das diferenças por incremento
diffs = []
for i in range(len(exp_stresses)):
    z_min = edges[i]
    z_max = edges[i + 1]

    mask = (sim_depths >= z_min) & (sim_depths <= z_max)
    points_in_interval = sim_stresses[mask]

    if len(points_in_interval) > 0:
        sim_mean = np.mean(points_in_interval)
        diffs.append(sim_mean - exp_stresses[i])

# 5. Cálculo e exibição das métricas
if diffs:
    diffs = np.array(diffs)
    abs_errors = np.abs(diffs)

    mae = np.mean(abs_errors)
    mse = np.mean(diffs ** 2)
    rmse = np.sqrt(mse)
    max_ae = np.max(abs_errors)

    print(f"MAE:    {mae:.4f}")
    print(f"MSE:    {mse:.4f}")
    print(f"RMSE:   {rmse:.4f}")
    print(f"MaxAE:  {max_ae:.4f}")