import os
import sys

def setup_env():
    """Set up environment variables from .env file"""
    env_files = [".env", "../.env", "../../.env", "/app/.env"]
    env_vars = {}
    
    # Try to find and read an .env file
    env_file_found = False
    for env_file in env_files:
        if os.path.exists(env_file):
            print(f"Reading {env_file} file...")
            env_file_found = True
            with open(env_file, "r") as f:
                for line in f:
                    line = line.strip()
                    if line and not line.startswith('#'):
                        try:
                            key, value = line.split('=', 1)
                            key = key.strip()
                            value = value.strip().strip("'\"")  # Remove quotes if present
                            env_vars[key] = value
                        except ValueError:
                            print(f"Warning: Skipping invalid line in {env_file}: {line}")
            
            # Set environment variables
            for key, value in env_vars.items():
                if key == "OPENAI_API_KEY" and value:
                    masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
                    print(f"Setting {key}={masked}")
                else:
                    print(f"Setting {key}={value}")
                os.environ[key] = value
            
            print(f"Loaded {len(env_vars)} variables from {env_file}")
            break
    
    if not env_file_found:
        print(f"No .env file found. Searched in: {', '.join(env_files)}")
    
    # Print current working directory and all environment variables for debugging
    print(f"Current working directory: {os.getcwd()}")
    print("All environment variables:")
    for key, value in sorted(os.environ.items()):
        if any(secret in key.lower() for secret in ["key", "password", "secret", "token"]):
            masked = value[:4] + "..." + value[-4:] if len(value) > 8 else "****"
            print(f"  {key}={masked}")
        else:
            print(f"  {key}={value}")

    # Verify critical variables
    critical_vars = ["OPENAI_API_KEY", "NEO4J_URI", "NEO4J_USERNAME", "NEO4J_PASSWORD"]
    for var in critical_vars:
        if var in os.environ:
            if var == "OPENAI_API_KEY":
                masked = os.environ[var][:4] + "..." + os.environ[var][-4:] if len(os.environ[var]) > 8 else "****"
                print(f"✅ {var} is set: {masked}")
            else:
                print(f"✅ {var} is set")
        else:
            print(f"❌ {var} is NOT set")
    
    return env_vars

if __name__ == "__main__":
    setup_env()