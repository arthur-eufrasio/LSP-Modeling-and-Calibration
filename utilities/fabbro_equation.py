import math

def calculate_reduced_impedance(z_confining, z_target):
    """Calcula a impedância acústica combinada/reduzida Z."""
    return (2.0 * z_confining * z_target) / (z_confining + z_target)

def calculate_fabbro_lsp(
    energy_J=3.50,
    pulse_duration_ns=10.0,
    spot_diameter_mm=4.98,
    z_water=1.48e5,      # g/(cm^2*s) para a água
    z_aluminum=1.72e6,    # g/(cm^2*s) para alumínio aeronáutico (2024/7075)
    alpha=0.10
):
    # 1. Geometria e Irradiância
    diameter_cm = spot_diameter_mm / 10.0
    pulse_duration_s = pulse_duration_ns * 1e-9
    area_cm2 = (math.pi / 4.0) * (diameter_cm ** 2)
    
    power_density_GW_cm2 = (energy_J / pulse_duration_s) / (area_cm2 * 1e9)
    
    # 2. Impedância Reduzida
    z_reduced = calculate_reduced_impedance(z_water, z_aluminum)
    
    # 3. Equação analítica de Fabbro
    efficiency_term = math.sqrt(alpha / (2 * alpha + 3))
    p_peak_gpa = 0.01 * efficiency_term * math.sqrt(z_reduced) * math.sqrt(power_density_GW_cm2)
    
    return {
        "area_cm2": area_cm2,
        "I0_GW_cm2": power_density_GW_cm2,
        "Z_reduced": z_reduced,
        "P_peak_GPa": p_peak_gpa,
        "P_peak_MPa": p_peak_gpa * 1000.0
    }

if __name__ == "__main__":
    print("=== LSP: MODELO DE FABBRO (ÁGUA + ALUMÍNIO AERONÁUTICO) ===")
    
    # Execução para alpha = 0.10
    res_10 = calculate_fabbro_lsp(alpha=0.11)
    print(f"Impedância Reduzida (Z) : {res_10['Z_reduced']:.4e} g/(cm²·s)")
    print(f"Densidade de Potência (I0): {res_10['I0_GW_cm2']:.2f} GW/cm²")
    print(f"Pressão de Pico (α = 0.10): {res_10['P_peak_GPa']:.3f} GPa ({res_10['P_peak_MPa']:.1f} MPa)")