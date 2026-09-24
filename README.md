
# aws-autorecycle

This is a Lambda resource which starts a relevant step function when invoked by a relevant Cloudwatch event. It checks that the component is recyclable, and if it is, triggers the step function with the relevant strategy to recycle the component. 


## Project Structure

The structure of this project, along with steps to build the Lambda and run the tests locally was copied from the example project in the [aws-lambda-example-project](https://github.com/hmrc/aws-lambda-example-project/tree/python/3.11) repo. 


| Location       | Description                                                                       |
|----------------|-----------------------------------------------------------------------------------|
| containers     | The Dockerfiles for development and release builds                                |
| src/           | The code for the Lambda is contained in `src`.                                    |
| terraform/     | Terraform configuration that is deployed by `webops-terraform`.                   |
| tests/         | Integration and unit tests.                                                       |
| .gitignore     | Every repo should have one.                                                       |
| .trivyignore   | Not all trivy issues need to be fixed, but having visibility helps                |
| compose.yaml   | Docker compose configuration for testing this lambda locally                      |
| Taskfile.yaml  | Taskfile config, used for shorthandedly running commands for linting and testing  |
| Jenkinsfile    | CI call to buildLambda function in the build pipeline                             |

## The Shared Pipeline: Infrastructure Pipeline Lambda Build

This repository uses the [infrastructure-pipeline-lambda-build](https://github.com/hmrc/infrastructure-pipeline-lambda-build/).

It provides shared tooling for:
- Docker-based Lambda builds
- Testing and linting
- CI/CD integration (Jenkins & Terraform)


`./task --list`

## Building the Lambda and running the tests

### Building the Image

`./task build`

### Linting and Security Scanning

`./task lint`

and

`./task scan`

### Tests

`./task test` runs the unit and integration tests and type-checks the source.

## Building and Deploying the Lambda

The [`buildLambda`](https://github.com/hmrc/infrastructure-pipeline-lambda-build/blob/main/vars/buildLambda.groovy)
Jenkins function takes care of building, testing and pushing the Lambda to ECR.

You can see this [example Lambda deployed here](https://github.com/hmrc/webops-terraform/blob/main/components/aws-lambda-example-project/main.tf).

However, most production lambdas will be deployed [from tenant-compute-terraform, like this.](https://github.com/hmrc/tenant-compute-terraform/tree/main/components/ecs-deployer-lambda).

## Dockerfile Structure

We now inherit Dockerfiles centrally from the above linked repository.

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
