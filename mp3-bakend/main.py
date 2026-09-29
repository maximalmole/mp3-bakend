import os
import uuid
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

DOWNLOAD_DIR = "/tmp/descargas"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

@app.get("/")
def home():
    return {"status": "Servidor de extracción MP3 activo"}

@app.get("/descargar-mp3")
def descargar_mp3(url: str):
    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")
    
    # Configuración flexible de formato: 'ba/b' busca solo audio (ba), o video+audio (b) para extraer el MP3
    ydl_opts = {
        'format': 'ba/b',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
    }

    # Usar cookies si existen en el repositorio
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + ".mp3"
            titulo_original = info.get('title', 'audio') + ".mp3"

        return FileResponse(
            path=mp3_filename, 
            filename=titulo_original, 
            media_type='audio/mpeg'
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
