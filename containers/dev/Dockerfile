# hadolint ignore=DL3006
FROM aws-autorecycle-test-base

SHELL ["/bin/bash", "-ueox", "pipefail", "-c"]

WORKDIR /app

COPY . .

RUN pip install --no-cache-dir -r requirements-dev.txt

RUN groupadd -g 1001 devgroup && \
    useradd -m -u 1001 -g devgroup devuser && \
    chown -R 1001 /app

USER 1001:1001

ENV PYTHONPATH .
