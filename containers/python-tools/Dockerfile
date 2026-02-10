FROM 419929493928.dkr.ecr.eu-west-2.amazonaws.com/docker-hub/library/python:3.11

RUN pip install --no-cache-dir \
    ruff==0.6.2 \
    mypy==1.11.2 \
    "bandit[toml]==1.7.10" \
    black==24.8.0 \
    isort==5.13.2 \
    pytest==8.3.3

ENTRYPOINT [ "bash" ]
WORKDIR /work

COPY pyproject.toml /tmp/
COPY src/ /tmp/src/
RUN pip install --no-cache-dir /tmp