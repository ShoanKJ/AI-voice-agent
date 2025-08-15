from fastapi import FastAPI, Request, HTTPException, UploadFile, File
from fastapi.responses import HTMLResponse, JSONResponse
from fastapi.staticfiles import StaticFiles
from fastapi.templating import Jinja2Templates
from fastapi.middleware.cors import CORSMiddleware

from pydantic import BaseModel
import requests
import os
from dotenv import load_dotenv
from pathlib import Path
import shutil
import assemblyai as aai  # <-- Import AssemblyAI SDK

# Load environment variables
load_dotenv()

MURF_API_KEY = os.getenv("MURF_API_KEY")
ASSEMBLYAI_API_KEY = os.getenv("ASSEMBLYAI_API_KEY")
print("DEBUG: Murf API Key is", MURF_API_KEY)
print("DEBUG: AssemblyAI API Key Loaded:", bool(ASSEMBLYAI_API_KEY))

# Setup AssemblyAI
aai.settings.api_key = ASSEMBLYAI_API_KEY
transcriber = aai.Transcriber()

# FastAPI setup
app = FastAPI()

# Enable CORS for frontend
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_methods=["*"],
    allow_headers=["*"],
)

# Serve static files and templates
app.mount("/static", StaticFiles(directory="static"), name="static")
templates = Jinja2Templates(directory="templates")

# Directory to store uploaded files
UPLOAD_DIR = Path("uploads")
UPLOAD_DIR.mkdir(exist_ok=True)

# Homepage
@app.get("/", response_class=HTMLResponse)
async def read_root(request: Request):
    return templates.TemplateResponse("index.html", {"request": request})


# Text-to-Speech Request Body
class TTSRequest(BaseModel):
    text: str

# Murf TTS Endpoint
@app.post("/generate-audio")
def generate_audio(request: TTSRequest):
    url = "https://api.murf.ai/v1/speech/generate"

    headers = {
        "api-key": MURF_API_KEY,
        "Content-Type": "application/json"
    }

    payload = {
        "voiceId": "en-US-natalie",  # Customize as needed
        "text": request.text,
        "format": "mp3"
    }

    try:
        response = requests.post(url, json=payload, headers=headers)
        if response.status_code != 200:
            print("Murf API Error:", response.status_code, response.text)
            raise HTTPException(status_code=500, detail="Murf API returned an error")

        return response.json()

    except Exception as e:
        print("Server Error:", e)
        raise HTTPException(status_code=500, detail="Something went wrong while generating audio")


# 🎤 Upload recorded audio (Day 5)
@app.post("/upload-audio")
async def upload_audio(file: UploadFile = File(...)):
    file_location = UPLOAD_DIR / file.filename
    with open(file_location, "wb") as f:
        shutil.copyfileobj(file.file, f)

    return {
        "filename": file.filename,
        "content_type": file.content_type,
        "size": file_location.stat().st_size
    }


# 📝 Transcribe uploaded audio using AssemblyAI (Day 6)
@app.post("/transcribe/file")
async def transcribe_file(file: UploadFile = File(...)):
    try:
        audio_data = await file.read()  # Read audio as bytes
        transcript = transcriber.transcribe(audio_data)  # Transcribe with AssemblyAI
        return JSONResponse(content={"transcript": transcript.text})
    except Exception as e:
        print("Transcription error:", str(e))
        raise HTTPException(status_code=500, detail="Transcription failed")
