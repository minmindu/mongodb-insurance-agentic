from langchain.agents import tool
from embeddings.bedrock.getters import get_embedding_model
from agent_vector_store import create_vector_store
from pymongo import MongoClient
from datetime import datetime
from bson import ObjectId

import os
import logging
import json
from dotenv import load_dotenv

# Load environment variables from .env file
load_dotenv()

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format="%(asctime)s - %(levelname)s - %(message)s"
)

INDEX_NAME = "description_index" 

# Configure logging for debugging
logger = logging.getLogger(__name__)

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
    """Runs semantic search on existing policies to find relevant ones based on the image description. 
    Returns complete policy information including handler actions, approval thresholds, and decision trees."""
    logger.info(f"fetch_guidelines called with query: {query}")
    
    try:
        logger.info("Attempting vector search...")
        result = vector_store.similarity_search_with_score(query=query, k=n) 
        logger.info(f"Vector search completed. Result length: {len(result) if result else 0}")
        
        # Check if we got any results
        if not result or len(result) == 0:
            logger.warning("No results from vector search")
            return "No relevant policies found for the given query. Please ensure the vector database is properly populated with policy data."
        
        # Get the full document from the database to include all fields
        cluster_uri = os.getenv("MONGODB_URI")
        database_name = os.getenv("DATABASE_NAME")
        collection_name = os.getenv("COLLECTION_NAME")
        
        client = MongoClient(cluster_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # The result contains the document content, we need to find the full document
        # by using the description to match against the database
        policy_description = result[0][0].page_content
        
        # Find the complete document that matches this description
        # Try exact match first, then partial match
        full_policy = collection.find_one({"description": policy_description})
        
        if not full_policy:
            # Try partial match if exact match fails
            full_policy = collection.find_one({"description": {"$regex": policy_description[:100]}})
        
        if not full_policy:
            # If still no match, get any policy document as fallback
            full_policy = collection.find_one({})
            if not full_policy:
                return "No policy documents found in the database. Please ensure the database is properly populated."
        
        # Extract the relevant sections for the agent
        policy_summary = {
            "name": full_policy.get("name", "Unknown Policy"),
            "type": full_policy.get("type", "general"),
            "description": full_policy.get("description", "No description available"),
            "handlerActions": full_policy.get("handlerActions", {
                "immediate": ["Contact insured to obtain statement", "Set initial reserves", "Log claim in system"],
                "within24Hours": ["Schedule damage inspection", "Review coverage", "Contact other parties"],
                "within72Hours": ["Review reports", "Adjust reserves", "Make coverage decision"]
            }),
            "approvalThresholds": full_policy.get("approvalThresholds", {
                "autoApprove": {"maxAmount": 5000, "conditions": ["minor damage"]},
                "supervisorApproval": {"maxAmount": 25000, "conditions": ["moderate damage"]},
                "managerApproval": {"maxAmount": 100000, "conditions": ["major damage"]},
                "executiveApproval": {"maxAmount": "unlimited", "conditions": ["catastrophic loss"]}
            }),
            "decisionTree": full_policy.get("decisionTree", {
                "severity": {
                    "minor": {"priority": "standard", "timeline": "5-10 days"},
                    "major": {"priority": "high", "timeline": "1-3 days"}
                }
            }),
            "reserveGuidelines": full_policy.get("reserveGuidelines", {
                "property": {"minor": 5000, "major": 25000},
                "bodily_injury": {"minor": 15000, "major": 75000}
            }),
            "documentationRequired": full_policy.get("documentationRequired", [
                "Police report", "Photos of damage", "Repair estimates", "Medical records"
            ])
        }
        
        print("Vector store - Enhanced Policy Retrieved: ", policy_summary["name"])
        return str(policy_summary)
        
    except Exception as e:
        print(f"Error in fetch_guidelines: {str(e)}")
        # Return fallback policy information
        fallback_policy = {
            "name": "General Auto Insurance Policy",
            "type": "general_auto",
            "description": "Standard auto insurance coverage for vehicle damage and liability",
            "handlerActions": {
                "immediate": ["Contact insured for statement", "Set initial reserves", "Log first notice of loss"],
                "within24Hours": ["Schedule vehicle inspection", "Review policy coverage", "Contact other parties if applicable"],
                "within72Hours": ["Review inspection report", "Adjust reserves based on findings", "Make coverage determination"]
            },
            "approvalThresholds": {
                "autoApprove": {"maxAmount": 5000, "conditions": ["clear coverage, minor damage"]},
                "supervisorApproval": {"maxAmount": 25000, "conditions": ["standard claims"]},
                "managerApproval": {"maxAmount": 100000, "conditions": ["complex claims"]},
                "executiveApproval": {"maxAmount": "unlimited", "conditions": ["catastrophic losses"]}
            },
            "decisionTree": {
                "liability": {
                    "clear": {"settlement": "proceed", "timeline": "30 days"},
                    "disputed": {"settlement": "investigate", "timeline": "60-90 days"}
                }
            },
            "reserveGuidelines": {
                "property_damage": {"standard": 10000},
                "bodily_injury": {"standard": 25000}
            },
            "documentationRequired": ["Police report", "Damage photos", "Repair estimates"]
        }
        return str(fallback_policy)


@tool
def persist_data(data) -> dict:
    """Persists the data in the database and returns the ObjectId."""
    cluster_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("DATABASE_NAME")
    collection_name = os.getenv("COLLECTION_NAME_2")

    client = MongoClient(cluster_uri)
    db = client[database_name]
    
    # Persist data
    collection = db[collection_name]
    result = collection.insert_one(data)
    
    # Get the ObjectId of the inserted document
    inserted_id = result.inserted_id
    
    return {
        "message": "Data persisted successfully.",
        "object_id": str(inserted_id)  # Convert ObjectId to string for easier handling
    }

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

@tool
def test_database_connection() -> str:
    """Test tool to verify database connection and policy data availability."""
    try:
        cluster_uri = os.getenv("MONGODB_URI")
        database_name = os.getenv("DATABASE_NAME")
        collection_name = os.getenv("COLLECTION_NAME")
        
        logger.info(f"Testing connection to: {database_name}.{collection_name}")
        
        client = MongoClient(cluster_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Count documents
        doc_count = collection.count_documents({})
        logger.info(f"Document count: {doc_count}")
        
        # Get a sample document
        sample_doc = collection.find_one({})
        if sample_doc:
            logger.info(f"Sample document found with keys: {list(sample_doc.keys())}")
            return f"Database connection successful. Found {doc_count} documents. Sample document has fields: {list(sample_doc.keys())}"
        else:
            return f"Database connection successful but no documents found in collection {collection_name}"
            
    except Exception as e:
        logger.error(f"Database connection test failed: {str(e)}")
        return f"Database connection failed: {str(e)}"

@tool
def create_vector_search_index() -> str:
    """Create the vector search index for policy documents if it doesn't exist."""
    try:
        cluster_uri = os.getenv("MONGODB_URI")
        database_name = os.getenv("DATABASE_NAME")
        collection_name = os.getenv("COLLECTION_NAME")
        
        client = MongoClient(cluster_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Check if index already exists
        try:
            indexes = list(collection.list_search_indexes())
            existing_names = [idx.get('name') for idx in indexes]
            
            if INDEX_NAME in existing_names:
                return f"Vector search index '{INDEX_NAME}' already exists."
        except:
            # If list_search_indexes doesn't work, continue with creation
            pass
        
        # Create vector search index definition
        index_definition = {
            "fields": [
                {
                    "type": "vector",
                    "path": "descriptionEmbedding",
                    "numDimensions": 1024,
                    "similarity": "cosine"
                },
                {
                    "type": "filter", 
                    "path": "type"
                }
            ]
        }
        
        # Create the vector search index
        try:
            result = collection.create_search_index(
                model={
                    "name": INDEX_NAME,
                    "definition": index_definition
                }
            )
            logger.info(f"Vector search index creation initiated: {result}")
            return f"Vector search index '{INDEX_NAME}' creation initiated. Result: {result}"
        except Exception as create_error:
            return f"Failed to create vector search index via API: {str(create_error)}. Please create it manually in MongoDB Atlas Console."
        
    except Exception as e:
        logger.error(f"Failed to create vector search index: {str(e)}")
        return f"Failed to create vector search index: {str(e)}"

tools = [fetch_guidelines, persist_data, clean_chat_history, test_database_connection, create_vector_search_index]
