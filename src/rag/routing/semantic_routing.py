from langchain_ollama import OllamaEmbeddings
from langchain.utils.math import cosine_similarity
from langchain_core.prompts import PromptTemplate

basic_template = """
    You are an assistant for question-answering tasks. Use the following pieces of retrieved context to answer the question. If you don't know the answer, just say that you don't know. Use three sentences maximum and keep the answer concise.
    Question: {question}
    Context: {context}
    Answer:
"""

physics_template = """
You are a very smart physics professor.
You are great at answering questions about physics in a concise and easy to understand manner.
When you are not sure about the answer, you admit, that you don't know.

Here is the question:
{question}
"""

math_template = """
You are a very smart math professor.
You are great at answering questions about math in a concise and easy to understand manner.
When you are not sure about the answer, you admit, that you don't know.

Here is the question:
{question}
"""

fallback_template = """
You are a very smart professor willing to help with any question.
You are great at answering questions in a concise and easy to understand manner.
When you are not sure about the answer, you admit, that you don't know.

Here is the question:
{question}
"""

def semantic_routing(question: str) -> str:
    embeddings = OllamaEmbeddings(model="nomic-embed-text")

    prompt_templates = [physics_template, math_template, fallback_template]
    prompt_embeddings = embeddings.embed_documents(prompt_templates)
    query_embedding = embeddings.embed_query(question)

    similarity = cosine_similarity([query_embedding], prompt_embeddings)[0]
    most_similar = prompt_templates[similarity.argmax()]

    return PromptTemplate.from_template(most_similar)

def get_base_template():
    return PromptTemplate.from_template(basic_template)

def __test__semantic_routing():
    print(semantic_routing("Why does gravity exist?"))
    print(semantic_routing("How to solve a differential equation?"))
    print(semantic_routing("What is the capital of France?"))

if __name__ == "__main__":
    __test__semantic_routing()