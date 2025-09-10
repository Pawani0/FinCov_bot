from langchain_google_genai import ChatGoogleGenerativeAI
import langchain
from langchain.cache import InMemoryCache

# Enable in-memory caching for the LLM
langchain.llm_cache = InMemoryCache()
from langchain_community.vectorstores import FAISS
from langchain_huggingface import HuggingFaceEmbeddings
from langchain.chains import create_history_aware_retriever, create_retrieval_chain
from langchain.chains.combine_documents import create_stuff_documents_chain
from langchain_core.runnables.history import RunnableWithMessageHistory
from langchain_core.prompts import ChatPromptTemplate, MessagesPlaceholder
from langchain_core.chat_history import BaseChatMessageHistory
from langchain_core.messages import BaseMessage
from dotenv import load_dotenv
import os
from typing import Dict, List

# Load environment variables
load_dotenv()
GOOGLE_API_KEY = os.getenv("GOOGLE_API_KEY")

# Initialize Gemini LLM
llm = ChatGoogleGenerativeAI(
    model="gemini-2.0-flash-lite",
    temperature=0.5,
    google_api_key=GOOGLE_API_KEY
)

# Store session history per SID
session_store: Dict[str, BaseChatMessageHistory] = {}

class SlidingWindowChatMessageHistory(BaseChatMessageHistory):
    """Simple sliding window approach - keeps only recent messages"""
    
    def __init__(self, window_size: int = 16):
        self.window_size = window_size
        self._messages: List[BaseMessage] = []
    
    @property
    def messages(self) -> List[BaseMessage]:
        return self._messages
    
    def add_message(self, message: BaseMessage) -> None:
        self._messages.append(message)
        
        if len(self._messages) > self.window_size:
            self._messages = self._messages[-self.window_size:]
    
    def clear(self) -> None:
        self._messages = []

def get_session_history(session_id: str) -> BaseChatMessageHistory:
    """Get or create session memory for a given session ID"""
    if session_id not in session_store:
        session_store[session_id] = SlidingWindowChatMessageHistory(window_size=10)
    return session_store[session_id]

# Load all domain-specific FAISS vectorstores
def load_all_vectorstores():
    embeddings = HuggingFaceEmbeddings(model_name="BAAI/bge-small-en-v1.5")
    domains = ["banking", "loan", "insurance", "tax", "investment"]
    vector_stores = {}
    
    for domain in domains:
        path = f"query_engine/faiss_index/{domain}"
        try:
            vector_stores[domain] = FAISS.load_local(
                folder_path=path,
                embeddings=embeddings,
                allow_dangerous_deserialization=True
            )
            print(f"Loaded vector store for domain: {domain}")
        except Exception as e:
            print(f"Failed to load vector store for domain '{domain}': {e}")
    
    return vector_stores

# Create the conversational RAG chain
def create_conversational_rag_chain(vectorstore):
    
    # Prompt for contextualizing questions based on chat history
    contextualize_q_system_prompt = """Given a chat history and the latest user question \
    which might reference context in the chat history, formulate a standalone question \
    which can be understood without the chat history. Do NOT answer the question, \
    just reformulate it if needed and otherwise return it as it is."""
    
    contextualize_q_prompt = ChatPromptTemplate.from_messages([
        ("system", contextualize_q_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    # Create history-aware retriever
    history_aware_retriever = create_history_aware_retriever(
        llm, vectorstore.as_retriever(), contextualize_q_prompt
    )
    
    # Prompt for answering questions - FIXED: consumer_data is now a dynamic input
    qa_system_prompt = """
You are Maya, a professional female AI calling assistant for FinCove Pvt. Ltd.,
a digital banking platform. You assist users over phone calls with queries related to 
FinCove's banking products and services.

You may also receive consumer profile data. If it is provided, use it naturally 
to personalize responses. If no data is provided, simply ignore that section.

Rules:
- You may answer greetings, pleasantries, or small talk (like "hello", "how are you") briefly and politely, 
  then redirect the user back to banking topics.
- Only answer queries related to banking and financial services (tax, loan, insurance, 
  investments, general banking).
- If a query is irrelevant (not banking and not small talk), refuse politely,
  Example refusal: "Sorry, I can only assist you with banking-related queries like tax, loan, insurance, 
  investments, or general banking for FinCove."
- Never use Markdown formatting (bold, italic, code). Plain text only.
- Keep responses concise, clear, and professional.
- Use the consumer profile data to provide personalized assistance when appropriate.
- After getting response according to data dont ask for any other information.
 #REMEMBER: IF U HAVE "user_data" THEN USE IT NATURALLY TO PERSONALIZE RESPONSES. DONT SAY " I am sorry, I cannot directly show you..."
- If consumer data is provided use it solely  do not make up any other data.
Context from knowledge base:
{context}

Consumer Profile (if available):
{consumer_data}
"""
    
    qa_prompt = ChatPromptTemplate.from_messages([
        ("system", qa_system_prompt),
        MessagesPlaceholder("chat_history"),
        ("human", "{input}"),
    ])
    
    # Create question-answering chain
    question_answer_chain = create_stuff_documents_chain(llm, qa_prompt)
    
    # Create the full RAG chain
    rag_chain = create_retrieval_chain(history_aware_retriever, question_answer_chain)
    
    # Add memory to the chain
    conversational_rag_chain = RunnableWithMessageHistory(
        rag_chain,
        get_session_history,
        input_messages_key="input",
        history_messages_key="chat_history",
        output_messages_key="answer",
    )
    
    return conversational_rag_chain

# Global variable to store the chain (initialize once per vectorstore)
conversational_chains = {}

def initialize_chain(vectorstore):
    """Initialize the conversational chain once per vectorstore"""
    global conversational_chains
    vectorstore_id = id(vectorstore)  # Use vectorstore object id as key
    
    if vectorstore_id not in conversational_chains:
        conversational_chains[vectorstore_id] = create_conversational_rag_chain(vectorstore)
    
    return conversational_chains[vectorstore_id]

# Ask function using conversational RAG
def ask(SID: str, query: str, vectorstore, consumer_data: str = None):
    try:
        # Initialize the chain if not already done
        chain = initialize_chain(vectorstore)
        
        # FIXED: Pass consumer_data as part of the input
        result = chain.invoke(
            {
                "input": query, 
                "consumer_data": consumer_data or "No consumer profile data available."
            },
            config={"configurable": {"session_id": SID}}
        )

        response = result["answer"]
        
        if result and "answer" in result:
            return response
        else:
            return "I apologize, but I couldn't find an answer to your question. Please try rephrasing it."
    
    except Exception as e:
        print(f"Error in ask function: {e}")
        return "I apologize, but I encountered an error processing your request. Please try again."