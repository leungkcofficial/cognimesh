import os
import checker

# Environment variable names and their default values
ENV_VARS = {
    'OPENAI_API_KEY': None,
    'ZOTERO_LIBRARY_ID': None,
    'ZOTERO_API_KEY': None,
    'ZOTFILE_FOLDER': 'default_zotfile_folder',
    'LOG_DIR': 'logs',
    'INPUT_DIR': 'input',
    'OUTPUT_DIR': 'output',
    'BACKUP_DIR': 'backup',
    'VECTORS_DIR': 'vectors',
    'PROMPT_DIR': 'prompt'  # The new prompt directory
}

# Path to the .env file
env_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), '.env')

try:
    # Load the existing environment variables from the .env file
    env_vars = {**ENV_VARS}  # Start with the default values
    if os.path.isfile(env_path):
        with open(env_path, 'r') as f:
            for line in f:
                if '=' in line:
                    var_name, var_value = line.strip().split('=')
                    env_vars[var_name] = var_value

    # Check each environment variable
    for var_name, default_value in ENV_VARS.items():
        var_value = env_vars.get(var_name, default_value)

        # If the variable value is not set, ask the user to input a value
        if not var_value:
            while True:
                var_value = input(f"Enter a value for {var_name} (leave blank for default): ")
                if not var_value and default_value is not None:
                    var_value = default_value  # Use the default value if the user didn't enter a value
                if var_value:  # Add any validation rules here
                    break
                else:
                    print("Invalid value. Please try again.")
            env_vars[var_name] = var_value

    # Write the updated environment variables back to the .env file
    with open(env_path, 'w') as f:
        for var_name, var_value in env_vars.items():
            f.write(f"{var_name}={var_value}\n")

    # Check if the directory variables point to existing directories, and if they don't, ask the user to input a path or create them
    for var_name in ['ZOTFILE_FOLDER', 'LOG_DIR', 'INPUT_DIR', 'OUTPUT_DIR', 'BACKUP_DIR', 'VECTORS_DIR', 'PROMPT_DIR']:  # Include the new prompt directory
        dir_path = env_vars[var_name]
        if not os.path.isdir(dir_path):
            while True:
                new_dir_path = input(f"Enter a path for {var_name} (leave blank to create in the current directory): ")
                if new_dir_path:
                    if os.path.isdir(new_dir_path):
                        dir_path = new_dir_path
                        break
                    else:
                        print("Invalid path. Please try again.")
                else:
                    dir_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), default_value)
                    os.makedirs(dir_path, exist_ok=True)
                    print(f"Created directory: {dir_path}")
                    break
            env_vars[var_name] = dir_path

    # Write the final environment variables back to the .env file
    with open(env_path, 'w') as f:
        for var_name, var_value in env_vars.items():
            f.write(f"{var_name}={var_value}\n")

except Exception as e:
    print(f"An error occurred: {e}")
    
try:
    checker.main()
except Exception as e:
    print(f"An error occurred during checking: {e}")
