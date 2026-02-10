FROM public.ecr.aws/lambda/python:3.11

COPY pyproject.toml /var/task/

# 2. Install dependencies (including aws-lambda-logging and botocore < 1.27)
RUN pip install .

COPY src/ /var/task/

ENV PYTHONPATH=/var/task

CMD ["monitor_autorecycle.main.lambda_handler"]