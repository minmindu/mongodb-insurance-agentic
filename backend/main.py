from fastapi import FastAPI, Request, File, UploadFile, HTTPException
from fastapi.responses import StreamingResponse
from fastapi.middleware.cors import CORSMiddleware
from fastapi.middleware.cors import CORSMiddleware
from fastapi import APIRouter
from dotenv import load_dotenv
import os
from tempfile import NamedTemporaryFile
from typing import Optional
from pic2textApi import stream_image_to_bedrock

load_dotenv()

app = FastAPI()

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
    """
    Endpoint to upload an image and stream analysis from Claude via AWS Bedrock
    """
    if not file.content_type or not file.content_type.startswith('image/'):
        raise HTTPException(status_code=400, detail="File must be an image")
    
    # Save the uploaded file to a temporary location
    with NamedTemporaryFile(delete=False, suffix=os.path.splitext(file.filename)[1]) as temp_file:
        temp_file_path = temp_file.name
        content = await file.read()
        temp_file.write(content)
    
    try:
        # Create a custom generator that handles the cleanup
        def generate_with_cleanup():
            try:
                yield from stream_image_to_bedrock(temp_file_path, model_id)
            finally:
                # Clean up the temporary file
                if os.path.exists(temp_file_path):
                    os.unlink(temp_file_path)
        
        # Return a streaming response
        return StreamingResponse(
            generate_with_cleanup(),
            media_type="text/plain"
        )
    except Exception as e:
        # Make sure to clean up if an exception occurs
        if os.path.exists(temp_file_path):
            os.unlink(temp_file_path)
        raise HTTPException(status_code=500, detail=f"Error processing image: {str(e)}")