import json 
import os
import time
import ast
from nltk.tokenize import sent_tokenize
from dotenv import load_dotenv
import google.generativeai as genai
from sklearn.metrics import precision_score, recall_score, f1_score

# 
requests_made = 0 
file_path = "gold_standard_entities.json"

def processing_gold_dataset(file_path):
    with open(file_path, "r", encoding='utf8') as file:
        test_data = json.load(file)

    golden_standard_entities = test_data["entities"]

    return golden_standard_entities


def llm_entities_extraction(chunks):
    global requests_made
    load_dotenv()
    API_KEY_GOOGLE_GEMINI_GRAPHDB = os.getenv("API_KEY_GOOGLE_GEMINI_GRAPHDB")
    genai.configure(api_key=API_KEY_GOOGLE_GEMINI_GRAPHDB)

    model = genai.GenerativeModel(model_name="gemini-1.5-flash", system_instruction="""
            You are an expert in Machine Learning (ML), Natural Language Processing (NLP), Artifical Intelligence and Neuronal Networks. 
            Your task is to extract entities from a given text.
    
            Entity examples:
            - ML methods, algorithms, datasets, tools, frameworks, performance metrics, general concepts
            
            Rules:
            - Format entities so they start with an uppercase. If an entity consists of more than one word write them together.
              Example: artificial intelligence = ArtificialInteligence
            
            - Do not extract entities twice. Means there should be no duplicate entities in the list. 
            - Format entities that are in plural to an entity in singular. Here are some Examples: 'SupportVectorMachines' should be 'SupportVectorMachine' or 'DecisionTrees' should be 'DecisionTree',
              'NeuralNetworks' should be 'NeuralNetwork', 'PolicyGradientMethods' should be 'PolicyGradientMethod'.
            
            Write all entities found in a list as in the following example:
            ['ArtificialIntelligence', 'Algorithm', 'Pattern', 'Data']""")
    
    llm_entities_list = []
    for chunk in chunks:
        user_prompt = f"""
            Extract all Entities from the following text:
            {chunk}
            """
        if requests_made >= 14:
            print("Rate limit reached. Sleeping for 50 seconds.")
            time.sleep(50)
            requests_made = 0
        
        llm_response = model.generate_content(contents=user_prompt)
        requests_made += 1

        try:
            llm_entities = ast.literal_eval(llm_response.text.strip())
            llm_entities_list.extend(llm_entities)
        except(ValueError, SyntaxError):
            print("Fehler beim Parsen der LLM-Antwort.")
    
    return llm_entities_list

# Function to split text into chunks using sentence boundaries
def split_text_by_sentence_splitter(chunk_size=500, chunk_overlap=50):
    with open("sample_data.txt", "r", encoding="utf-8") as file:
        text = file.read()
    
    sentences = sent_tokenize(text)  # Split text into sentences
    chunks = []
    current_chunk = ""
    
    for sentence in sentences:
        # Check if adding the next sentence exceeds the chunk size
        if len(current_chunk) + len(sentence) <= chunk_size:
            current_chunk += " " + sentence
        else:
            # Add the current chunk to the list and include overlap
            chunks.append(current_chunk.strip())
            current_chunk = " ".join(chunks[-1].split()[-chunk_overlap:]) + " " + sentence  # Add overlap
        
    # Add the final chunk
    if current_chunk:
        chunks.append(current_chunk.strip())
    
    return chunks

def metrics_calculations(golden_standard_entities, llm_entities):
    
    gold_standard_set = set(golden_standard_entities)
    llm_entities_set = set(llm_entities)

    only_gold = gold_standard_set - llm_entities_set
    only_llm = llm_entities_set - gold_standard_set

    # Universum aller Entitäten
    all_entities = list(gold_standard_set | llm_entities_set)

    print("\nNur im Gold-Standard:", only_gold)
    print("\nNur im LLM:", only_llm)
    print("\nAll entities:", all_entities)
    # Berechne die Metriken

    # Binäre Indikatoren erstellen
    gold_labels = [1 if entity in gold_standard_set else 0 for entity in all_entities]
    llm_labels = [1 if entity in llm_entities_set else 0 for entity in all_entities]

    # Berechnung der Metriken
    precision = precision_score(gold_labels, llm_labels)
    recall = recall_score(gold_labels, llm_labels)
    f1 = f1_score(gold_labels, llm_labels)

    print(f"\nPrecision: {precision:.2f}")
    print(f"Recall: {recall:.2f}")
    print(f"F1-Score: {f1:.2f}")
    
    true_positives = gold_standard_set & llm_entities_set
    false_positives = llm_entities_set - gold_standard_set
    false_negatives = gold_standard_set - llm_entities_set

    precision_m = len(true_positives) / (len(true_positives) + len(false_positives)) if llm_entities_set else 0
    recall_m = len(true_positives) / (len(true_positives) + len(false_negatives)) if gold_standard_set else 0
    f1_m = 2 * (precision * recall) / (precision + recall) if (precision + recall) else 0

    print(f"\nPrecision: {precision_m:.2f}")
    print(f"Recall: {recall_m:.2f}")
    print(f"F1-Score: {f1_m:.2f}")

if __name__ == "__main__":
    
    golden_standard_entities = processing_gold_dataset(file_path)
    print("Golden-Standard-Entities:",golden_standard_entities)
    
    chunks = ['Machine learning is a core component of artificial intelligence, where algorithms are developed to identify patterns in data and make predictions or decisions based on these patterns. The process begins with data collection, where large volumes of raw data are gathered from various sources such as databases, APIs, or sensors. Before it can be used, this data is processed in Data preparation involves several steps, including cleaning, where erroneous or irrelevant data is removed, and normalization, where values are transformed into a consistent range to improve training stability.','Another crucial step is feature engineering, where relevant properties are extracted from data to make them usable for the model. For example, in analyzing customer behavior, features like age, average order value, or purchase frequency might be extracted. The next step in machine learning is selecting an appropriate model. In supervised learning, one of the main categories of machine learning, models are trained on labeled data. This data consists of inputs and the corresponding desired outputs. An example would be predicting real estate prices, where input data such as square footage and location are used to predict the price.','Classification models such as decision trees or support vector machines are particularly suited for discrete outputs, while linear regression or neural networks are used for continuous values. A key concept in supervised learning is the cost function, which measures how well a model makes predictions. During the training process, the algorithm minimizes this cost function by adjusting the model parameters using an optimization method such as gradient descent. Gradient descent is an iterative process where parameters are adjusted in the direction of the steepest descent of the cost function until a local minimum or global minimum is reached.','Another critical aspect of machine learning is unsupervised learning, where no labels are provided, and the model must discover patterns or structures in the data. Typical tasks in this area include clustering and dimensionality reduction. Clustering algorithms like K-Means or DBSCAN group data points based on their similarity, while methods like Principal Component Analysis reduce the dimensions of a dataset to reveal hidden structures or make the data more manageable for visualization.','Reinforcement learning, another major category of machine learning, is based on a completely different approach. Here, an agent learns by interacting with an environment and receiving rewards or penalties for its actions. The goal is to develop a strategy that maximizes long-term rewards. This is often used in dynamic systems such as controlling autonomous vehicles or in games. Algorithms like Q-learning or policy gradient methods are particularly popular here.','Model validation assesses how well a model performs on unseen data. To do this, the dataset is often split into training data, validation data, and test data. Validation is used to evaluate the algorithm during training and prevent overfitting, which occurs when a model learns the training data too precisely and is no longer able to generalize to new data. Regularization techniques such as L1 norms and L2 norms or dropout in neural networks help address overfitting.','Neural networks play an outstanding role in machine learning, particularly in tasks such as image recognition and speech recognition. They consist of layers of neurons that process input data through multiple transformations. Each connection between the neurons has a weight that is adjusted during training. A neural network learns by processing inputs through forward propagation, calculating the error, and then updating the weights using backpropagation.','Modern architectures such as convolutional neural networks (CNNs) are specifically optimized for image data and use convolutional layers to recognize local features like edges or textures. For time dependent data such as speech series or time series, recurrent neural networks (RNNs) or their advancements, such as Long Short-Term Memory (LSTM) and Gated Recurrent Units (GRUs), are used. These models can process sequences by storing information from previous steps and using it in later processing stages.','Transformer models, as used in language models like GPT or BERT, enabled the efficient processing of data through mechanisms such as self-attention. In practical applications, machine learning models are often implemented using frameworks like TensorFlow, PyTorch, or scikit-learn. These libraries provide pre-built functions and modules that significantly simplify the development and training of models. After training a model, it is crucial to deploy it in a real-world environment. To do this, models are often embedded in APIs or directly integrated into applications.','Monitoring the model in operation is equally important, as data can change over time, a phenomenon known as data drift. Regular evaluations and, if necessary, retraining the model are essential to maintain accuracy and reliability. Machine learning is an iterative process that requires continuous improvement and adaptation to meet the demands of specific use cases.']
    
    #chunks = split_text_by_sentence_splitter()
    #print(chunks)
    #with open("sample_data.txt", "r", encoding="utf-8") as file:
        #chunks = file.read()
  
    
    llm_entities = llm_entities_extraction(chunks)
    print("\nLLM-extracted-Entities:", llm_entities)
    
    metrics_calculations(golden_standard_entities, llm_entities)
    