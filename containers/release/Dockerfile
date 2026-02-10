# hadolint ignore=DL3006
FROM public.ecr.aws/lambda/python:3.11

WORKDIR ${LAMBDA_TASK_ROOT}

COPY requirements.txt .
RUN pip install --no-cache-dir -r requirements.txt

COPY src/ src/
RUN chmod -R 0555 .

ENV PYTHONPATH "${LAMBDA_TASK_ROOT}/src"
CMD [ "hander.lambda_handler" ]