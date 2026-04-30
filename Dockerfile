## Use official Python image
#FROM python:3.10-slim
#
## Set working directory inside container
#WORKDIR /app
#
## Copy all files into container
#COPY . .
#
## Install dependencies
#RUN pip install --no-cache-dir -r requirements.txt
#
## Run your app
#CMD ["python", "main.py"]

#
#FROM python:3.10-slim
#
#WORKDIR /app
#
#COPY . .
#
## Install system dependencies for OpenCV
#RUN apt-get update && apt-get install -y \
#    libgl1 \
#    libglib2.0-0 \
#    libsm6 \
#    libxext6 \
#    libxrender1 \
#    libxcb1 \
#    && rm -rf /var/lib/apt/lists/*
#
## Install Python dependencies
#RUN pip install --no-cache-dir -r requirements.txt
#
#CMD ["python", "main.py"]



FROM python:3.10-slim

WORKDIR /app

COPY . .

RUN apt-get update && apt-get install -y \
    libglib2.0-0 \
    libgl1 \
    && rm -rf /var/lib/apt/lists/*

RUN pip install --no-cache-dir -r requirements.txt

CMD ["python", "app.py"]