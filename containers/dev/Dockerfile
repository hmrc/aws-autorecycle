# hadolint ignore=DL3006
FROM aws-autorecycle-test-base

SHELL ["/bin/bash", "-ueox", "pipefail", "-c"]

WORKDIR /app

COPY requirements*.txt .

RUN pip install --no-cache-dir -r requirements-dev.txt

ENV PYTHONPATH .
