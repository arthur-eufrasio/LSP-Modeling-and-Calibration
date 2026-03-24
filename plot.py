import json
import matplotlib.pyplot as plt
import os
import glob

# Define the folder path instead of a specific file
folder_path = "C:/Users/arthu/Desktop/arthur/git/LSP-Modeling-and-Calibration/backend/data/"

# Create the two figures and their axes BEFORE looping
fig_depth, ax_depth = plt.subplots(figsize=(14, 10))
fig_surf, ax_surf = plt.subplots(figsize=(14, 10))

# Find all JSON files in the directory
# This assumes your files end with '_model_stress_profile.json'
search_pattern = os.path.join(folder_path, "*_model_stress_profile.json")
json_files = glob.glob(search_pattern)

# Sort the files so they plot (and appear in the legend) in numerical order
json_files.sort()

# Loop through every found JSON file
for file_path in json_files:
    # Extract filename, model name, and element size
    filename = os.path.basename(file_path)
    prefix = filename.split('_')[0]
    model_name = prefix + '_model'
    ele_size = int(prefix)
    
    # Load JSON data
    with open(file_path, 'r') as file:
        data = json.load(file)
        
    # Skip if the model name isn't in the JSON (safety check)
    if model_name not in data:
        print(f"Warning: {model_name} not found in {filename}. Skipping.")
        continue

    depth_data = data[model_name]["depth"]
    surface_data = data[model_name]["surface"]

    depth_x = [point[0] for point in depth_data]
    depth_y = [point[1] for point in depth_data]

    surface_x = [point[0] for point in surface_data]
    surface_y = [point[1] for point in surface_data]

    # Plot on Depth Figure (letting Matplotlib auto-assign colors)
    ax_depth.plot(depth_x, depth_y, markersize=4, marker='o', linestyle='-', label=f'{ele_size} µm')

    # Plot on Surface Figure (letting Matplotlib auto-assign colors)
    ax_surf.plot(surface_x, surface_y, markersize=4, marker='s', linestyle='--', label=f'{ele_size} µm')

# --- Finalize Figure 1: Depth ---
ax_depth.axhline(0, color='black', linewidth=1)
ax_depth.set_xlabel('Distance (mm)')
ax_depth.set_ylabel('Residual Stress (MPa)')
ax_depth.set_title('LSP Residual Stresses - Depth')
ax_depth.legend(title="Element Size")
ax_depth.grid(True, linestyle=':', alpha=0.7)

# --- Finalize Figure 2: Surface ---
ax_surf.axhline(0, color='black', linewidth=1)
ax_surf.set_xlabel('Distance (mm)')
ax_surf.set_ylabel('Residual Stress (MPa)')
ax_surf.set_title('LSP Residual Stresses - Surface')
ax_surf.legend(title="Element Size")
ax_surf.grid(True, linestyle=':', alpha=0.7)

# Display both populated windows simultaneously
plt.show()