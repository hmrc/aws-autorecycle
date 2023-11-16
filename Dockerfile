FROM aws-autocycle-lambda-dev AS dev

WORKDIR ${LAMBDA_TASK_ROOT}

COPY pyproject.toml .
RUN poetry install --no-root && poetry export -o requirements.txt

COPY src src
COPY tests tests

FROM aws-autocycle-lambda-release AS release

WORKDIR ${LAMBDA_TASK_ROOT}

COPY --from=dev ${LAMBDA_TASK_ROOT}/requirements.txt .
RUN pip install -r requirements.txt

COPY src src

RUN chmod -R o+rX .

ENV PYTHONPATH /var/task/src
CMD ["handler.lambda_handler"]
