import glob
import json
import os
import matplotlib.pyplot as plt
import numpy as np
import pandas as pd

# 1. Configurações visuais e tipográficas (padrão publicação)
plt.rcParams.update(
    {
        "font.family": "serif",
        "font.serif": ["Times New Roman", "DejaVu Serif", "Liberation Serif"],
        "font.size": 10,
        "axes.labelsize": 11,
        "axes.titlesize": 11,
        "xtick.labelsize": 9.5,
        "ytick.labelsize": 9.5,
        "legend.fontsize": 8.5,
        "figure.titlesize": 12,
        "svg.fonttype": "none",
        "mathtext.fontset": "stix",
    }
)

# 2. Resolução dinâmica dos caminhos
base_dir = os.path.dirname(os.path.dirname(os.path.abspath(__file__)))
data_folder = os.path.join(base_dir, "backend", "data")
target_file = os.path.join(base_dir, "target_curve.csv")

if not os.path.exists(data_folder):
    data_folder = "C:/Users/arthu/Desktop/arthur/git/LSP-Modeling-and-Calibration/backend/data/"
if not os.path.exists(target_file):
    target_file = "C:/Users/arthu/Desktop/arthur/git/LSP-Modeling-and-Calibration/target_curve.csv"

search_pattern = os.path.join(data_folder, "*_stress_profile.json")
json_files = sorted(glob.glob(search_pattern))

if not json_files:
    raise FileNotFoundError(
        f"Nenhum arquivo encontrado em {data_folder} com o padrão '{search_pattern}'"
    )

# 3. Construção do gráfico de profundidade
fig, ax = plt.subplots(figsize=(8.0, 4.5), dpi=300)

# Curva Alvo Experimental (Hole Drilling)
if os.path.exists(target_file):
    target_df = pd.read_csv(target_file)
    exp_depth_ends = target_df.iloc[:, 0].values.astype(float)
    exp_stresses = target_df.iloc[:, 1].values.astype(float)
    plot_x_edges = np.insert(exp_depth_ends, 0, 0.0)

    ax.stairs(
        exp_stresses,
        plot_x_edges,
        baseline=None,
        color="#111111",
        linewidth=2.0,
        label="Experimental",
        zorder=5,
    )
else:
    print(f"[Aviso] Arquivo target '{target_file}' não encontrado.")

# Simulações dos arquivos JSON
for file_path in json_files:
    filename = os.path.basename(file_path)

    with open(file_path, "r", encoding="utf-8") as file:
        data = json.load(file)

    for model_name, model_content in data.items():
        if "depth" not in model_content:
            continue

        depth_data = np.array(model_content["depth"])

        # Prioriza o campo 'legend' se existir; caso contrário, usa a chave do modelo
        label_name = model_content.get("legend", model_name)

        ax.plot(
            depth_data[:, 0],
            depth_data[:, 1],
            marker="o",
            markersize=3.5,
            markeredgewidth=0.4,
            markeredgecolor="black",
            linewidth=1.4,
            label=label_name,
            zorder=3,
        )

# 4. Formatação e ajustes finais
ax.axhline(0, color="gray", linewidth=0.8, linestyle=":", zorder=1)
ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6, zorder=0)

ax.set_xlabel("Profundidade $z$ [mm]")
ax.set_ylabel("Tensão Residual $S_{11}$ [MPa]")
ax.set_title("Perfil de Tensão Residual em Profundidade")
ax.legend(frameon=True, edgecolor="none", facecolor="white", framealpha=0.8)

plt.tight_layout()
plt.savefig("plot/perfil_tensao_profundidade_lsp.svg", format="svg", bbox_inches="tight")
# plt.show()