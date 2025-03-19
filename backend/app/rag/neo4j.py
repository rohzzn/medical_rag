import neo4j
import os
from app.core.config import settings

def get_neo4j_driver():
    """
    Create and return a Neo4j driver instance exactly as in the Jupyter notebook.
    """
    print(f"Connecting to Neo4j at: {settings.NEO4J_URI}")
    print(f"With username: {settings.NEO4J_USERNAME}")
    print(f"Password length: {len(settings.NEO4J_PASSWORD)}")
    
    try:
        driver = neo4j.GraphDatabase.driver(
            settings.NEO4J_URI, 
            auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
        )
        print("Neo4j driver created successfully")
        return driver
    except Exception as e:
        print(f"Error creating Neo4j driver: {e}")
        return None


def close_neo4j_driver(driver):
    """Close the Neo4j driver."""
    if driver:
        try:
            driver.close()
            print("Neo4j driver closed successfully")
        except Exception as e:
            print(f"Error closing Neo4j driver: {e}")


class Neo4jManager:
    """Context manager for Neo4j connections"""
    def __init__(self):
        print("Initializing Neo4j manager")
        self.driver = get_neo4j_driver()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        close_neo4j_driver(self.driver)