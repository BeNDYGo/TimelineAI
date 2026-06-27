from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from TTI import generate

app = FastAPI()


class GenerationRequest(BaseModel):
    prompt: str


class GenerationResponse(BaseModel):
    filename: str


@app.post("/generate", response_model=GenerationResponse)
async def generate_endpoint(request: GenerationRequest):
    """
    Generate image from text prompt.
    
    - **prompt**: Text description of the image

    Returns the generated image filename.
    """
    try:
        filename = generate(
            prompt=request.prompt
        )
        
        return GenerationResponse(filename=filename)
        
    except Exception as e:
        raise HTTPException(status_code=500, detail=f"Ошибка генерации: {str(e)}")


@app.get("/health")
async def health_check():
    """Health check endpoint"""
    return {"status": "ok"}

if __name__ == "__main__":
    import uvicorn
    uvicorn.run(app, host="0.0.0.0", port=4002)
