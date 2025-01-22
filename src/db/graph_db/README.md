# Graph Database

A graph database that stores a video processed by the data pipeline. Processing of the video into the graph database is started at the end of the data pipeline. 

## Input

The script for creating the graph database receives two inputs from the data pipeline:

- The video_id is required to retrieve the transcript chunks and the frame description in the form of a CSV file.
- Meta data of the video to be saved. The meta data is used to enrich the individual nodes in the graph database with additional information. 

## Output

Nodes that represent the entities in the individual text chunks. The entities are placed in a context with meaningful relationships. In addition, all nodes contain the meta data of the processed video and the corresponding frame descriptions.

The information is added to the nodes as attributes. Each attribute saves the data in an array list. If a new video is processed and entities that have already been extracted are recognized, the information from the video is added to the existing node as a new entry in the list. The required information can then be called up via the respective index. 

The graph database is used for relationship-based cypher queries and, in addition to the vector database, provides additional information with which the answers can be enriched. 

## Core Functions

**1. utilities.py** 

Processes the two CSV files (chunks & frames) into a list of dictonaries.

**2. main.py** 

The gemini-1.5-flash large language model is used to promptly extract all entities and relationships from the transcript chunks.
A condition was added that a 50-second wait is required after every 14 requests to avoid overloading the API. 

The response from the LLM is then processed and converted into a suitable format. Nodes are now created from the extracted entities and written to the database. The nodes are then linked to the extracted relationships. In the same process, the metadata is also added as attributes to the individual nodes. 

The respective times of the frame descriptions are then compared with the timestamps of the chunks and the description is then assigned to the node with the smallest time difference. 

In addition, all nodes without relationships are deleted and no longer used. 

## Setup

Docker is required to get the database up and running. 

Configure settings in docker-compose.yaml:

```yaml
services:
  neo4j:
    image: neo4j:5.26.0
    volumes:
      - ./src/db/graph_db/logs:/logs
      - ./src/db/graph_db/config:/config
      - ./src/db/graph_db/data:/data
      - ./src/db/graph_db/plugins:/plugins
    environment:
      - NEO4J_AUTH=your_user/your_password
      - NEO4J_PLUGINS["apoc"]
    ports:
      - "7474:7474"
      - "7687:7687"
    restart: always
```

The database can be accessed via the web interface `localhost:7474`. Log in with your credentials. 

## Usage 

To store your login information securely, use the `.env` file previously created in data pre-processing.
You can now set the following parameters in the file:

`API_KEY_GOOGLE_GEMINI_GRAPHDB="your_api_key"`
`NEO4J_URI="bolt://localhost:7687"`
`NEO4J_USER="neo4j"`
`NEO4J_PASSWORD="your_password"`

You can use the same API key that you used in the data preprocessing. To improve performance, it is recommended to generate a second API key and use it specifically for the graph database requests. 
