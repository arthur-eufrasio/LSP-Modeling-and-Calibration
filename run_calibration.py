from calibration.calibrator import PSOCalibrator

def main():
    print("=== Initializing Abaqus PSO Calibration ===")
    
    # Initialize and run the calibrator
    calibrator = PSOCalibrator()
    calibrator.run()

if __name__ == "__main__":
    main()