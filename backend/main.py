from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
from dotenv import load_dotenv
import os
from tempfile import NamedTemporaryFile
from typing import Optional
from pic2textApi import stream_image_to_bedrock
from insurance_agent import insurance_agent
from bson import ObjectId
import logging
import json
from pymongo import MongoClient

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

load_dotenv()

app = FastAPI()

image_description = None  # Global variable to store the most recent description

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

router = APIRouter()

@app.get("/")
async def read_root(request: Request):
    return {"message": "Server is running"}


@app.post("/imageDescriptor")
async def analyze_image(
    file: UploadFile = File(...),
    model_id: Optional[str] = 'anthropic.claude-3-sonnet-20240229-v1:0',
    prompt: Optional[str] = "What do you see in this image? Give a concise description and focus and what happened to vehicles."
):
    global image_description  # Use the global variable

    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save the uploaded file to a temporary location
    with NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        temp_file_path = temp_file.name
        content = await file.read()
        temp_file.write(content)
    
    try:
        # Reset the current description
        image_description = ""
        
        # Process the image and collect the full description before responding
        def process_with_insurance_agent():
            global image_description
            try:
                # Collect the full description
                for chunk in stream_image_to_bedrock(temp_file_path, model_id):
                    image_description += chunk
                    yield chunk
                
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        # Return a streaming response
        return StreamingResponse(
            process_with_insurance_agent(),
            media_type="text/plain"
        )
    
    except Exception as e:
        # Make sure to clean up if an exception occurs
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")
    
@app.post("/runAgent")
async def run_agent():
    global image_description

    if not image_description:
        raise HTTPException(status_code=400, detail="Image description not yet available")

    try:
        # Call the insurance agent with the current image description
        logger.info(f"Running agent with description: {image_description[:100]}...")
        object_id = insurance_agent(image_description)
        logger.info(f"ObjectId: {object_id}")       

    except Exception as e:
        logger.error(f"Error during agent processing: {str(e)}")
        raise HTTPException(status_code=500, detail=f"Agent processing error: {str(e)}")
    
    cluster_uri = os.getenv("MONGODB_URI")
    database_name = os.getenv("DATABASE_NAME")
    collection_name = os.getenv("COLLECTION_NAME_2")

    client = MongoClient(cluster_uri)
    db = client[database_name]
    collection = db[collection_name]

    document = collection.find_one({"_id": ObjectId(object_id)})

    if document:
        document["_id"] = str(document["_id"])  # Convert ObjectId to string
        
        # Debug logging to see what's in the document
        logger.info(f"Document retrieved: {document}")
        logger.info(f"Recommendation field: {document.get('recommendation', 'NOT FOUND')}")
        logger.info(f"Recommendation type: {type(document.get('recommendation'))}")
        
        # Keep the original nested structure for the enhanced frontend UI
        if 'recommendation' in document:
            rec = document['recommendation']
            if isinstance(rec, dict):
                # Keep the nested object structure for the new enhanced UI
                logger.info(f"Keeping nested recommendation structure: {rec}")
                # Ensure all expected fields exist with defaults
                if 'immediate_actions' not in rec:
                    rec['immediate_actions'] = []
                if 'short_term_actions' not in rec:
                    rec['short_term_actions'] = []
                if 'approval_guidance' not in rec:
                    rec['approval_guidance'] = {}
                if 'reserve_recommendations' not in rec:
                    rec['reserve_recommendations'] = {}
                
                document['recommendation'] = rec
                
            elif isinstance(rec, str):
                # If it's a string, try to parse it as JSON first
                try:
                    import json
                    parsed_rec = json.loads(rec)
                    if isinstance(parsed_rec, dict):
                        # Keep as nested object for enhanced UI
                        document['recommendation'] = parsed_rec
                    elif isinstance(parsed_rec, list):
                        # Convert array to basic structure
                        document['recommendation'] = {
                            'immediate_actions': parsed_rec,
                            'short_term_actions': [],
                            'approval_guidance': {},
                            'reserve_recommendations': {}
                        }
                    else:
                        # Fallback to basic structure
                        document['recommendation'] = {
                            'immediate_actions': [rec],
                            'short_term_actions': [],
                            'approval_guidance': {},
                            'reserve_recommendations': {}
                        }
                except:
                    # If JSON parsing fails, create basic structure
                    actions = []
                    if '\n' in rec:
                        actions = [line.strip() for line in rec.split('\n') if line.strip()]
                    elif '•' in rec:
                        actions = [line.strip() for line in rec.split('•') if line.strip()]
                    elif '-' in rec:
                        actions = [line.strip() for line in rec.split('-') if line.strip()]
                    else:
                        actions = [rec]
                    
                    document['recommendation'] = {
                        'immediate_actions': actions,
                        'short_term_actions': [],
                        'approval_guidance': {},
                        'reserve_recommendations': {}
                    }
            elif isinstance(rec, list):
                # Convert array to nested structure for enhanced UI
                document['recommendation'] = {
                    'immediate_actions': rec,
                    'short_term_actions': [],
                    'approval_guidance': {},
                    'reserve_recommendations': {}
                }
            else:
                # Fallback to basic structure
                document['recommendation'] = {
                    'immediate_actions': [str(rec)] if rec else [],
                    'short_term_actions': [],
                    'approval_guidance': {},
                    'reserve_recommendations': {}
                }
        else:
            document['recommendation'] = {
                'immediate_actions': ["No specific recommendations generated"],
                'short_term_actions': [],
                'approval_guidance': {},
                'reserve_recommendations': {}
            }
        
        # Ensure priority is always a string for frontend compatibility
        if 'priority' in document:
            if isinstance(document['priority'], (int, float)):
                priority_map = {1: "Low", 2: "Medium", 3: "High", 4: "Critical"}
                document['priority'] = priority_map.get(document['priority'], "Standard")
            elif not isinstance(document['priority'], str):
                document['priority'] = str(document['priority'])
        else:
            document['priority'] = "Standard"
        
        logger.info(f"Final recommendation array: {document['recommendation']}")
        logger.info(f"Final priority: {document['priority']}")
        
        return document
    else:
        raise HTTPException(status_code=404, detail="Document not found")

   
