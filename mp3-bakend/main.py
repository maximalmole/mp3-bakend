import os
import uuid
import re
from fastapi import FastAPI, HTTPException, BackgroundTasks
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

def cleanup_file(filepath: str):
    """Elimina el archivo descargado para evitar sobrepasar los 512 MB de RAM en Render."""
    try:
        if os.path.exists(filepath):
            os.remove(filepath)
    except Exception as e:
        print(f"Error al eliminar {filepath}: {e}")

def setup_cookies():
    """Genera el archivo de cookies desde la Variable de Entorno YOUTUBE_COOKIES en Render."""
    cookies_env = os.getenv("YOUTUBE_COOKIES")
    if cookies_env and len(cookies_env.strip()) > 50:
        with open(COOKIES_PATH, "w", encoding="utf-8") as f:
            f.write(cookies_env.strip())
        return True
    return False

@app.get("/")
def home():
    has_cookies = setup_cookies()
    return {
        "status": "Servidor de extracción MP3 activo (Optimizado para memoria RAM)",
        "cookies_cargadas": has_cookies
    }

@app.get("/descargar-mp3")
def descargar_mp3(url: str, background_tasks: BackgroundTasks):
    # Limpiar cualquier archivo huérfano previo en la carpeta de descargas
    for f in os.listdir(DOWNLOAD_DIR):
        file_path = os.path.join(DOWNLOAD_DIR, f)
        if os.path.isfile(file_path):
            cleanup_file(file_path)

    file_id = str(uuid.uuid4())
    output_template = os.path.join(DOWNLOAD_DIR, f"{file_id}.%(ext)s")
    
    has_cookies = setup_cookies()

    ydl_opts = {
        'format': 'bestaudio/best',
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'outtmpl': output_template,
        'quiet': True,
        'no_warnings': True,
        'concurrent_fragment_downloads': 1,  # Limita el uso de CPU/RAM durante la descarga
        'extractor_args': {
            'youtube': {
                'player_client': ['web', 'mweb', 'android', 'ios']
            }
        }
    }

    if has_cookies and os.path.exists(COOKIES_PATH):
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

        # Programar la eliminación automática del archivo MP3 una vez enviado al usuario
        background_tasks.add_task(cleanup_file, mp3_filename)

        return FileResponse(
            path=mp3_filename, 
            media_type='audio/mpeg',
            headers=headers
        )
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))
