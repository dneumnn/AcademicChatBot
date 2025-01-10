from neo4j import GraphDatabase

from ..constants.env import NEO4J_URI, NEO4J_USER, NEO4J_PASSWORD

graphstore = GraphDatabase.driver(NEO4J_URI, auth=(NEO4J_USER, NEO4J_PASSWORD))

def get_full_graph_information():
    with graphstore.session() as session:
        # Get all nodes and relationships
        result = session.run("""
            MATCH (n)
            OPTIONAL MATCH (n)-[r]->(m)
            RETURN collect(distinct {
                node: n,
                type: labels(n)[0],
                properties: properties(n)
            }) as nodes,
            collect(distinct {
                start: startNode(r),
                type: type(r),
                end: endNode(r),
                properties: properties(r)
            }) as relationships
        """)
        result_data = result.single()
        print("Nodes:", result_data["nodes"])
        print("Relationships:", result_data["relationships"])
        return result_data
    
if __name__ == "__main__":
    get_full_graph_information()
