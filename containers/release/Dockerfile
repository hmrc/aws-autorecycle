# hadolint ignore=DL3006
FROM aws-autorecycle-release-base

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
RUN chmod -R 0555 .

USER 1001:1001

ENV PYTHONPATH "${LAMBDA_TASK_ROOT}/src"
CMD [ "hander.lambda_handler" ]