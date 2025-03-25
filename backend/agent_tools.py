from langchain.agents import tool
from embeddings.bedrock.getters import get_embedding_model
from agent_vector_store import create_vector_store
from pymongo import MongoClient
from datetime import datetime

import os
import logging
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

INDEX_NAME = "description_index" 

embedding_model = get_embedding_model(model_id="cohere.embed-english-v3")

vector_store = create_vector_store(
        cluster_uri=os.getenv("MONGODB_URI"),
        database_name=os.getenv("DATABASE_NAME"),
        collection_name=os.getenv("COLLECTION_NAME"),                       
        text_key="description",
        embedding_key="descriptionEmbedding",
        index_name=INDEX_NAME,
        embedding_model=embedding_model
    )

@tool
def fetch_guidelines(query: str, n=1) -> str:
    """Runs semantic search on existing policies to find relevant ones based on the image description."""
    result = vector_store.similarity_search_with_score(query=query, k=n) 
    print("Vector store - Similarity Search Raw: ", result)
    print("Vector store - Similarity Search Partial: ", str(result[0][0].page_content))
    return str(result[0][0].page_content)

@tool
def persist_data(data) -> dict:
    """Persists the data in the database."""
    cluster_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("DATABASE_NAME")
    collection_name = os.getenv("COLLECTION_NAME_2")

    client = MongoClient(cluster_uri)
    db = client[database_name]
    
    # Persist data
    collection = db[collection_name]
    collection.insert_one(data)

    return {"message": "Data persisted successfully."}

@tool
def clean_chat_history() -> dict:
    """Cleans the chat history in the database at the end of the workflow."""
    cluster_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("DATABASE_NAME")
    chat_history_coll = os.getenv("CHAT_HISTORY_COLLECTION")

    client = MongoClient(cluster_uri)
    db = client[database_name]
    
    # Persist data
    collection = db[chat_history_coll]
    collection.delete_many({})

    return {"message": "Chat history cleaned successfully."}

tools = [fetch_guidelines, persist_data, clean_chat_history]

if __name__ == "__main__":
    # Example usage
    #print("Calling fetch_guidelines...")

    #query = "school bus accident with passenger vehicle"
    #print(fetch_guidelines(query))
    data = {"accident_description": "school bus accident with passenger vehicle",
             "timestamp": "2021-07-27T22:00:00Z",
             "final_answer": "Policy 1"
           }
    
    persist_data(data)
    print("Done.")
