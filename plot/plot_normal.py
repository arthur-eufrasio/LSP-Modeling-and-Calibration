import json
import os
import glob
import numpy as np
import pandas as pd
import matplotlib.pyplot as plt

# Resolução dinâmica dos caminhos (relativo à raiz do repositório ou absoluto)
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_folder = os.path.join(base_dir, "backend", "data")
target_file = os.path.join(base_dir, "target_curve.csv")

# Fallback caso os caminhos relativos não encontrem os arquivos
if not os.path.exists(data_folder):
    data_folder = "C:/Users/arthu/Desktop/arthur/git/LSP-Modeling-and-Calibration/backend/data/"
if not os.path.exists(target_file):
    target_file = "C:/Users/arthu/Desktop/arthur/git/LSP-Modeling-and-Calibration/target_curve.csv"

# Busca todos os arquivos JSON dentro da pasta data
search_pattern = os.path.join(data_folder, "*_stress_profile.json")
json_files = glob.glob(search_pattern)

if not json_files:
    raise FileNotFoundError(f"Nenhum arquivo encontrado em {data_folder} com o padrão '{search_pattern}'")

# Ordena os arquivos para consistência visual
json_files.sort()

# Criação da figura com dois subplots lado a lado
fig, (ax_depth, ax_surf) = plt.subplots(1, 2, figsize=(16, 6))

# --- 1. Plotagem da Curva Alvo Experimental (Hole Drilling em degraus) ---
if os.path.exists(target_file):
    target_df = pd.read_csv(target_file)
    exp_depth_ends = target_df.iloc[:, 0].values.astype(float)
    exp_stresses = target_df.iloc[:, 1].values.astype(float)

    # Cria as bordas dos intervalos inserindo 0.0 na primeira posição
    plot_x_edges = np.insert(exp_depth_ends, 0, 0.0)

    # Plota os degraus dos incrementos
    ax_depth.stairs(
        exp_stresses,
        plot_x_edges,
        baseline=None,
        color='black',
        linewidth=2.2,
        label="Target Experimental (Hole Drilling)",
        zorder=5
    )
else:
    print(f"[Aviso] Arquivo target '{target_file}' não encontrado.")

# --- 2. Plotagem dos Resultados de Simulação dos JSONs ---
for file_path in json_files:
    filename = os.path.basename(file_path)
    
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    for model_name, model_content in data.items():
        if "depth" not in model_content or "surface" not in model_content:
            print(f"Aviso: Dados de 'depth' ou 'surface' não encontrados para '{model_name}' em '{filename}'. Pulando.")
            continue

        depth_data = model_content["depth"]
        surface_data = model_content["surface"]

        depth_x = [point[0] for point in depth_data]
        depth_y = [point[1] for point in depth_data]

        surface_x = [point[0] for point in surface_data]
        surface_y = [point[1] for point in surface_data]

        ax_depth.plot(depth_x, depth_y, marker='o', markersize=3, linestyle='-', label=model_name)
        ax_surf.plot(surface_x, surface_y, marker='s', markersize=3, linestyle='--', label=model_name)

# --- Finalização: Gráfico de Profundidade ---
ax_depth.axhline(0, color='black', linewidth=1, linestyle=':')
ax_depth.set_xlabel('Depth (mm)')
ax_depth.set_ylabel('Residual Stress S11 (MPa)')
ax_depth.set_title('Depth Stress Profile (Simulations vs. Target)')
ax_depth.grid(True, linestyle=':', alpha=0.7)
ax_depth.legend()

# --- Finalização: Gráfico de Superfície ---
ax_surf.axhline(0, color='black', linewidth=1, linestyle=':')
ax_surf.set_xlabel('Radial Distance (mm)')
ax_surf.set_ylabel('Residual Stress S11 (MPa)')
ax_surf.set_title('Surface Stress Profile (All Models)')
ax_surf.grid(True, linestyle=':', alpha=0.7)
ax_surf.legend()

plt.tight_layout()
plt.show()