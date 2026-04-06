FROM python:3.12-slim

WORKDIR /app

COPY requirements.txt /app/requirements.txt
RUN pip install --no-cache-dir -r /app/requirements.txt

COPY app /app/app
COPY web /app/web

CMD ["python", "-m", "uvicorn", "web.main:app", "--host", "0.0.0.0", "--port", "8080"]
