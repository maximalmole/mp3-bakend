import os
import uuid
import re
from fastapi import FastAPI, HTTPException
from fastapi.middleware.cors import CORSMiddleware
from fastapi.responses import FileResponse
from urllib.parse import quote
import yt_dlp

app = FastAPI()

# Permite que el JavaScript de tu web lea el header con el título original
app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
    expose_headers=["Content-Disposition"], # <--- Permiso clave para leer el nombre
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

    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"
    
    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            mp3_filename = os.path.splitext(filename)[0] + ".mp3"
            
            # Obtener el título original del video de YouTube
            titulo_raw = info.get('title', 'audio')
            # Limpiar caracteres no permitidos en nombres de archivo
            titulo_limpio = re.sub(r'[\\/*?:"<>|]', "", titulo_raw) + ".mp3"

        # Codificar el título para compatibilidad con caracteres especiales (acentos, ñ, etc.)
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
