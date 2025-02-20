
# aws-autorecycle

This is a Lambda resource which starts a relevant step function when invoked by a relevant Cloudwatch event. It checks that the component is recyclable, and if it is, triggers the step function with the relevant strategy to recycle the component. 


## Project Structure

The structure of this project, along with steps to build the Lambda and run the tests locally was copied from the example project in the [aws-lambda-example-project](https://github.com/hmrc/aws-lambda-example-project/tree/python/3.11) repo. 


| Location       | Description                                                                     |
|----------------|---------------------------------------------------------------------------------|
| containers     | The Dockerfiles for development and release builds                              |
| src/           | The code for the Lambda is contained in `src`.                                  |
| terraform/     | Terraform configuration that is deployed by `webops-terraform`.                 |
| tests/         | Integration and unit tests.                                                     |
| .gitignore     | Every repo should have one.                                                     |
| .trivyignore   | Not all trivy issues need to be fixed, but having visibility helps              |
| batect         | The script executable to run batect locally.                                    |
| batect.yml     | The batect configuration for running the lambda and tests.                      |
| Jenkinsfile    | CI call to buildLambda function in the build pipeline                           |
| requirements-dev.txt| The Python package dependencies used for development                       |
| requirements.txt| The Python packages used to run the lambda                                     |

### A note on Batect

[Batect](https://batect.dev/) is used extensively to centralise and simplify container tasks.

It is highly recommended you familiarise yourself with the included bundles reference in this batect.yml

`./batect --list-tasks`

For example, [repo: git@github.com:hmrc/infrastructure-pipeline-lambda-build.git](https://github.com/hmrc/infrastructure-pipeline-lambda-build/blob/main/batect-bundle.yml)

You can quickly use these tasks to run standardised linting and scanning of your code, as defined below.

## Building the Lambda and running the tests

### Building the Image

`./batect build`

### Linting and Security Scanning

`./batect lint`

and

`./batect scan`

### Tests

Too run *all* unit and integration tests `./batect test`

Unit tests can be run with `./batect test:unit`

Integration tests can be run with `./batect test:integration`

Add your tests to th### A note on Batect

[Batect](https://batect.dev/) is used extensively to centralise and simplify container tasks.

It is highly recommended you familiarise yourself with the included bundles reference in this batect.yml

`./batect --list-tasks`

For example, [repo: git@github.com:hmrc/infrastructure-pipeline-lambda-build.git](https://github.com/hmrc/infrastructure-pipeline-lambda-build/blob/main/batect-bundle.yml)

You can quickly use these tasks to run standardised linting and scanning of your code, as defined below.

## Building the Lambda and running the tests

### Building the Image

`./batect build`

### Linting and Security Scanning

`./batect lint`

and

`./batect scan`

### Tests relevant folder to execute them in these containers.

## Building and Deploying the Lambda

The [`buildLambda`](https://github.com/hmrc/infrastructure-pipeline-lambda-build/blob/main/vars/buildLambda.groovy)
Jenkins function takes care of building, testing and pushing the Lambda to ECR.

You can see this [example Lambda deployed here](https://github.com/hmrc/webops-terraform/blob/main/components/aws-lambda-example-project/main.tf).

However, most production lambdas will be deployed [from tenant-compute-terraform, like this.](https://github.com/hmrc/tenant-compute-terraform/tree/main/components/ecs-deployer-lambda).

## Dockerfile Structure

There are 2 distinct Dockerfiles:
- containers/dev/ is for local work and testing. It contains all of the dev requirements.
    - modify this with the requirements-dev.txt and any other tools you need.
- containers/release/ is used by the deployment process to host the lambda
    - ensure your runtime dependencies are defined in pyproject.toml

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
