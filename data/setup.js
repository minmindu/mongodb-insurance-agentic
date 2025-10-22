// Simple MongoDB Setup - Just the essentials
// Run these commands in mongosh after connecting to your cluster

// Use the insurance database
use("insurance_claims");

// 1. Import data using mongoimport (run this in terminal first):
// mongoimport --uri "mongodb+srv://mdbadmin:mdbadmin@demo.31ady.mongodb.net/insurance_claims" --collection policy_documents_v2 --file data/insurance_agentic.policy.json --jsonArray --drop

// 2. Verify data was loaded
print("Checking data...");
const count = db.policy_documents_v2.countDocuments({});
print(`Documents loaded: ${count}`);

// 3. Vector search index configuration (copy this to Atlas UI):
const indexConfig = {
  "name": "description_index",
  "type": "vectorSearch", 
  "definition": {
    "fields": [
      {
        "type": "vector",
        "path": "descriptionEmbedding", 
        "numDimensions": 1024,
        "similarity": "cosine"
      }
    ]
  }
};

print("Vector search index config:");
print(JSON.stringify(indexConfig, null, 2));
print("\nCopy the above config to MongoDB Atlas → Search Indexes → Create Search Index");