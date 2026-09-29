FROM python:3.10-slim

# Instalar ffmpeg, curl y dependencias
RUN apt-get update && apt-get install -y ffmpeg curl unzip && rm -rf /var/lib/apt/lists/*

# Instalar Deno (Motor de JS necesario para los desafíos de YouTube)
RUN curl -fsSL https://deno.land/install.sh | sh
ENV PATH="/root/.deno/bin:$PATH"

WORKDIR /app

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY . .

EXPOSE 10000

# Actualizar yt-dlp al iniciar y arrancar el servidor
CMD ["sh", "-c", "pip install -U yt-dlp && uvicorn main:app --host 0.0.0.0 --port 10000"]
