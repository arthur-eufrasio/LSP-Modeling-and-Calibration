import json
import os
import subprocess
import threading
import tkinter as tk
from tkinter import messagebox
from tkinter import scrolledtext
from tkinter import ttk

from matplotlib.backends.backend_tkagg import FigureCanvasTkAgg
from matplotlib.figure import Figure

from utilities.clean_files import clean_files

ABAQUS_CMD_PATH = r"C:\SIMULIA\Abaqus\Commands\abaqus.bat"

ROOT_DIR = os.path.dirname(os.path.abspath(__file__))
BACKEND_DIR = os.path.join(ROOT_DIR, "backend")
MODEL_CONFIG_DIR = os.path.join(BACKEND_DIR, "model_config")
DEFAULT_MODEL_CONFIG_PATH = os.path.join(MODEL_CONFIG_DIR, "default_model_config.json")
MODEL_CONFIG_PATH = os.path.join(MODEL_CONFIG_DIR, "model_config.json")


def load_default_model_config():
    if not os.path.exists(DEFAULT_MODEL_CONFIG_PATH):
        raise FileNotFoundError(
            "Arquivo de defaults nao encontrado: {}".format(DEFAULT_MODEL_CONFIG_PATH)
        )

    with open(DEFAULT_MODEL_CONFIG_PATH, "r") as file:
        config = json.load(file)

    if not config:
        raise ValueError("default_model_config.json esta vazio.")

    model_name = list(config.keys())[0]
    return model_name, config[model_name]


class SimulationUI(tk.Tk):
    def __init__(self):
        super(SimulationUI, self).__init__()

        self.title("LSP - Model Config e Simulacao")
        self.geometry("1400x900")
        self.configure(bg="#eef2f5")

        self.default_model_name, self.default_model_config = load_default_model_config()
        self.model_name_var = tk.StringVar(value=self.default_model_name)

        self.field_vars = {}
        self.field_original_values = {}
        self.figure_canvas = None

        self._configure_style()
        self._build_layout()
        self._populate_fields_with_defaults()

    def _configure_style(self):
        style = ttk.Style(self)
        style.theme_use("clam")
        style.configure("TFrame", background="#eef2f5")
        style.configure("TLabel", background="#eef2f5", font=("Segoe UI", 10))
        style.configure("Header.TLabel", background="#eef2f5", font=("Segoe UI", 15, "bold"))
        style.configure("TLabelframe", background="#f8fbfd", borderwidth=1)
        style.configure("TLabelframe.Label", background="#f8fbfd", foreground="#123044", font=("Segoe UI", 11, "bold"))
        style.configure("TButton", font=("Segoe UI", 10, "bold"), padding=6)

    def _build_layout(self):
        root_container = ttk.Frame(self)
        root_container.pack(fill=tk.BOTH, expand=True, padx=14, pady=14)

        left_panel = ttk.Frame(root_container)
        left_panel.pack(side=tk.LEFT, fill=tk.BOTH, expand=False)

        right_panel = ttk.Frame(root_container)
        right_panel.pack(side=tk.RIGHT, fill=tk.BOTH, expand=True, padx=(12, 0))

        title = ttk.Label(left_panel, text="Parametros da Simulacao", style="Header.TLabel")
        title.pack(anchor="w", pady=(0, 10))

        model_name_frame = ttk.LabelFrame(left_panel, text="Identificacao do Modelo", padding=10)
        model_name_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(model_name_frame, text="Nome do modelo").grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Entry(model_name_frame, textvariable=self.model_name_var, width=32).grid(row=0, column=1, sticky="w")

        scroll_container = ttk.Frame(left_panel)
        scroll_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(scroll_container, bg="#eef2f5", highlightthickness=0, width=590)
        self.canvas.pack(side=tk.LEFT, fill=tk.BOTH, expand=True)

        scrollbar = ttk.Scrollbar(scroll_container, orient="vertical", command=self.canvas.yview)
        scrollbar.pack(side=tk.RIGHT, fill=tk.Y)

        self.canvas.configure(yscrollcommand=scrollbar.set)
        self.form_frame = ttk.Frame(self.canvas)
        self.canvas_window = self.canvas.create_window((0, 0), window=self.form_frame, anchor="nw")

        self.form_frame.bind("<Configure>", self._on_form_configure)
        self.canvas.bind("<Configure>", self._on_canvas_configure)

        controls_frame = ttk.Frame(left_panel)
        controls_frame.pack(fill=tk.X, pady=(8, 0))

        self.run_button = ttk.Button(controls_frame, text="Run Simulation", command=self._on_run_clicked)
        self.run_button.pack(side=tk.LEFT)

        ttk.Button(controls_frame, text="Restaurar Defaults", command=self._populate_fields_with_defaults).pack(side=tk.LEFT, padx=(8, 0))

        self.status_var = tk.StringVar(value="Pronto")
        ttk.Label(controls_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=(12, 0))

        plot_frame = ttk.LabelFrame(right_panel, text="Resultados", padding=10)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        self.plot_container = ttk.Frame(plot_frame)
        self.plot_container.pack(fill=tk.BOTH, expand=True)

        log_frame = ttk.LabelFrame(right_panel, text="Log da Execucao", padding=10)
        log_frame.pack(fill=tk.BOTH, expand=False, pady=(10, 0))

        self.log_widget = scrolledtext.ScrolledText(log_frame, height=12, wrap=tk.WORD, font=("Consolas", 9))
        self.log_widget.pack(fill=tk.BOTH, expand=True)
        self.log_widget.configure(state=tk.DISABLED)

    def _on_form_configure(self, _event):
        self.canvas.configure(scrollregion=self.canvas.bbox("all"))

    def _on_canvas_configure(self, event):
        self.canvas.itemconfigure(self.canvas_window, width=event.width)

    def _log(self, message):
        self.log_widget.configure(state=tk.NORMAL)
        self.log_widget.insert(tk.END, message + "\n")
        self.log_widget.see(tk.END)
        self.log_widget.configure(state=tk.DISABLED)

    def _create_entry_row(self, parent, row_idx, label_text, path_tuple, default_value):
        ttk.Label(parent, text=label_text).grid(row=row_idx, column=0, sticky="w", padx=(0, 10), pady=3)

        entry_text = json.dumps(default_value) if isinstance(default_value, (list, dict)) else str(default_value)
        var = tk.StringVar(value=entry_text)
        ttk.Entry(parent, textvariable=var, width=36).grid(row=row_idx, column=1, sticky="ew", pady=3)

        self.field_vars[path_tuple] = var
        self.field_original_values[path_tuple] = default_value

    def _build_group_fields(self, parent, data_dict, base_path):
        row_idx = 0
        for key, value in data_dict.items():
            path_tuple = base_path + (key,)
            if isinstance(value, dict):
                section = ttk.LabelFrame(parent, text=key, padding=10)
                section.grid(row=row_idx, column=0, columnspan=2, sticky="ew", pady=6)
                section.columnconfigure(1, weight=1)
                self._build_group_fields(section, value, path_tuple)
            else:
                self._create_entry_row(parent, row_idx, key, path_tuple, value)
            row_idx += 1

    def _populate_fields_with_defaults(self):
        for child in self.form_frame.winfo_children():
            child.destroy()

        self.field_vars = {}
        self.field_original_values = {}

        self.model_name_var.set(self.default_model_name)

        odb_group = ttk.LabelFrame(self.form_frame, text="Extractor", padding=10)
        odb_group.pack(fill=tk.X, padx=4, pady=6)
        odb_group.columnconfigure(1, weight=1)
        self._build_group_fields(odb_group, self.default_model_config["odbExtractor"], ("odbExtractor",))

        model_builder = self.default_model_config["modelBuilder"]
        for group_name in ["pulse", "step", "mesh", "geometry", "material", "job"]:
            if group_name not in model_builder:
                continue
            group = ttk.LabelFrame(self.form_frame, text=group_name, padding=10)
            group.pack(fill=tk.X, padx=4, pady=6)
            group.columnconfigure(1, weight=1)
            self._build_group_fields(group, model_builder[group_name], ("modelBuilder", group_name))

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.status_var.set("Defaults carregados")
        self._log("Defaults recarregados na interface.")

    def _parse_value(self, text_value, original_value):
        if isinstance(original_value, bool):
            normalized = text_value.strip().lower()
            if normalized in ("true", "1", "yes", "y"):
                return True
            if normalized in ("false", "0", "no", "n"):
                return False
            raise ValueError("Valor booleano invalido: {}".format(text_value))

        if isinstance(original_value, int) and not isinstance(original_value, bool):
            return int(float(text_value))

        if isinstance(original_value, float):
            return float(text_value)

        if isinstance(original_value, (list, dict)):
            return json.loads(text_value)

        if original_value is None:
            if text_value.strip().lower() == "null":
                return None
            return text_value

        return text_value

    def _set_nested_value(self, target, path, value):
        ref = target
        for key in path[:-1]:
            ref = ref[key]
        ref[path[-1]] = value

    def _build_runtime_model_config(self):
        model_name = self.model_name_var.get().strip()
        if not model_name:
            raise ValueError("Informe um nome de modelo.")

        runtime_config = json.loads(json.dumps(self.default_model_config))

        for path_tuple, var in self.field_vars.items():
            raw_text = var.get().strip()
            original_value = self.field_original_values[path_tuple]
            parsed = self._parse_value(raw_text, original_value)
            self._set_nested_value(runtime_config, path_tuple, parsed)

        return model_name, {model_name: runtime_config}

    def _write_model_config(self, config_data):
        with open(MODEL_CONFIG_PATH, "w") as file:
            json.dump(config_data, file, indent=4)

    def _on_run_clicked(self):
        try:
            model_name, config_data = self._build_runtime_model_config()
            self._write_model_config(config_data)
        except Exception as exc:
            messagebox.showerror("Erro de validacao", str(exc))
            return

        self.run_button.configure(state=tk.DISABLED)
        self.status_var.set("Executando simulacao...")
        self._log("Config salvo em model_config.json. Iniciando simulacao para {}...".format(model_name))

        worker = threading.Thread(target=self._run_pipeline_worker, args=(model_name,), daemon=True)
        worker.start()

    def _run_pipeline_worker(self, model_name):
        os.environ["BACKEND_PROJECT_PATH"] = BACKEND_DIR
        abaqus_command = '"{}" cae noGUI="backend/command.py"'.format(ABAQUS_CMD_PATH)
        
        try:
            result = subprocess.run(
                abaqus_command,
                shell=True,
                check=True,
                cwd=ROOT_DIR,
                capture_output=True,
                text=True,
            )

            clean_files()
            self.after(0, self._on_pipeline_success, model_name, result)
        except subprocess.CalledProcessError as exc:
            self.after(0, self._on_pipeline_error, exc)
        except Exception as exc:
            self.after(0, self._on_pipeline_generic_error, exc)

    def _on_pipeline_success(self, model_name, result):
        self._log("Simulacao e extracao finalizadas com sucesso.")
        if result.stdout.strip():
            self._log("[STDOUT]\n{}".format(result.stdout.strip()))
        if result.stderr.strip():
            self._log("[STDERR]\n{}".format(result.stderr.strip()))

        try:
            self._plot_results(model_name)
            self.status_var.set("Concluido")
        except Exception as exc:
            self.status_var.set("Concluido com erro de plot")
            self._log("Falha ao plotar resultados: {}".format(exc))
            messagebox.showwarning("Plot", "A simulacao concluiu, mas o plot falhou: {}".format(exc))

        self.run_button.configure(state=tk.NORMAL)

    def _on_pipeline_error(self, exc):
        self.status_var.set("Erro na simulacao")
        self._log("Simulacao falhou.")
        if exc.stdout:
            self._log("[STDOUT]\n{}".format(exc.stdout.strip()))
        if exc.stderr:
            self._log("[STDERR]\n{}".format(exc.stderr.strip()))
        messagebox.showerror("Erro Abaqus", "Falha ao executar Abaqus. Veja o log da interface.")
        self.run_button.configure(state=tk.NORMAL)

    def _on_pipeline_generic_error(self, exc):
        self.status_var.set("Erro")
        self._log("Erro inesperado: {}".format(exc))
        messagebox.showerror("Erro", str(exc))
        self.run_button.configure(state=tk.NORMAL)

    def _plot_results(self, model_name):
        data_file = os.path.join(BACKEND_DIR, "data", "{}_stress_profile.json".format(model_name))
        if not os.path.exists(data_file):
            raise FileNotFoundError("Arquivo de resultados nao encontrado: {}".format(data_file))

        with open(data_file, "r") as file:
            loaded_data = json.load(file)

        if model_name not in loaded_data:
            raise KeyError("Modelo {} nao encontrado no JSON de resultados.".format(model_name))

        model_data = loaded_data[model_name]
        depth_data = model_data["depth"]
        surface_data = model_data["surface"]

        depth_x = [point[0] for point in depth_data]
        depth_y = [point[1] for point in depth_data]
        surface_x = [point[0] for point in surface_data]
        surface_y = [point[1] for point in surface_data]

        fig = Figure(figsize=(9.0, 4.6), dpi=100)
        ax_depth = fig.add_subplot(1, 2, 1)
        ax_surface = fig.add_subplot(1, 2, 2)

        ax_depth.plot(depth_x, depth_y, marker="o", linestyle="-", color="#1d4e89", markersize=4)
        ax_depth.axhline(0, color="#222", linewidth=1)
        ax_depth.set_title("Depth")
        ax_depth.set_xlabel("Distance (mm)")
        ax_depth.set_ylabel("Residual Stress (MPa)")
        ax_depth.grid(True, linestyle=":", alpha=0.7)

        ax_surface.plot(surface_x, surface_y, marker="s", linestyle="--", color="#bd5d38", markersize=4)
        ax_surface.axhline(0, color="#222", linewidth=1)
        ax_surface.set_title("Surface")
        ax_surface.set_xlabel("Distance (mm)")
        ax_surface.set_ylabel("Residual Stress (MPa)")
        ax_surface.grid(True, linestyle=":", alpha=0.7)

        fig.tight_layout()

        if self.figure_canvas is not None:
            self.figure_canvas.get_tk_widget().destroy()

        self.figure_canvas = FigureCanvasTkAgg(fig, master=self.plot_container)
        self.figure_canvas.draw()
        self.figure_canvas.get_tk_widget().pack(fill=tk.BOTH, expand=True)

        self._log("Resultados plotados na interface.")


def main():
    app = SimulationUI()
    app.mainloop()


if __name__ == "__main__":
    main()

