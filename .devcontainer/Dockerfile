FROM mcr.microsoft.com/devcontainers/python:3.13

RUN apt-get update \
    && apt-get install -y --no-install-recommends postgresql postgresql-client \
    && rm -rf /var/lib/apt/lists/*
