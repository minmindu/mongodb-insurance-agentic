from langchain_mongodb import MongoDBAtlasVectorSearch

from langchain_aws import BedrockEmbeddings
from embeddings.bedrock.getters import get_embedding_model

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


def create_vector_store(
    cluster_uri: str,
    database_name: str,
    collection_name: str,
    text_key: str,
    embedding_model: BedrockEmbeddings,
    index_name: str = None,
) -> MongoDBAtlasVectorSearch:
    """
    Creates a vector store using MongoDB Atlas.

    :param cluster_uri: MongoDB connection URI.
    :param database_name: Name of the database.
    :param collection_name: Name of the collection.
    :param text_key: The field containing text data.
    :param index_name: Name of the index.
    :param embedding_model: The embedding model to use.
    """

    logging.info(f"Creating vector store...")

    # Vector Store Creation
    vector_store = MongoDBAtlasVectorSearch.from_connection_string(
        connection_string=cluster_uri,
        namespace=database_name + "." + collection_name,
        embedding=embedding_model,
        index_name=index_name,
        text_key=text_key,
    )

    return vector_store


def lookup_collection(vector_store: MongoDBAtlasVectorSearch, query: str, n=2) -> str:
    result = vector_store.similarity_search_with_score(query=query, k=n)
    return str(result)


# Example usage
if __name__ == "__main__":

    embedding_model = get_embedding_model(model_id="cohere.embed-english-v3")

    INDEX_NAME = "description_index"
    

    vector_store = create_vector_store(
        cluster_uri=os.getenv("MONGODB_URI"),
        database_name=os.getenv("DATABASE_NAME"),
        collection_name=os.getenv("COLLECTION_NAME"),
        text_key="description",
        index_name=INDEX_NAME,
        embedding_model=embedding_model
    )

    
    query = "pile up collision"

    result = lookup_collection(vector_store, query=query, n=2)
    print(result)
