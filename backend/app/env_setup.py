import os

# Script to set up environment variables directly
# This bypasses Pydantic settings which might have issues

def setup_env():
    env_file = ".env"
    env_vars = {}
    
    # Try to read .env file
    if os.path.exists(env_file):
        print(f"Reading {env_file} file...")
        with open(env_file, "r") as f:
            for line in f:
                line = line.strip()
                if line and not line.startswith('#'):
                    key, value = line.split('=', 1)
                    value = value.strip("'\"")  # Remove quotes if present
                    env_vars[key] = value
        
        # Set environment variables
        for key, value in env_vars.items():
            if key == "OPENAI_API_KEY" and value:
                masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
                print(f"Setting {key}={masked}")
            else:
                print(f"Setting {key}={value}")
            os.environ[key] = value
        
        print(f"Loaded {len(env_vars)} variables from {env_file}")
    else:
        print(f"No {env_file} file found in {os.getcwd()}")
    
    # Print the OPENAI_API_KEY status
    if os.environ.get("OPENAI_API_KEY"):
        masked = os.environ["OPENAI_API_KEY"][:4] + "..." + os.environ["OPENAI_API_KEY"][-4:] if len(os.environ["OPENAI_API_KEY"]) > 8 else "****"
        print(f"OPENAI_API_KEY is set: {masked}")
    else:
        print("OPENAI_API_KEY is NOT set")
    
    return env_vars