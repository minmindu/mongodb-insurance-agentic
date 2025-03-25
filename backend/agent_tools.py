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
    
    return str(result[0][0].page_content)
    #return str(result)

@tool
def persist_data(data):
    """Persists the data in the database."""

    # Ensure required fields are present
    # required_fields = ["accident_description", "timestamp", "final_answer"]
    # for field in required_fields:
    #     if field not in data:
    #         return f"Error: Missing required field '{field}'"

    # # Convert timestamp if necessary
    # if isinstance(data["timestamp"], str):
    #     try:
    #         data["timestamp"] = datetime.fromisoformat(data["timestamp"].replace("Z", "+00:00"))
    #     except ValueError:
    #         return "Error: Invalid timestamp format. Use ISO 8601 (e.g., '2021-07-27T22:00:00Z')"
    

    cluster_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("DATABASE_NAME")
    collection_name = os.getenv("COLLECTION_NAME_2")

    client = MongoClient(cluster_uri)
    db = client[database_name]
    collection = db[collection_name]

    collection.insert_one(data)
    return "Data persisted successfully."

tools = [fetch_guidelines, persist_data]

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
