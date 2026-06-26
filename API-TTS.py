from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from TTS import generateText

app = FastAPI(title="TTS API", description="Text-to-Speech API using Supertonic")


class TTSRequest(BaseModel):
    voice_style: str
    lang: str
    text: str

class TTSResponse(BaseModel):
    filename: str
    duration: str


@app.post("/generate", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
    """
    Generate text-to-speech audio file.
    
    - **voice_style**: Voice style (F1 to M5)
    - **lang**: Language code (e.g., 'ru', 'en')
    - **text**: Text to synthesize
    
    Returns the generated audio filename and duration in seconds.
    """
    try:
        filename, duration = generateText(
            voice_style=request.voice_style,
            lang=request.lang,
            text=request.text
        )
        
        return TTSResponse(filename=filename, duration=duration)
    
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Error generating audio: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}


if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4001)
