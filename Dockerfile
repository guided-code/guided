FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/guided

COPY . .

RUN pip install uv
