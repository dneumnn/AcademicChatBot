# RAG (Retrieval Augmented Generation) System

A modular RAG system that supports both vector and graph-based retrieval with multiple LLM options.

## Core Functions

### [HTTP /GET] Get Available Models

Returns a list of all available LLM models from the local Ollama server and cloud providers. Use these model IDs when calling the chat function.

```python
from rag.app import models_internal

available_models = models_internal() # e.g. ["llama3.2:latest", "mistral:latest"]
```

### [HTTP /GET] Get Available Collections (Knowledge Bases)

Returns a list of all available collections for the local vector database.

```python
from rag.app import collections_internal

available_collections = collections_internal() # e.g. ["Data_Science", "fallback"]
```

### [INTERNAL] RAG Function - Direct Access to RAG Pipeline

```python
from rag.rag import rag

response = rag(
    question="What is machine learning?",
    message_history=[
        {"role": "user", "content": "Previous question"},
        {"role": "assistant", "content": "Previous answer"}
    ],
    model_id="llama3.2",
    model_parameters={
        "temperature": 0.8,
        "top_p": 0.9,
        "top_k": 40
    },
    knowledge_base="fallback",
    use_logical_routing=false,
    use_semantic_routing=false,
    stream=True,
    plaintext=False,
    mode="fast"
)
```

Parameters:

- `question`: Your query
- `model_id`: LLM model ID (e.g., "llama3.2:latest")
- `model_parameters`: Dictionary containing:
  - `temperature`: Controls randomness (0.0-1.0)
  - `top_p`: Nucleus sampling parameter (0.0-1.0)
  - `top_k`: Number of tokens to consider
- `message_history`: Optional list of previous messages for context
- `knowledge_base`: Specify knowledge base (defaults to "all")
- `use_logical_routing`: Enable rule-based routing (default: False)
- `use_semantic_routing`: Enable semantic-based routing (default: False)
- `stream`: Set wether response should be streamed (Default: true)
- `plaintext`: Set wether response should be limited to plaintext (Default: false)
- `mode`: Set the mode of the RAG module ("fast" or "smart")
- `playlist_id`: Optional YouTube playlist ID filter for context
- `video_id`: Optional YouTube video ID filter for context
- `database`: Database type to use ("vector", "graph", or "all")

### [HTTP /POST] Chat Function - High-Level Interface

```python
from rag.app import chat_internal

response = chat_internal(
    prompt="What is machine learning?"
)
```

Parameters:

- `prompt`: Your query
- `model_id`: Optional model ID (defaults to gemini-1.5-flash)
- `message_history`: Previous conversation history
- `knowledge_base`: Specific knowledge base to query (example: fallback)
- `model_parameters`: Dictionary containing:
  - `temperature`: Controls randomness (0.0-1.0)
  - `top_p`: Nucleus sampling parameter (0.0-1.0)
  - `top_k`: Number of tokens to consider
- `database`: Database type to use ("vector", "graph", or "all")
- `playlist_id`: Optional YouTube playlist ID filter for context
- `video_id`: Optional YouTube video ID filter for context
- `stream`: Set wether response should be streamed (Default: true)
- `plaintext`: Set wether response should be limited to plaintext (Default: false)
- `mode`: Set the mode of the RAG module ("fast" or "smart")
- `use_logical_routing`: Enable rule-based routing (default: False)
- `use_semantic_routing`: Enable semantic-based routing (default: False)

## Setup

1. Install dependencies:

```bash
pip install -r requirements.txt
```

2. Start Ollama server with required models

3. (Optional) Start Neo4j for graph database support:

```bash
docker compose up -d
```

4. Configure settings in config.yml:

```yaml
config:
  default_database: all
  default_model: gemini-1.5-flash
  default_model_parameters:
    temperature: 0.8
    top_p: 0.9
    top_k: 40
  default_knowledge_base: fallback
  default_mode: fast
  use_semantic_routing: false
  use_logical_routing: false
  retrieval_embedding_model: all-MiniLM-L6-v2
  reranking_cross_encoder_model: BAAI/bge-reranker-large # cross-encoder/stsb-roberta-base
  vectorstore_top_k: 40
  reranking_top_k: 10
  neo4j_fallback:
    uri: bolt://localhost:7687
    user: neo4j
    password: this_pw_is_a_test25218###1119jj
  include_image_descriptions: false
```

Key Configuration Options:

- `default_database`: Type of database to use ("vector", "graph", "all")
- `default_model`: Default LLM model ID
- `default_model_parameters`: Model inference settings
- `default_knowledge_base`: Default knowledge base to query
- `use_semantic_routing`: Whether semantic (prompt) routing should be used
- `use_logical_routing`: Whether logical (collection) routing should be used
- `retrieval_embedding_model`: Model used for text embeddings
- `reranking_cross_encoder_model`: Model used for reranking results
- `vectorstore_top_k`: Number of initial vector results to retrieve
- `reranking_top_k`: Number of results to keep after reranking
- `neo4j_fallback`: Non sensitive Neo4j connection data
- `include_image_descriptions`: Wether image descriptions of the youtube video should be considered in vector space or only the transcript

## Database Options

### Vector Store (ChromaDB)

- For general queries
- Embedded database, no setup required

### Graph Store (Neo4j)

- For relationship-based queries
- Requires Docker
- Web interface: `localhost:7474` (neo4j/password)

## Model Parameters Guide

- `temperature`:
  - 0.8: More creative responses
  - 0.2: More focused, factual responses
- `top_p`: Filter for token sampling (0.9 recommended)
- `top_k`: Number of tokens to consider (40 recommended)

Note: The system includes built-in logging (stored in `logger/logs/`) and error handling for invalid parameters, connection issues, etc.
