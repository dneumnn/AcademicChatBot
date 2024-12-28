


# Knoten mit dynamischen Daten erstellen 
#from neo4j import GraphDatabase 
# pip install neo4j 
#from src.data_processing.data_pipeline import extract_meta_data
#Verbindung zur neo4j Datenbank erstellen 

#uri = "bolt://localhost:7474"
#user = "neo4j"
#password = "this_pw_is_a_test25218###1119jj"

#driver = GraphDatabase.driver(uri, auth=(user, password))

def create_meta_data_node(tx, meta_data):
    query = """
    CREATE (m:MetaData {
        id: $meta_id, title: $title, view_count: $view_count,
        uploader: $uploader
    })
    """
    tx.run(query, meta_id=meta_data["id"], 
           title=meta_data["title"], 
           view_count=meta_data["view_count"],  
           uploader=meta_data["uploader"]) 
    
#with driver.session() as session:
#session.execute_write(create_meta_data_node, meta_data)
          

