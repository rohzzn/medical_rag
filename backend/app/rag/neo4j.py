import neo4j
from app.core.config import settings

def get_neo4j_driver():
    """Create and return a Neo4j driver instance."""
    driver = neo4j.GraphDatabase.driver(
        settings.NEO4J_URI, 
        auth=(settings.NEO4J_USERNAME, settings.NEO4J_PASSWORD)
    )
    return driver


def close_neo4j_driver(driver):
    """Close the Neo4j driver."""
    if driver:
        driver.close()


class Neo4jManager:
    def __init__(self):
        self.driver = get_neo4j_driver()
    
    def __enter__(self):
        return self
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        close_neo4j_driver(self.driver)