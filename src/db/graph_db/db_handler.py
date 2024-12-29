from neo4j import GraphDatabase
from src.db.graph_db.node_creation import create_meta_data_node
from src.db.graph_db.node_creation import create_transcript_chunk_node

class GraphHandler:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_meta_data_session(self, meta_data):
        with self.driver.session() as session:
            session.execute_write(create_meta_data_node, meta_data)

    def create_transcript_chunk_session(self, chunk):
        with self.driver.session() as session:
            session.execute_write(create_transcript_chunk_node, chunk)