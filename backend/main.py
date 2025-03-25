from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
from dotenv import load_dotenv
import os
import uvicorn
from tempfile import NamedTemporaryFile
from typing import Optional
from pic2textApi import stream_image_to_bedrock
from insurance_agent import insurance_agent
import logging
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
                
                # Now that we have the full description, call the insurance agent
                logger.info(f"Description complete, calling insurance agent with description preview: {image_description[:100]}...")
                insurance_result = insurance_agent(image_description)
                logger.info(f"Insurance agent processing result: {insurance_result}")
                
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
    
if __name__ == "__main__":
    uvicorn.run("main:app", host="0.0.0.0", port=8000, reload=True)