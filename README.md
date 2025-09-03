# FinCov-Backend

This project is an AI-powered Voice Assistant application designed to provide natural voice-based interaction between users and a language model. The backend of this application is developed using FastAPI, with a strong focus on real-time communication, audio processing, and retrieval-augmented generation (RAG).

## 👥 Contributors:
👨‍💻 Arsh Ahmad - (Endpoints and FastAPI integration) <br>
👨‍💻 Rishabh Pawani - (Classification engine RAG and NLP) <br>
👨‍💻 Tilak Gupta - (Vector storage and Embeddings) <br>
👨‍💻 Sumit Mewada - (Speech-To-Text and Text-To-Speech) <br>


## 🛠️ Setup Instructions
### 🔧 Backend Setup
```
1. Create a virtual environment.
    python -m venv venv 
    # On Windows: .\venv\Scripts\activate
2. Create the given file structure.
3. Copy source code files according to the file structure.
4. Now install all the dependencies in terminal using
    pip install -r requirements.txt
```
### 📁 File Structure
```
FinCov-Backend
 ├── query_engine
 │      ├── docs
 │      │    ├── banking.txt
 │      │    ├── insurance.txt
 │      │    ├── investment.txt
 │      │    ├── loan.txt
 │      │    └── tax.txt
 │      ├── faiss_index
 │      │    ├── banking
 │      │    │    ├── index.faiss
 │      │    │    └── index.pkl
 │      │    ├── insurance
 │      │    │    ├── index.faiss
 │      │    │    └── index.pkl 
 │      │    ├── investment
 │      │    │    ├── index.faiss
 │      │    │    └── index.pkl
 │      │    ├── loan
 │      │    │    ├── index.faiss
 │      │    │    └── index.pkl
 │      │    └── tax
 │      │         ├── index.faiss
 │      │         └── index.pkl
 │      ├── classifier_engine.py
 │      ├── intents.json 
 │      ├── rag_pipeline.py 
 │      └── vector_indexing.py
 ├── utils
 │      ├── auth_routes.py
 │      ├── chat_storage.py
 │      ├── tts.py
 │      └── twilio_verify.py
 ├── main.py
 ├── .env
 ├── README.md
 └── requirements.txt
```

### 🔐 Update .env with your keys: 
```
# Gorq API Key
GROQ_API_KEY = "YOUR_API_KEY"

# Twilio API IDs
TWILIO_ACCOUNT_SID="YOUR_ACCOUNT_SID"
TWILIO_AUTH_TOKEN="YOUR_AUTH_TOKEN"
TWILIO_VERIFY_SID="YOUR_VERIFY_SID"

Note: You are required to create this .env file. Add your Groq API Key and Twilio Keys as mentioned above.
```
# **FinCov-Ai_modules**  
- ## Domain Classifier Engine
  #### To classify domain follow the steps :
  1. Import `classify_domain` from `query_engine.classifier_engine`.
     ```python
     from query_engine.classifier_engine import classify_domain
     ```
  2. Pass User query in the function.
     ```python
     classify_domain(querry)
     ```
- ## Intent Classifier Engine
  #### To find out the intent of query follow the steps :
  1. Import `classify_intent` from `query_engine.classifier_engine`.
     ```python
     from query_engine.classifier_engine import classify_intent
     ```
  2. Pass User query and domain to the function.
     ```python
     classify_intent(query, domain)
     ```
- ## Retrieval-Augmented Generation(RAG)
  #### For asking query using RAG follow the steps :
  1. Import `ask` and `load_all_vectorstores` from `query_engine.rag_pipeline`.
     ```python
     from query_engine.rag_pipeline import ask, load_all_vectorstores
     ```
  2. Load all vectorstores in the starting.
     ```python
     vectorstores = load_all_vectorstores()
     ```
  3. Now, pass Session ID, User query and vectorstore to the function.
     ```python
     ask(SID, query, vectorstores[domain])
     ```
     Here, `SID` is Session ID in string format.
           `query` is the user query.
           `vectorstores[domain]` is the vectorstore of particular domain.
     
     Note: Handle domain and intent correctly as they can return `None`.

- ## MongoDB utility
  #### For saving the conversation on database.
  1. Make sure that You save `MONGO_URI` in .env file.
     `MONGO_URI = "Your_URI_from_mongo_db"`
  2. Import `dump_session_to_mongo` and `store_message` from `utils.chat_storage`.
     ```python
     from utils.chat_storage import dump_session_to_mongo, store_message
     ```
  3. Use `store_message()` to store the pair of messages between the human and the bot in a temporary dictionary.
     ```python
     store_message(session_id, query, response, domain, intent)
     ```
     Pass all the parameters: session id, query, response, domain and intent.
  4. Now just pass the `SID` in `dump_session_to_mongo()`.
     ```python
     dump_session_to_mongo(SID)
     ```
