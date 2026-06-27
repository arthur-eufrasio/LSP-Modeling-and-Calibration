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
            "Default configuration file not found: {}".format(DEFAULT_MODEL_CONFIG_PATH)
        )

    with open(DEFAULT_MODEL_CONFIG_PATH, "r", encoding="utf-8") as file:
        config = json.load(file)

    if not config:
        raise ValueError("default_model_config.json is empty.")

    model_name = list(config.keys())[0]
    return model_name, config[model_name]


class SimulationUI(tk.Tk):
    def __init__(self):
        super(SimulationUI, self).__init__()

        self.title("LSP - Model Config and Simulation")
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

        title = ttk.Label(left_panel, text="Simulation Parameters", style="Header.TLabel")
        title.pack(anchor="w", pady=(0, 10))

        model_name_frame = ttk.LabelFrame(left_panel, text="Model Identification", padding=10)
        model_name_frame.pack(fill=tk.X, pady=(0, 8))
        ttk.Label(model_name_frame, text="Model name").grid(row=0, column=0, sticky="w", padx=(0, 10))
        ttk.Entry(model_name_frame, textvariable=self.model_name_var, width=32).grid(row=0, column=1, sticky="w")

        scroll_container = ttk.Frame(left_panel)
        scroll_container.pack(fill=tk.BOTH, expand=True)

        self.canvas = tk.Canvas(scroll_container, bg="#eef2f5", highlightthickness=0, width=300)
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

        ttk.Button(controls_frame, text="Restore Defaults", command=self._populate_fields_with_defaults).pack(side=tk.LEFT, padx=(8, 0))

        self.status_var = tk.StringVar(value="Ready")
        ttk.Label(controls_frame, textvariable=self.status_var).pack(side=tk.LEFT, padx=(12, 0))

        plot_frame = ttk.LabelFrame(right_panel, text="Results", padding=10)
        plot_frame.pack(fill=tk.BOTH, expand=True)
        self.plot_container = ttk.Frame(plot_frame)
        self.plot_container.pack(fill=tk.BOTH, expand=True)

        log_frame = ttk.LabelFrame(right_panel, text="Execution Log", padding=10)
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

    def _create_entry_row(self, parent, row_idx, key, item_dict, base_path):
        label_text = item_dict.get("labelUI", key)
        default_value = item_dict["value"]
        unit_text = item_dict.get("unit", "")

        # Map the path specifically to the "value" key
        value_path = base_path + ("value",)

        # UI Label
        ttk.Label(parent, text=label_text).grid(row=row_idx, column=0, sticky="w", padx=(0, 10), pady=3)

        # UI Input Field
        entry_text = json.dumps(default_value) if isinstance(default_value, (list, dict)) else str(default_value)
        var = tk.StringVar(value=entry_text)
        ttk.Entry(parent, textvariable=var, width=28).grid(row=row_idx, column=1, sticky="ew", pady=3)

        # UI Unit System (if provided)
        if unit_text:
            ttk.Label(parent, text=unit_text).grid(row=row_idx, column=2, sticky="w", padx=(5, 0), pady=3)

        self.field_vars[value_path] = var
        self.field_original_values[value_path] = default_value

    def _build_group_fields(self, parent, data_dict, base_path):
        row_idx = 0
        for key, item in data_dict.items():
            # Skip the metadata labels used by parent frames
            if key in ("labelUI", "unit"):
                continue

            path_tuple = base_path + (key,)

            if isinstance(item, dict):
                # If it has a "value" key, it is a data parameter (leaf node)
                if "value" in item:
                    # ONLY create a UI element if "labelUI" is present
                    if "labelUI" in item:
                        self._create_entry_row(parent, row_idx, key, item, path_tuple)
                        row_idx += 1
                    # If "labelUI" is missing, we do nothing. 
                    # It won't appear in the UI, but it will be preserved in the configuration copy.
                
                # If it doesn't have a "value" key, it's a nested subgroup
                else:
                    group_label = item.get("labelUI", key)
                    section = ttk.LabelFrame(parent, text=group_label, padding=10)
                    
                    section.grid(row=row_idx, column=0, columnspan=3, sticky="ew", pady=6)
                    section.columnconfigure(1, weight=1)
                    
                    self._build_group_fields(section, item, path_tuple)
                    row_idx += 1

    def _populate_fields_with_defaults(self):
        for child in self.form_frame.winfo_children():
            child.destroy()

        self.field_vars = {}
        self.field_original_values = {}

        self.model_name_var.set(self.default_model_name)

        # Model Builder block
        model_builder = self.default_model_config.get("modelBuilder", {})
        for group_name in ["pulse", "step", "mesh", "geometry", "material", "job"]:
            if group_name not in model_builder:
                continue
            
            group_data = model_builder[group_name]
            group_label = group_data.get("labelUI", group_name.capitalize())
            
            group = ttk.LabelFrame(self.form_frame, text=group_label, padding=10)
            group.pack(fill=tk.X, padx=4, pady=6)
            group.columnconfigure(1, weight=1)
            self._build_group_fields(group, group_data, ("modelBuilder", group_name))

        # ODB Extractor block
        odb_data = self.default_model_config.get("odbExtractor", {})
        odb_label = odb_data.get("labelUI", "Extraction Parameters")
        odb_group = ttk.LabelFrame(self.form_frame, text=odb_label, padding=10)
        odb_group.pack(fill=tk.X, padx=4, pady=6)
        odb_group.columnconfigure(1, weight=1)
        self._build_group_fields(odb_group, odb_data, ("odbExtractor",))

        self.canvas.configure(scrollregion=self.canvas.bbox("all"))
        self.status_var.set("Defaults loaded")
        self._log("Defaults parameters loaded in the interface.")

    def _parse_value(self, text_value, original_value):
        if isinstance(original_value, bool):
            normalized = text_value.strip().lower()
            if normalized in ("true", "1", "yes", "y"):
                return True
            if normalized in ("false", "0", "no", "n"):
                return False
            raise ValueError("Invalid boolean value: {}".format(text_value))

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

    def _strip_metadata(self, config_dict):
        """
        Recursively removes 'labelUI' and 'unit' from the dictionary and 
        flattens the 'value' key so the Abaqus backend receives standard parameters.
        """
        cleaned = {}
        for key, item in config_dict.items():
            if key in ("labelUI", "unit"):
                continue
            
            if isinstance(item, dict):
                if "value" in item:
                    # Flatten the dict by grabbing just the value
                    cleaned[key] = item["value"]
                else:
                    # Recursively clean sub-dictionaries
                    cleaned[key] = self._strip_metadata(item)
            else:
                cleaned[key] = item
        return cleaned

    def _build_runtime_model_config(self):
        model_name = self.model_name_var.get().strip()
        if not model_name:
            raise ValueError("Please provide a model name.")

        # Update a deep copy of the configuration structure with user inputs.
        # Hidden parameters (without labelUI) will naturally be preserved here.
        runtime_config = json.loads(json.dumps(self.default_model_config))

        for path_tuple, var in self.field_vars.items():
            raw_text = var.get().strip()
            original_value = self.field_original_values[path_tuple]
            parsed = self._parse_value(raw_text, original_value)
            self._set_nested_value(runtime_config, path_tuple, parsed)

        # Strip out UI-specific metadata before saving for the Abaqus backend
        cleaned_config = self._strip_metadata(runtime_config)

        return model_name, {model_name: cleaned_config}

    def _write_model_config(self, config_data):
        with open(MODEL_CONFIG_PATH, "w", encoding="utf-8") as file:
            json.dump(config_data, file, indent=4)

    def _on_run_clicked(self):
        try:
            model_name, config_data = self._build_runtime_model_config()
            self._write_model_config(config_data)
        except Exception as exc:
            messagebox.showerror("Validation Error", str(exc))
            return

        self.run_button.configure(state=tk.DISABLED)
        self.status_var.set("Running simulation...")
        self._log("Configuration saved to model_config.json. Starting simulation for {}...".format(model_name))

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
        self._log("Simulation and extraction completed successfully.")
        if result.stdout.strip():
            self._log("[STDOUT]\n{}".format(result.stdout.strip()))
        if result.stderr.strip():
            self._log("[STDERR]\n{}".format(result.stderr.strip()))

        try:
            self._plot_results(model_name)
            self.status_var.set("Completed")
        except Exception as exc:
            self.status_var.set("Completed with plotting error")
            self._log("Failed to plot results: {}".format(exc))
            messagebox.showwarning("Plot", "The simulation completed, but plotting failed: {}".format(exc))

        self.run_button.configure(state=tk.NORMAL)

    def _on_pipeline_error(self, exc):
        self.status_var.set("Simulation error")
        self._log("Simulation failed.")
        if exc.stdout:
            self._log("[STDOUT]\n{}".format(exc.stdout.strip()))
        if exc.stderr:
            self._log("[STDERR]\n{}".format(exc.stderr.strip()))
        messagebox.showerror("Abaqus Error", "Failed to execute Abaqus. Check the interface log.")
        self.run_button.configure(state=tk.NORMAL)

    def _on_pipeline_generic_error(self, exc):
        self.status_var.set("Error")
        self._log("Unexpected error: {}".format(exc))
        messagebox.showerror("Error", str(exc))
        self.run_button.configure(state=tk.NORMAL)

    def _plot_results(self, model_name):
        data_file = os.path.join(BACKEND_DIR, "data", "{}_stress_profile.json".format(model_name))
        if not os.path.exists(data_file):
            raise FileNotFoundError("Results file not found: {}".format(data_file))

        with open(data_file, "r") as file:
            loaded_data = json.load(file)

        if model_name not in loaded_data:
            raise KeyError("Model {} not found in results JSON.".format(model_name))

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

        self._log("Results plotted in the interface.")


def main():
    app = SimulationUI()
    app.mainloop()


if __name__ == "__main__":
    main()