# hadolint ignore=DL3006
FROM public.ecr.aws/lambda/python:3.11

SHELL ["/bin/bash", "-ueox", "pipefail", "-c"]

WORKDIR /app

COPY requirements*.txt .

RUN pip install --no-cache-dir -r requirements-dev.txt

ENV PYTHONPATH .
