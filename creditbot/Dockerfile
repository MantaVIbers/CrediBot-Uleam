# Imagen del backend FastAPI de CrediBot
FROM python:3.12-slim

# Evita archivos .pyc y fuerza logs sin buffer (mejor para contenedores)
ENV PYTHONDONTWRITEBYTECODE=1 \
    PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependencias primero para aprovechar la cache de capas
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia el código de la aplicación
COPY . .

# Puerto por defecto (Render/hosts inyectan la variable PORT)
EXPOSE 8000

# Arranca el servidor; usa $PORT si el host lo define, si no 8000
CMD ["sh", "-c", "uvicorn app.main:app --host 0.0.0.0 --port ${PORT:-8000}"]
