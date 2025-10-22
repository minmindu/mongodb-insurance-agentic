#!/usr/bin/env python3
"""
Simple MongoDB connection test
"""

import json
import os

# Try to load environment variables manually
# Get the project root directory (two levels up from this test script)
script_dir = os.path.dirname(os.path.abspath(__file__))
project_root = os.path.dirname(os.path.dirname(script_dir))
env_path = os.path.join(project_root, "backend", ".env")

env_vars = {}
try:
    with open(env_path, 'r') as f:
        for line in f:
            if line.strip() and not line.startswith('#') and '=' in line:
                key, value = line.strip().split('=', 1)
                env_vars[key] = value
    print("✅ Loaded environment variables")
except Exception as e:
    print(f"❌ Failed to load .env file: {e}")
    exit(1)

# Simple test using pymongo (if available)
try:
    import pymongo
    print("✅ pymongo available")
    
    client = pymongo.MongoClient(env_vars.get('MONGODB_URI'))
    db = client[env_vars.get('DATABASE_NAME')]
    collection = db[env_vars.get('COLLECTION_NAME')]
    
    print(f"Database: {env_vars.get('DATABASE_NAME')}")
    print(f"Collection: {env_vars.get('COLLECTION_NAME')}")
    
    # Test connection
    total_docs = collection.count_documents({})
    print(f"Total documents: {total_docs}")
    
    if total_docs > 0:
        # Get sample document
        sample = collection.find_one({})
        print(f"Sample document fields: {list(sample.keys())}")
        
        # Check specific fields
        if 'description' in sample:
            print(f"✅ Has 'description' field")
            print(f"Description preview: {sample['description'][:100]}...")
        else:
            print("❌ Missing 'description' field")
        
        if 'descriptionEmbedding' in sample:
            print(f"✅ Has 'descriptionEmbedding' field")
            print(f"Embedding length: {len(sample['descriptionEmbedding'])}")
        else:
            print("❌ Missing 'descriptionEmbedding' field")
            
        # Check for other possible field names
        possible_desc_fields = [f for f in sample.keys() if 'desc' in f.lower()]
        possible_embed_fields = [f for f in sample.keys() if 'embed' in f.lower()]
        
        print(f"Possible description fields: {possible_desc_fields}")
        print(f"Possible embedding fields: {possible_embed_fields}")
    
except ImportError:
    print("❌ pymongo not available, using JSON file check instead")
    
    # Fallback: check the JSON file structure
    script_dir = os.path.dirname(os.path.abspath(__file__))
    project_root = os.path.dirname(os.path.dirname(script_dir))
    json_path = os.path.join(project_root, "data", "insurance_agentic.policy.json")
    try:
        with open(json_path, 'r') as f:
            policies = json.load(f)
        
        print(f"✅ Loaded JSON file with {len(policies)} policies")
        
        first_policy = policies[0]
        print(f"JSON policy fields: {list(first_policy.keys())}")
        
        if 'description' in first_policy:
            print(f"✅ JSON has 'description' field")
        if 'descriptionEmbedding' in first_policy:
            print(f"✅ JSON has 'descriptionEmbedding' field")
            print(f"Embedding dimensions: {len(first_policy['descriptionEmbedding'])}")
        
    except Exception as e:
        print(f"❌ Failed to read JSON file: {e}")

print("\n--- Environment Variables ---")
for key in ['MONGODB_URI', 'DATABASE_NAME', 'COLLECTION_NAME', 'COLLECTION_NAME_2']:
    value = env_vars.get(key, 'NOT FOUND')
    # Hide sensitive parts of URI
    if 'URI' in key and value != 'NOT FOUND':
        masked_value = value[:20] + "..." + value[-10:]
        print(f"{key}: {masked_value}")
    else:
        print(f"{key}: {value}")