# Dockerfile
FROM python:3.10-slim

# Evita prompts de input do apt e problemas com timezone
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

WORKDIR /app

# Instala dependências do sistema necessárias para algumas bibliotecas (como psycopg2)
RUN apt-get update && \
    apt-get install -y gcc libpq-dev && \
    rm -rf /var/lib/apt/lists/*

# Instala dependências do projeto
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copia todo o restante do projeto
COPY . .

# Comando padrão ao iniciar o container
CMD ["python", "run.py"]
