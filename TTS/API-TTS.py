from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from TTS import generateText

app = FastAPI()


class TTSRequest(BaseModel):
    voice_style: str
    lang: str
    text: str

class TTSResponse(BaseModel):
    filename: str
    duration: str


@app.post("/generate", response_model=TTSResponse)
async def generate_tts(request: TTSRequest):
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
