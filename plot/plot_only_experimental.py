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
target_file = os.path.join(base_dir, "target_curve.csv")

if not os.path.exists(target_file):
    target_file = "C:/Users/arthu/Desktop/arthur/git/LSP-Modeling-and-Calibration/target_curve.csv"  #[cite: 6]

if not os.path.exists(target_file):
    raise FileNotFoundError(f"Arquivo target '{target_file}' não encontrado.")

# 3. Construção do gráfico
fig, ax = plt.subplots(figsize=(8.0, 4.5), dpi=300)  #[cite: 6]

# Curva Alvo Experimental com barras de intervalo horizontal e ponto médio
target_df = pd.read_csv(target_file)  #[cite: 6]
exp_depth_ends = target_df.iloc[:, 0].values.astype(float)  #[cite: 6]
exp_stresses = target_df.iloc[:, 1].values.astype(float)  #[cite: 6]
plot_x_edges = np.insert(exp_depth_ends, 0, 0.0)  #[cite: 6]

# Cálculo dos pontos médios e semilarguras dos intervalos
x_starts = plot_x_edges[:-1]  #[cite: 6]
x_ends = plot_x_edges[1:]  #[cite: 6]
x_mids = (x_starts + x_ends) / 2.0  #[cite: 6]
x_errs = (x_ends - x_starts) / 2.0  #[cite: 6]

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
    label="Experimental (Furo Cego)",  #[cite: 6]
    zorder=5,  #[cite: 6]
)

# 4. Formatação e ajustes visuais
ax.axhline(0, color="gray", linewidth=0.8, linestyle=":", zorder=1)  #[cite: 6]
ax.grid(True, linestyle="--", linewidth=0.5, alpha=0.6, zorder=0)  #[cite: 6]

# Rótulos dos eixos
ax.set_xlabel(r"Profundidade em $r = 0.75\,\mathrm{mm}$ [mm]")  #[cite: 6]
ax.set_ylabel(r"Tensão Residual $\sigma_r$ [MPa]")  #[cite: 6]

# Legenda com respiro das bordas
ax.legend(
    loc="best",
    frameon=True,
    edgecolor="black",
    facecolor="white",
    framealpha=0.9,
    fancybox=False,
    borderaxespad=1.2,  #[cite: 6]
    borderpad=0.6,  #[cite: 6]
)

os.makedirs("plot", exist_ok=True)  #[cite: 6]
plt.tight_layout()  #[cite: 6]
plt.savefig("plot/perfil_tensao_profundidade_experimental.svg", format="svg", bbox_inches="tight")
# plt.show()