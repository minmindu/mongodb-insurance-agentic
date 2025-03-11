from langchain.agents import tool
from embeddings.bedrock.getters import get_embedding_model
from agent_vector_store import create_vector_store

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



tools = [fetch_guidelines]

if __name__ == "__main__":
    # Example usage
    print("Calling fetch_guidelines...")

    query = "school bus accident with passenger vehicle"
    print(fetch_guidelines(query))
