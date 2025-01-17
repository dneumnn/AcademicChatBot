from langchain_ollama import ChatOllama
from langchain_openai import ChatOpenAI
from langchain_google_genai import ChatGoogleGenerativeAI
from langchain_core.prompts import ChatPromptTemplate

from .routes import SUBJECTS, RouteQuery

def route_query(query: str, llm: ChatOllama | ChatOpenAI | ChatGoogleGenerativeAI, message_history: list[dict] = None) -> str:
    system = f"""
    You are an expert at determining the subject of a user question.
    Possible subjects are: {", ".join(SUBJECTS)}
    If you are not sure, return "other".
    Based on the conversation history and last user question, determine which subject is most relevant, return only the name of the subject.
    """

    messages = [("system", system)]
    
    if message_history:
        for msg in message_history:
            if msg != message_history[-1]:
                messages.append((msg["role"], msg["content"]))
    
    messages.append(("user", "{question}"))

    prompt = ChatPromptTemplate.from_messages(messages)

    structured_llm = llm.with_structured_output(RouteQuery)

    router = prompt | structured_llm
    try:
        result = router.invoke({"question": query})
        return result.subject
    except Exception as e:
        print("\033[93m" + str(e) + "\033[0m")
        return "other"

def __test__route_query():
    print(route_query("What element is copper?"))
    print(route_query("What is the capital?", [
        {"role": "user", "content": "Tell me about French cuisine"}, 
        {"role": "assistant", "content": "French cuisine is renowned worldwide for its sophistication and emphasis on fresh ingredients. Some famous dishes include coq au vin, beef bourguignon, and ratatouille."},
        {"role": "user", "content": "What is the capital?"}
    ]))

if __name__ == "__main__":
    __test__route_query()
