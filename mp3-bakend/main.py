import os
import tempfile
from fastapi import FastAPI, HTTPException, Query
from fastapi.responses import FileResponse
from fastapi.middleware.cors import CORSMiddleware
import yt_dlp

app = FastAPI()

app.add_middleware(
    CORSMiddleware,
    allow_origins=["*"],
    allow_credentials=True,
    allow_methods=["*"],
    allow_headers=["*"],
)

@app.get("/descargar-mp3")
async def descargar_mp3(url: str = Query(..., description="YouTube Video URL")):
    temp_dir = tempfile.mkdtemp()
    out_tmpl = os.path.join(temp_dir, "%(title)s.%(ext)s")
    
    ydl_opts = {
        'format': 'bestaudio/best',
        'outtmpl': out_tmpl,
        'postprocessors': [{
            'key': 'FFmpegExtractAudio',
            'preferredcodec': 'mp3',
            'preferredquality': '192',
        }],
        'quiet': True,
        'no_warnings': True,
        # 1. Bypasses standard web bot checks by using mobile client APIs
        'extractor_args': {
            'youtube': {
                'player_client': ['android', 'ios', 'mweb'],
            }
        },
        # 2. Add realistic browser user agent
        'http_headers': {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/122.0.0.0 Safari/537.36',
        }
    }
    
    # 3. Use a cookies.txt file if available on the server
    if os.path.exists("cookies.txt"):
        ydl_opts['cookiefile'] = "cookies.txt"

    try:
        with yt_dlp.YoutubeDL(ydl_opts) as ydl:
            info = ydl.extract_info(url, download=True)
            filename = ydl.prepare_filename(info)
            base_name, _ = os.path.splitext(filename)
            mp3_file = base_name + ".mp3"

            if not os.path.exists(mp3_file):
                raise HTTPException(status_code=500, detail="El archivo MP3 no se pudo generar.")

            return FileResponse(
                path=mp3_file,
                media_type="audio/mpeg",
                filename=f"{info.get('title', 'audio')}.mp3"
            )
    except Exception as e:
        error_msg = str(e)
        # Custom error handling for YouTube bot error
        if "Sign in to confirm you're not a bot" in error_msg:
            raise HTTPException(
                status_code=403, 
                detail="YouTube ha bloqueado temporalmente la IP del servidor. "
                       "Actualiza las cookies en Render o habilita el modo Android client."
            )
        raise HTTPException(status_code=500, detail=error_msg)
