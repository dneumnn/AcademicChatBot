from neo4j import GraphDatabase
from src.db.graph_db.node_creation import *
from src.db.graph_db.relation_creation import *

class GraphHandler:

    def __init__(self, uri, user, password):
        self.driver = GraphDatabase.driver(uri, auth=(user, password))

    def close(self):
        self.driver.close()

    def create_meta_data_session(self, meta_data):
        with self.driver.session() as session:
            session.execute_write(create_meta_data_node, meta_data)

    def create_transcript_chunk_session(self, chunks):
        with self.driver.session() as session:
            for chunk in chunks:
                session.execute_write(create_transcript_chunk_node, chunk)
    
    def create_chunk_next_relation_session(self, chunks):
         with self.driver.session() as session:
            for i in range(len(chunks) - 1):
                session.execute_write(
                    create_next_relationship,
                    chunks[i]['node_id'],
                    chunks[i + 1]['node_id'])
                
    def create_chunk_metadata_relation_session(self, chunks, meta_data):
        with self.driver.session() as session:
            for chunk in chunks:
                session.execute_write(
                    create_meta_data_relationship,
                    chunk['node_id'],
                    meta_data['id']
                )