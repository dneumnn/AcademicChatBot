import json
import logging
from langchain_core.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from langchain_openai import OpenAI, ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI

from ..routing.semantic_routing import get_base_template, semantic_routing
from ..rerankers.rerankers import rerank_passages_with_cross_encoder
from ..vectorstore.vectorstore import format_docs, retrieve_top_n_documents_chromadb, transform_string_list_to_string, \
    generate_vector_filter
from ..routing.logical_routing import route_query
from ..logger.logger import setup_logger
from ..constants.config import VECTORSTORE_TOP_K, RERANKING_TOP_K, DEFAULT_KNOWLEDGE_BASE
from ..constants.env import GEMINI_API_KEY, OPENAI_API_KEY
from ..models.model import get_local_ollama_models, get_openai_models, get_gemini_models, get_available_models
from ..graphstore.graphstore import question_to_graphdb


def contextualize_and_improve_query(question: str, llm: ChatOllama | ChatOpenAI | ChatGoogleGenerativeAI,
                                    logger: logging.Logger, message_history: list[dict] = None):
    logger.info("Improving query")
    if message_history is not None:
        logger.info("Contextualizing query with provided message history")

    contextualize_q_prompt_string = """
        You are an expert at reformulating questions to be more concise and only mention the most relevant information and adding relevant context.

        Given a optional chat history and the latest user question \
        which might reference context in the chat history, formulate a standalone question \
        which can be understood without the chat history if provided. Do NOT answer the question, \
        just reformulate it if needed and otherwise return it as is. \
        
        Also improve the standalone question as much as possible. \
        The question should be concise and only mention the most relevant information. \
        If the question is already concise and only mentions the most relevant information, \
        return it as is. Do not return a history, only a reformulated question. \
        Try to indentify what the user is trying to ask. Focus on the user messages. \
        The newly generated question should be good for a vector search and prompting GenAI.

        ==============================
        Question: {query}
        ==============================
        Chat History: {message_history}
        ==============================

        ONLY return the reformulated question, do not add any other text or explanation.
    """

    contextualize_q_prompt = PromptTemplate.from_template(contextualize_q_prompt_string)

    contextualize_q_chain = (
            {"message_history": RunnablePassthrough(), "query": RunnablePassthrough()}
            | contextualize_q_prompt
            | llm
            | StrOutputParser()
    )

    output = []
    for chunk in contextualize_q_chain.stream({"message_history": message_history, "query": question}):
        output.append(chunk)
        print(chunk, end="", flush=True)
    print()

    logger.info(f"Contextualized and improved user query: {''.join(output)}")

    return ''.join(output)


def get_vector_context(question: str, subject: str, logger: logging.Logger, mode: str, vectorstore_top_k: int = 25,
                       reranker_top_k: int = 5, filter: dict | None = None):
    vector_context = retrieve_top_n_documents_chromadb(
        question=question,
        subject=subject,
        logger=logger,
        top_k=vectorstore_top_k,
        filter=filter
    )

    if mode == "fast":
        logger.info("Returning vector context without reranking due to fast mode")
        return vector_context

    passages = [doc["document"] for doc in vector_context]

    if len(passages) == 0:
        logger.warning("No passages found in vector context")
        return []

    reranked_passages = rerank_passages_with_cross_encoder(
        question=question,
        passages=passages,
        logger=logger,
        top_k=reranker_top_k
    )

    # add metadata for reranked passage from original vector_context
    reranked_context = [next(orig_doc for orig_doc in vector_context if orig_doc["document"] == reranked_passage) for
                        reranked_passage in reranked_passages]

    return reranked_context


def rag(
        question: str,
        model_id: str,
        model_parameters: dict,
        logger: logging.Logger | None = None,
        message_history: list[dict] = None,
        use_logical_routing: bool = False,
        knowledge_base: str | None = None,
        video_id: str | None = None,
        playlist_id: str | None = None,
        use_semantic_routing: bool = False,
        plaintext: bool = False,
        database: str = "all",
        mode: str = "fast"
):
    if logger is None:
        logger = setup_logger()

    if model_id in get_local_ollama_models():
        llm = ChatOllama(
            model=model_id,
            temperature=model_parameters["temperature"],
            top_p=model_parameters["top_p"],
            top_k=model_parameters["top_k"]
        )
    elif model_id in get_openai_models():
        llm = ChatOpenAI(
            model=model_id,
            temperature=model_parameters["temperature"],
            top_p=model_parameters["top_p"],
            api_key=OPENAI_API_KEY
        )
    elif model_id in get_gemini_models():
        llm = ChatGoogleGenerativeAI(
            model=model_id,
            temperature=model_parameters["temperature"],
            top_p=model_parameters["top_p"],
            top_k=model_parameters["top_k"],
            api_key=GEMINI_API_KEY
        )
    else:
        raise ValueError(f"Invalid model ID: {model_id}. Available models: {get_available_models()}")

    if mode != "fast":
        logger.info("Improving question, since mode is not fast")
        improved_question = contextualize_and_improve_query(question, llm, logger, message_history)

    if knowledge_base is None and use_logical_routing == False:
        logger.info(
            f"Knowledge base is not provided and logical routing is not enabled. Using default knowledge base: {DEFAULT_KNOWLEDGE_BASE}")
        knowledge_base = DEFAULT_KNOWLEDGE_BASE

    logger.info(f"Starting RAG with model: {model_id}")
    logger.info(
        f"Using top_k values in retrieval: VECTORSTORE_TOP_K={VECTORSTORE_TOP_K}, RERANKER_TOP_K={RERANKING_TOP_K}")

    prompt_template = get_base_template() if not use_semantic_routing else semantic_routing(question)
    logger.info(f"Using prompt template: {prompt_template.template}, use_semantic_routing={use_semantic_routing}")

    vector_context_text = ""
    vector_context_metadata = []

    if database == "vector" or database == "all":
        subject = route_query(question, llm, logger) if (use_logical_routing and knowledge_base is None) else knowledge_base
        logger.info(f"Using subject: {subject}, use_logical_routing={use_logical_routing}")
        vector_filter = generate_vector_filter(logger, video_id, playlist_id)
        vector_context = get_vector_context(question, subject, logger, mode, VECTORSTORE_TOP_K, RERANKING_TOP_K,
                                            vector_filter)

        vector_context_text = "\n".join([doc["document"] for doc in vector_context])
        vector_context_metadata = [doc["metadata"] for doc in vector_context]

    graph_context = ""
    graph_context_metadata = []

    if database == "graph" or database == "all":
        graph_context, graph_context_metadata = question_to_graphdb(question, llm, logger, mode)

    context = f"""
        {vector_context_text}
        {graph_context}
    """

    if mode != "fast":
        question = f"""
            Original question: {question}
            Question with additional context: {improved_question}
        """

    rag_chain = (
            {"context": RunnablePassthrough(), "question": RunnablePassthrough()}
            | prompt_template
            | llm
            | StrOutputParser()
    )

    vector_sources = [f"https://youtu.be/{metadata['video_id']}?t={metadata['time']}s" for metadata in vector_context_metadata]
    graph_sources = [f"https://youtu.be/{metadata['video_id']}?t={metadata['time']}s" for metadata in graph_context_metadata]

    if plaintext:
        for chunk in rag_chain.stream({"context": context, "question": question}):
            yield chunk
    else:
        for chunk in rag_chain.stream({"context": context, "question": question}):
            yield json.dumps({"content": chunk, "sources": vector_sources + graph_sources})
