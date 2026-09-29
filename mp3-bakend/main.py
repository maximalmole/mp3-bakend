import os
import uuid
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from urllib.parse import quote
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"],
)

DOWNLOAD_DIR = "/tmp/descargas"
COOKIES_PATH = "/tmp/cookies_render.txt"
os.makedirs(DOWNLOAD_DIR, exist_ok=True)

# Cargar cookies desde la Variable de Entorno Privada de Render
cookies_env = os.getenv("YOUTUBE_COOKIES")
if cookies_env:
    with open(COOKIES_PATH, "w", encoding="utf-8") as f:
        f.write(cookies_env)

@app.get("/")
def home():
    return {"status": "Servidor de extracción MP3 activo"}

@app.get("/descargar-mp3")
def descargar_mp3(url: str):
    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")
    
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
        'extractor_args': {
            'youtube': {
                'player_client': ['ios', 'android', 'mweb']
            }
        }
    }

    # Si existen cookies privadas en /tmp/
    if os.path.exists(COOKIES_PATH):
        ydl_opts['cookiefile'] = COOKIES_PATH
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + ".mp3"
            
            titulo_raw = info.get('title', 'audio')
            titulo_limpio = re.sub(r'[\\/*?:"<>|]', "", titulo_raw) + ".mp3"

        encoded_filename = quote(titulo_limpio)
        headers = {
            "Content-Disposition": f'attachment; filename="{titulo_limpio}"; filename*=UTF-8\'\'{encoded_filename}'
        }

        return FileResponse(
            path=mp3_filename, 
            media_type='audio/mpeg',
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
