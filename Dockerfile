#Dockerfile
FROM python:3.12-slim-bookworm

# Install system dependencies - ADICIONE libmagic1 aqui
RUN apt-get update && \
    apt-get install -y curl vim libpq-dev gcc python3-dev netcat-traditional libmagic1 && \
    apt-get clean

WORKDIR /app

# Copy requirements first to leverage Docker cache
COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

# Copy project files
COPY . .

# Create and set entrypoint
COPY entrypoint.sh /app/entrypoint.sh
RUN chmod +x /app/entrypoint.sh

ENTRYPOINT ["/app/entrypoint.sh"]

EXPOSE 8000

CMD ["python", "manage.py", "runserver", "0.0.0.0:8000"]