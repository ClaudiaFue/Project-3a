# Use a Python base image
FROM python:3.9-slim

# Set working directory
WORKDIR /app

COPY . /app

RUN pip install --upgrade pip

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]




