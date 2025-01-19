import yaml
import os

CONFIG_PATH = os.path.join(os.path.dirname(__file__), "..", "config.yml")

with open(CONFIG_PATH, "r") as file:
    config = yaml.safe_load(file).get("config")

DEFAULT_DATABASE = config.get("default_database")
DEFAULT_MODEL = config.get("default_model")
DEFAULT_MODEL_PARAMETER_TEMPERATURE = config.get("default_model_parameters").get("temperature")
DEFAULT_MODEL_PARAMETER_TOP_P = config.get("default_model_parameters").get("top_p")
DEFAULT_MODEL_PARAMETER_TOP_K = config.get("default_model_parameters").get("top_k")
DEFAULT_KNOWLEDGE_BASE = config.get("default_knowledge_base")
USE_SEMANTIC_ROUTING = config.get("use_semantic_routing")
USE_LOGICAL_ROUTING = config.get("use_logical_routing")
RETRIEVAL_EMBEDDING_MODEL = config.get("retrieval_embedding_model")
RERANKING_CROSS_ENCODER_MODEL = config.get("reranking_cross_encoder_model")
VECTORSTORE_TOP_K = config.get("vectorstore_top_k")
RERANKING_TOP_K = config.get("reranking_top_k")
DEFAULT_MODE = config.get("default_mode")

NEO4J_FALLBACK = config.get("neo4j_fallback")
