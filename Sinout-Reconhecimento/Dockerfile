FROM python:3.9-slim

WORKDIR /app


RUN apt-get update && apt-get install -y \
    libgl1-mesa-glx \
    libglib2.0-0 \
    libsm6 \
    libxext6 \
    libxrender-dev \
    && rm -rf /var/lib/apt/lists/*


COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt


COPY sinout-fc.py .


ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1


ENV DEEPFACE_HOME=/app/.deepface

EXPOSE 5000


CMD ["python", "sinout-fc.py"]