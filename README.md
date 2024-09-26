
# aws-autorecycle

This is a Lambda resource which starts a relevant step function when invoked by a relevant Cloudwatch event. It checks that the component is recyclable, and if it is, triggers the step function with the relevant strategy to recycle the component. 


## Project Structure

The structure of this project, along with steps to build the Lambda and run the tests locally was copied from the example project in the [infrastructure-pipeline-lambda-build](https://github.com/hmrc/infrastructure-pipeline-lambda-build/tree/main/example-project) repo. 


| Location       | Description                                                                     |
|----------------|---------------------------------------------------------------------------------|
| src/           | The code for the Lambda is contained in `src`.                                  |
| terraform/     | Terraform configuration that is deployed by `webops-terraform`.                 |
| tests/         | Integration and unit tests.                                                     |
| Dockerfle      | The Docker commands required to build a test and release version of the Lambda. |
| Makefile       | The commands required by the `buildLambda` function, plus others.               |
| batect.yml     | The batect configuration for running the lambda and tests.                      |
| pyproject.toml | The Python project configuration, including Poetry dependencies.                |




## Building the Lambda and running the tests

### Building the Image

You will need to authenticate with the management account to be able to pull the base images, e.g:  
`aws-vault exec webops-management-RoleInfrastructureEngineer -- aws ecr get-login-password --region eu-west-2 | docker login --username AWS --password-stdin 419929493928.dkr.ecr.eu-west-2.amazonaws.com`

The Lambda can be built with `make build TAG=autorecycle`.  
This will build a Docker image which is tagged with `autorecycle`.

### Linting and Security Tests

The linting and security tests are provided by the `aws-lambda-dev-base` image.

They can be ran via Docker with `make test-lint`, which invokes the `make lint` command in `/devtools/Makefile`.

### Unit Tests

Run the unit tests via your IDE or with Docker by `make test-unit`.

### Integration Tests

To run the integration tests via your IDE you need to start the Lambda locally.  
This can be performed by running `make lambda-local` which starts the Lambda on port `8080`.  
You can then run the tests normally via your IDE.

Alternatively, run `make test-integration` which will start the Lambda and run the integration tests for you in Docker.

## Building and Deploying the Lambda

The `buildLambda` Jenkins function takes care of building, testing and pushing the Lambda to ECR.

Currently, the deployment is handled by `webops-terraform` which uses the `terraform/` folder as a module.

You can see this example Lambda deployed [here](https://github.com/hmrc/webops-terraform/blob/c0668f0359884256451422ed745e0040573c2bb8/components/autorecycle/lambda_functions.tf#L16).

## Dockerfile Structure

The Dockerfile contains both the `dev` (test) stage and a `release` stage.

### Stage: dev

In the `dev` stage, it bases the image from `aws-lambda-dev-base` which contains linting and security tooling.

It copies in the `pyproject.toml` which contains the Poetry dependencies and exports a `requirements.txt` which is used by the
release stage to install locked production dependencies that the Lambda was tested with at the time.

Finally, the Python package `example` and the `tests` are copied in to the image.

### Stage: release

In the `release` stage, it bases the image from `aws-lambda-release-base` which contains a patched version of Python.

It installs the production dependencies via pip from the `requirements.txt` generated in the `dev` stage.

It then copies the Python package `example` and makes it executable.

Finally, it tests whether it can import the `example` handler file and then sets the handler endpoint that Lambda will execute.

## batect.yml

The batect file contains three containers:

| Name         | Description                                                                         |
|--------------|-------------------------------------------------------------------------------------|
| dev          | The tooling and development container used locally only.                            |
| release      | A build of the container using only the runtime dependencies.                       |
| lambda-local | A container based on release to run the lambda locally for integration testing or debugging.|

And it contains the following tasks:

| Name             | Description                                                                                                  |
|------------------|--------------------------------------------------------------------------------------------------------------|
| local            | Starts the `lambda-local` container with a shell entrypoint for debugging. You can invoke this lambda locally as explained below |
| test:integration | Starts the `lambda-local` container to host the lambda and then runs `pytest -vv tests/integration` in the `dev` container to test the lambda.|
| test:unit        | Starts the `dev` container and runs `pytest -v tests/unit`.                                                  |

check all available tasks included with the bundles `./batect --list-tasks`

## Other requirements

Ensure you use the `asg-recycle` module - this will take care of creating any required extras e.g. SQS queue.

## Configuration

Component recycling configuration is done with tags on the asg

### Required tags
autorecycle_recycle_on_asg_update: "true" or "false"  
autorecycle_strategy: eg. "in-out"  

### Optional tags
autorecycle_slack_monitoring_channel  
autorecycle_notify_pager_duty: "true" or "false"  
autorecycle_team  
autorecycle_step_function_name  
autorecycle_dry_run: "true" or "false"  

### Recycle Strategy

The strategy key above defines the method for recycling and is used by the step function to choose the path to take.

* out-in - this will double the size of an autoscaling group to scale up and halve the size of the autoscaling group to scale down. This is the standard default method.
* in-out - one at a time instance scaling in and then out. Used where we have ENI e.g. rate_hods_proxy
