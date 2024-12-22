from langchain_core.prompts import PromptTemplate
from langchain_chroma import Chroma
from langchain_ollama import ChatOllama, OllamaEmbeddings
from langchain_core.output_parsers import StrOutputParser
from langchain_core.runnables import RunnablePassthrough
from rerankers.rerankers import rerank_passages_with_cross_encoder_bge
from vectorstore.vectorstore import format_docs, transform_string_list_to_string

def rag(database_path: str, collection_name: str, question: str):
    embeddings = OllamaEmbeddings(model="nomic-embed-text")
    vectorstore = Chroma(
        persist_directory=database_path,
        embedding_function=embeddings,
        collection_name=collection_name,
        collection_metadata={"hnsw:space": "cosine"}
    )
    retriever = vectorstore.as_retriever(search_type="similarity", search_kwargs={"k": 25})
 
    llm = ChatOllama(model="llama3.2")
 
    prompt = """
        You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
        Question: {question}
        Context: {context}
        Answer:
    """
 
    prompt_template = PromptTemplate.from_template(prompt)
 
    retriever_chain = (
        retriever 
        | format_docs 
        | (lambda docs: rerank_passages_with_cross_encoder_bge(question=question, passages=docs, top_k=5))
        | transform_string_list_to_string
    )
    docs = retriever_chain.invoke(question)
    print(docs)

    rag_chain = (
        {"context": retriever_chain, "question": RunnablePassthrough()}
        | prompt_template
        | llm
        | StrOutputParser()
    )
    rag_chain.get_graph().print_ascii()

    for chunk in rag_chain.stream(question):
        print(chunk, end="", flush=True)