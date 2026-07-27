import csv
from pathlib import Path

import numpy as np
from scipy.interpolate import interp1d


_X_HEADERS = ("coord", "coords", "coordinate", "coordinates", "depth")
_Y_HEADERS = ("residual_stress", "rs", "stress")


def load_target_curve(csv_path):
    csv_path = Path(csv_path)

    with csv_path.open("r", newline="") as file:
        reader = csv.DictReader(file)
        if not reader.fieldnames:
            raise ValueError(f"Target curve CSV has no header: {csv_path}")

        field_lookup = {name.lower().strip(): name for name in reader.fieldnames}

        x_field = next((field_lookup[name] for name in _X_HEADERS if name in field_lookup), None)
        y_field = next((field_lookup[name] for name in _Y_HEADERS if name in field_lookup), None)

        if x_field is None or y_field is None:
            raise ValueError(
                f"Target curve CSV must contain coordinate and residual-stress columns: {csv_path}"
            )

        coords = []
        stresses = []
        for row in reader:
            if not row:
                continue
            coords.append(float(row[x_field]))
            stresses.append(float(row[y_field]))

    coords = np.asarray(coords, dtype=float)
    stresses = np.asarray(stresses, dtype=float)

    if coords.size < 2:
        raise ValueError(f"Target curve CSV needs at least two points: {csv_path}")

    order = np.argsort(coords)
    coords = coords[order]
    stresses = stresses[order]

    unique_coords, unique_indices = np.unique(coords, return_index=True)
    coords = unique_coords
    stresses = stresses[unique_indices]

    return coords, stresses


def build_target_interpolator(csv_path):
    coords, stresses = load_target_curve(csv_path)
    return interp1d(
        coords,
        stresses,
        kind="linear",
        bounds_error=False,
        fill_value=(stresses[0], stresses[-1]),
        assume_sorted=True,
    )