import os
import sys

def check_required_env_vars():
    """
    Check if important environment variables are set.
    If critical variables are missing, log a warning but continue.
    """
    # Check OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        masked_key = openai_key[:4] + "..." + openai_key[-4:] if len(openai_key) > 8 else "****"
        print(f"✅ OPENAI_API_KEY is set: {masked_key}")
    else:
        print("❌ OPENAI_API_KEY is NOT set")
        
    # Check Neo4j connection info
    if os.environ.get("NEO4J_URI"):
        print(f"✅ NEO4J_URI is set")
    else:
        print(f"❌ NEO4J_URI is NOT set")
        
    if os.environ.get("NEO4J_USERNAME"):
        print(f"✅ NEO4J_USERNAME is set")
    else:
        print(f"❌ NEO4J_USERNAME is NOT set")
        
    if os.environ.get("NEO4J_PASSWORD"):
        print(f"✅ NEO4J_PASSWORD is set")
    else:
        print(f"❌ NEO4J_PASSWORD is NOT set")
    
    # No hard failures - we'll just log warnings

def check_environment():
    """
    Check if important environment variables are set.
    Returns True if all critical variables are present.
    """
    print("Checking environment variables...")
    
    # Check OpenAI API key
    openai_key = os.environ.get("OPENAI_API_KEY")
    if openai_key:
        masked_key = openai_key[:4] + "..." + openai_key[-4:] if len(openai_key) > 8 else "****"
        print(f"✅ OPENAI_API_KEY is set: {masked_key}")
    else:
        print("❌ OPENAI_API_KEY is NOT set")
        
    # Check database connection info
    db_vars = {
        "POSTGRES_SERVER": os.environ.get("POSTGRES_SERVER"),
        "POSTGRES_USER": os.environ.get("POSTGRES_USER"),
        "POSTGRES_PASSWORD": os.environ.get("POSTGRES_PASSWORD", "****"),
        "POSTGRES_DB": os.environ.get("POSTGRES_DB"),
    }
    
    for key, value in db_vars.items():
        if value:
            print(f"✅ {key} is set: {value if key != 'POSTGRES_PASSWORD' else '****'}")
        else:
            print(f"❌ {key} is NOT set")
    
    # Check Neo4j connection info
    neo4j_vars = {
        "NEO4J_URI": os.environ.get("NEO4J_URI"),
        "NEO4J_USERNAME": os.environ.get("NEO4J_USERNAME"),
        "NEO4J_PASSWORD": os.environ.get("NEO4J_PASSWORD", "****"),
    }
    
    for key, value in neo4j_vars.items():
        if value:
            print(f"✅ {key} is set: {value if key != 'NEO4J_PASSWORD' else '****'}")
        else:
            print(f"❌ {key} is NOT set")
    
    # Show all environment variables when in debug mode
    if '--debug' in sys.argv:
        print("\nAll environment variables:")
        for key, value in sorted(os.environ.items()):
            if 'password' in key.lower() or 'key' in key.lower() or 'secret' in key.lower():
                value = '****'
            print(f"{key}: {value}")
    
    # Check if critical vars are missing
    critical_vars = ["OPENAI_API_KEY", "POSTGRES_SERVER", "NEO4J_URI"]
    missing_critical = [var for var in critical_vars if not os.environ.get(var)]
    
    if missing_critical:
        print(f"\n❌ Missing critical environment variables: {', '.join(missing_critical)}")
        return False
    
    print("✅ All critical environment variables are set")
    return True

if __name__ == "__main__":
    check_environment()