#!/usr/bin/env python3
"""
Debug script to test MongoDB vector search directly
"""

import os
import sys
import json

# Load environment variables manually from .env file
def load_env_vars():
    env_vars = {}
    # Get the project root directory (two levels up from this test script)
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    env_path = os.path.join(project_root, "backend", ".env")
    
    try:
        with open(env_path, 'r') as f:
            for line in f:
                if line.strip() and not line.startswith('#') and '=' in line:
                    key, value = line.strip().split('=', 1)
                    env_vars[key] = value
                    os.environ[key] = value  # Set in environment
        print("✅ Loaded environment variables from .env file")
        return env_vars
    except Exception as e:
        print(f"❌ Failed to load .env file: {e}")
        return {}

# Load environment variables first
env_vars = load_env_vars()

# Add backend directory to Python path (relative to project root)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
backend_path = os.path.join(project_root, "backend")
sys.path.append(backend_path)

# Now try to import the modules (if available)
try:
    from pymongo import MongoClient
    PYMONGO_AVAILABLE = True
    print("✅ pymongo available")
except ImportError:
    PYMONGO_AVAILABLE = False
    print("❌ pymongo not available")

try:
    from embeddings.bedrock.getters import get_embedding_model
    from agent_vector_store import create_vector_store
    BEDROCK_AVAILABLE = True
    print("✅ Bedrock modules available")
except ImportError as e:
    BEDROCK_AVAILABLE = False
    print(f"❌ Bedrock modules not available: {e}")

def test_mongodb_connection():
    """Test basic MongoDB connection and data"""
    if not PYMONGO_AVAILABLE:
        print("❌ Cannot test MongoDB connection - pymongo not available")
        return False
        
    cluster_uri = env_vars.get("MONGODB_URI")
    database_name = env_vars.get("DATABASE_NAME") 
    collection_name = env_vars.get("COLLECTION_NAME")
    
    print(f"Connecting to MongoDB...")
    print(f"Database: {database_name}")
    print(f"Collection: {collection_name}")
    
    try:
        client = MongoClient(cluster_uri)
        db = client[database_name]
        collection = db[collection_name]
        
        # Count total documents
        total_docs = collection.count_documents({})
        print(f"Total documents in collection: {total_docs}")
        
        # Check if documents have the required fields
        docs_with_description = collection.count_documents({"description": {"$exists": True}})
        docs_with_embedding = collection.count_documents({"descriptionEmbedding": {"$exists": True}})
        
        print(f"Documents with 'description' field: {docs_with_description}")
        print(f"Documents with 'descriptionEmbedding' field: {docs_with_embedding}")
        
        # Get sample document
        sample_doc = collection.find_one({})
        if sample_doc:
            print(f"Sample document fields: {list(sample_doc.keys())}")
            if 'description' in sample_doc:
                print(f"Sample description: {sample_doc['description'][:100]}...")
            if 'descriptionEmbedding' in sample_doc:
                print(f"Sample embedding length: {len(sample_doc['descriptionEmbedding'])}")
        
        return total_docs > 0
    except Exception as e:
        print(f"❌ MongoDB connection failed: {e}")
        return False

def test_vector_search():
    """Test vector search functionality"""
    print(f"\n--- Testing Vector Search ---")
    
    if not BEDROCK_AVAILABLE:
        print("❌ Cannot test vector search - Bedrock modules not available")
        return False
    
    try:
        # Get embedding model
        embedding_model = get_embedding_model(model_id="cohere.embed-english-v3")
        print("✅ Embedding model loaded successfully")
        
        # Create vector store
        cluster_uri = env_vars.get("MONGODB_URI")
        database_name = env_vars.get("DATABASE_NAME")
        collection_name = env_vars.get("COLLECTION_NAME")
        
        vector_store = create_vector_store(
            cluster_uri=cluster_uri,
            database_name=database_name,
            collection_name=collection_name,
            text_key="description",
            embedding_key="descriptionEmbedding",
            embedding_model=embedding_model,
            index_name="description_index"
        )
        print("✅ Vector store created successfully")
        
        # List available methods
        print(f"Available vector store methods:")
        methods = [method for method in dir(vector_store) if not method.startswith('_') and 'search' in method.lower()]
        for method in methods:
            print(f"  - {method}")
        
        # Test search queries
        test_queries = [
            "school bus accident",
            "winter weather driving",
            "collision",
            "vehicle damage"
        ]
        
        for query in test_queries:
            print(f"\nTesting query: '{query}'")
            try:
                # Try different search methods to see which one works
                print("  Trying similarity_search_with_score...")
                try:
                    results = vector_store.similarity_search_with_score(query=query, k=2)
                    print(f"  ✅ similarity_search_with_score: {len(results)} results")
                except AttributeError as e:
                    print(f"  ❌ similarity_search_with_score not available: {e}")
                    results = None
                
                if not results:
                    print("  Trying similarity_search...")
                    try:
                        results = vector_store.similarity_search(query=query, k=2)
                        print(f"  ✅ similarity_search: {len(results)} results")
                        # Convert to score format for consistency
                        results = [(doc, 1.0) for doc in results]
                    except Exception as e:
                        print(f"  ❌ similarity_search failed: {e}")
                        results = None
                
                if not results:
                    print("  Trying similarity_search_with_relevance_scores...")
                    try:
                        results = vector_store.similarity_search_with_relevance_scores(query=query, k=2)
                        print(f"  ✅ similarity_search_with_relevance_scores: {len(results)} results")
                    except Exception as e:
                        print(f"  ❌ similarity_search_with_relevance_scores failed: {e}")
                        results = None
                
                if results:
                    for i, (doc, score) in enumerate(results):
                        print(f"  Result {i+1}: Score={score:.4f}")
                        print(f"    Content: {doc.page_content[:150]}...")
                else:
                    print("  ❌ No results found with any method")
                    
            except Exception as e:
                print(f"  ❌ Error in search: {str(e)}")
        
    except Exception as e:
        print(f"❌ Vector search setup failed: {str(e)}")
        return False
    
    return True

if __name__ == "__main__":
    print("=== MongoDB Vector Search Debug ===\n")
    
    print(f"Environment variables loaded:")
    for key in ['DATABASE_NAME', 'COLLECTION_NAME']:
        value = env_vars.get(key, 'NOT FOUND')
        print(f"  {key}: {value}")
    
    # Test basic connection
    if PYMONGO_AVAILABLE:
        if test_mongodb_connection():
            print("✅ MongoDB connection successful")
        else:
            print("❌ MongoDB connection failed")
    else:
        print("⚠️  Skipping MongoDB connection test - pymongo not available")
    
    # Test vector search  
    if BEDROCK_AVAILABLE:
        if test_vector_search():
            print("\n✅ Vector search tests completed")
        else:
            print("\n❌ Vector search tests failed")
    else:
        print("⚠️  Skipping vector search test - Bedrock modules not available")
        
    # Fallback: Check JSON file structure
    print("\n--- Checking JSON File Structure ---")
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    json_path = os.path.join(project_root, "data", "insurance_agentic.policy.json")
    try:
        with open(json_path, 'r') as f:
            policies = json.load(f)
        
        print(f"✅ JSON file contains {len(policies)} policies")
        if policies:
            first_policy = policies[0]
            print(f"✅ First policy has fields: {list(first_policy.keys())}")
            if 'descriptionEmbedding' in first_policy:
                print(f"✅ Embeddings present with {len(first_policy['descriptionEmbedding'])} dimensions")
    except Exception as e:
        print(f"❌ Failed to read JSON file: {e}")