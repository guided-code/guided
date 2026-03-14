FROM python:3.12-slim

RUN apt-get update && apt-get install -y \
    python3-pip \
    && rm -rf /var/lib/apt/lists/*

WORKDIR /usr/src/guided

COPY --from=docker.io/astral/uv:latest /uv /usr/local/bin/uv

COPY . .

RUN /usr/local/bin/uv sync
