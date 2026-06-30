from supertonic import TTS
import soundfile as sf
import uuid
import math


tts = TTS(auto_download=True)

def generateText(voice_style: str, lang: str, text: str) -> dict:

    filename = f"output_{uuid.uuid4().hex}.wav"
    style = tts.get_voice_style(voice_name=f"{voice_style}")

    wav, duration = tts.synthesize(
        text=text,
        lang=lang,
        voice_style=style,
        total_steps=9,
        speed=1.3,
    )

    tts.save_audio(wav, filename)
    return filename, f"{math.ceil(duration[0] * 1000)/1000}"
