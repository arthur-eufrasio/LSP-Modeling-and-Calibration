import json
import matplotlib.pyplot as plt

file_path = 'backend/data/data.json'

with open(file_path, 'r') as file:
    data = json.load(file)

depth_data = data["lspModel"]["depth"]
surface_data = data["lspModel"]["surface"]

depth_x = [point[0] for point in depth_data]
depth_y = [point[1] for point in depth_data]

surface_x = [point[0] for point in surface_data]
surface_y = [point[1] for point in surface_data]

fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(14, 6))

ax1.plot(depth_x, depth_y, marker='o', linestyle='-', color='blue', label='Depth')
ax1.axhline(0, color='black', linewidth=1)
ax1.set_xlabel('Distance (mm)')
ax1.set_ylabel('Residual Stress (MPa)')
ax1.set_title('LSP Residual Stresses - Depth')
ax1.legend()
ax1.grid(True, linestyle=':', alpha=0.7)

ax2.plot(surface_x, surface_y, marker='s', linestyle='--', color='red', label='Surface')
ax2.axhline(0, color='black', linewidth=1)
ax2.set_xlabel('Distance (mm)')
ax2.set_ylabel('Residual Stress (MPa)')
ax2.set_title('LSP Residual Stresses - Surface')
ax2.legend()
ax2.grid(True, linestyle=':', alpha=0.7)

plt.tight_layout()
plt.show()