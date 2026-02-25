from calibration.calibrator import PSOCalibrator

def main():
    print("=== Initializing Abaqus PSO Calibration ===")
    calibrator = PSOCalibrator()
    calibrator.run()

if __name__ == "__main__":
    main()