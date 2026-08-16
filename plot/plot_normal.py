import json
import matplotlib.pyplot as plt
import os
import glob

folder_path = "C:/Users/arthu/Desktop/arthur/git/LSP-Modeling-and-Calibration/backend/data/"

# Busca todos os arquivos JSON dentro da pasta data
search_pattern = os.path.join(folder_path, "*_stress_profile.json")
json_files = glob.glob(search_pattern)

if not json_files:
    raise FileNotFoundError(f"Nenhum arquivo encontrado em {folder_path} com o padrão '{search_pattern}'")

# Ordena os arquivos para consistência visual
json_files.sort()

# Criação da figura com dois subplots lado a lado
fig, (ax_depth, ax_surf) = plt.subplots(1, 2, figsize=(16, 6))

# Itera sobre todos os arquivos JSON encontrados
for file_path in json_files:
    filename = os.path.basename(file_path)
    
    with open(file_path, 'r') as file:
        data = json.load(file)
    
    # Itera sobre os modelos contidos dentro do JSON
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

        # Plota os dados nos respectivos eixos usando o nome do modelo como legenda
        ax_depth.plot(depth_x, depth_y, marker='o', markersize=3, linestyle='-', label=model_name)
        ax_surf.plot(surface_x, surface_y, marker='s', markersize=3, linestyle='--', label=model_name)

# --- Finalização: Gráfico de Profundidade ---
ax_depth.axhline(0, color='black', linewidth=1, linestyle=':')
ax_depth.set_xlabel('Depth (mm)')
ax_depth.set_ylabel('Residual Stress S11 (MPa)')
ax_depth.set_title('Depth Stress Profile (All Models)')
ax_depth.grid(True, linestyle=':', alpha=0.7)
ax_depth.legend(title="Models")

# --- Finalização: Gráfico de Superfície ---
ax_surf.axhline(0, color='black', linewidth=1, linestyle=':')
ax_surf.set_xlabel('Radial Distance (mm)')
ax_surf.set_ylabel('Residual Stress S11 (MPa)')
ax_surf.set_title('Surface Stress Profile (All Models)')
ax_surf.grid(True, linestyle=':', alpha=0.7)
ax_surf.legend(title="Models")

plt.tight_layout()
plt.show()