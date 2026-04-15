FROM python:3.11-slim

WORKDIR /app

# Instalar dependencias del sistema
RUN apt-get update && apt-get install -y \
    build-essential \
    && rm -rf /var/lib/apt/lists/*

# Copiar archivos de requerimientos
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copiar el código del bot
COPY whatsapp_bot.py .
COPY .env .

# Exponer el puerto del bot
EXPOSE 3001

# Comando para arrancar el bot
CMD ["python", "whatsapp_bot.py"]
