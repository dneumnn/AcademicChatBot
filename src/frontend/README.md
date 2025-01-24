# Streamlit Frontend

A frontend created with streamlit. 

## Functions

The following functions are provided:

### Login

There is a basic login system where users can register with a user name and password. The user is mainly needed to save the chat history and write support requests.

### Chat

Questions on specific topics can be asked in the chat, which are then forwarded to the RAG system. YouTube links can also be inserted to expand the knowledge base from which the answers are generated.

Various settings for generating the response as well as for analyzing the YouTube videos can be adjusted under Settings.

The LLM used for the Chat Generation can be changed on the left-hand side.

### Settings

#### Settings for generating a response:

- `Message History`: Use the context of past messages for the creation
- `Database`: Choose between the Vector Database, Graph Database or use both. 
- `Randomness`: Controls the randomness of the model answer. The higher the more creative the answer will be. 
- `Nucleus Sampling`: Limits options to tokens within a cumulative probability. Higher values allow for more diverse and creative responses.
- `Token consideration`: Restricts the number of considered tokens. The more tokens are considered, the more creative the answer will be. 
-  `Youtube Playlist` : Enter a specific Youtube playlist, which is then used for the generation
- `Youtube Video_`: Enter a specific YouTube video, which is then used for the generation
- `Mode`: Set the mode of the RAG mode. Choose between fast or smart.
- `Logical Routing`: Use rule-based routing.
- `emantic Routing`: Use semantic-based routing.

#### Settings for analyzing a Youtube Video or Playlist

- `Chunk Size`: Specifies the maximum number of characters allowed in each chunk.
- `Chunk Overlap Length`: Determines how many characters overlap between consecutive chunks.
- `Seconds between frames`: Decides how many seconds should pass between the extracted and analyzed frames.
- `Embedding Model`: Choose a embedding Model. Right now only one is available. 
- `Local model`: Decides if a local model should be used, instead of using the Gemini API.
- `Detailed Chunking`: Decides if a detailed, LLM-based chunking should be used, instead of sentence-based chunking.

### Support 

If errors occur or requests want to be made, this can be done via this form. The input will be forwarded to the admin. 

### Chat History

The user's chat history can be viewed here. 

### Admin Panel

Only available for Admin to see the Support requests. 
