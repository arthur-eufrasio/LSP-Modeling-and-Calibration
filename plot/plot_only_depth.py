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
    data_folder = "C:/Users/arthu/Desktop/arthur/git/LSP-Modeling-and-Calibration/backend/data/"  #[cite: 5]
if not os.path.exists(target_file):
    target_file = "C:/Users/arthu/Desktop/arthur/git/LSP-Modeling-and-Calibration/target_curve.csv"  #[cite: 5]

search_pattern = os.path.join(data_folder, "*_stress_profile.json")
json_files = sorted(glob.glob(search_pattern))

if not json_files:
    raise FileNotFoundError(
        f"Nenhum arquivo encontrado em {data_folder} com o padrão '{search_pattern}'"
    )

# 3. Construção do gráfico de profundidade
fig, ax = plt.subplots(figsize=(8.0, 4.5), dpi=300)

# Curva Alvo Experimental com barras de intervalo horizontal e ponto médio
if os.path.exists(target_file):
    target_df = pd.read_csv(target_file)
    exp_depth_ends = target_df.iloc[:, 0].values.astype(float)
    exp_stresses = target_df.iloc[:, 1].values.astype(float)
    plot_x_edges = np.insert(exp_depth_ends, 0, 0.0)

    # Cálculo dos pontos médios e semilarguras dos intervalos
    x_starts = plot_x_edges[:-1]
    x_ends = plot_x_edges[1:]
    x_mids = (x_starts + x_ends) / 2.0
    x_errs = (x_ends - x_starts) / 2.0

    ax.errorbar(
        x_mids,
        exp_stresses,
        xerr=x_errs,
        fmt="o",
        color="#C0392B",
        ecolor="#C0392B",
        elinewidth=1.4,
        capsize=3.5,
        capthick=1.2,
        markersize=4.5,
        markeredgecolor="black",
        markeredgewidth=0.5,
        label="Experimental (Furo Cego)",  #[cite: 5]
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

# Rótulos dos eixos
ax.set_xlabel(r"Profundidade em $r = 0.75\,\mathrm{mm}$ [mm]")
ax.set_ylabel(r"Tensão Residual $\sigma_r$ [MPa]")

# Legenda afastada das bordas dos eixos
ax.legend(
    loc="best",
    frameon=True,
    edgecolor="black",
    facecolor="white",
    framealpha=0.9,
    fancybox=False,
    borderaxespad=1.2,  # Afasta a caixa da borda/eixo do gráfico
    borderpad=0.6,  # Espaçamento interno entre texto e borda da caixa
)

os.makedirs("plot", exist_ok=True)
plt.tight_layout()
plt.savefig("plot/perfil_tensao_profundidade_lsp.svg", format="svg", bbox_inches="tight")
# plt.show()