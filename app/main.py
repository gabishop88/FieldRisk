#project_path = "/content/drive/My Drive/AgDataNinjas/SCE_Files"

# When analysis starts: 

# Get Inputs

# Get Weather Data from API

# Make Predictions 

# Create MET Files

# Run Simulations
import subprocess

result = subprocess.run(['Rscript', os.path.join(project_path, 'simulation_script.R')],
                        capture_output=True, text=True)

print(result.stdout)
if result.stderr:
    print("Errors:", result.stderr)

# Get Outputs