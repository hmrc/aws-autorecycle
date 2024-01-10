TERRAFORM_VERSION = 1.3.10

build:
	docker build -t $(TAG) .

lambda-local:
	./batect lambda-local

test-lint:
	./batect test-lint

test-integration:
	./batect test-integration

test-unit:
	./batect test-unit

fix-lint:
	./batect fix-lint

.PHONY: test
test: test-unit test-integration

terraform-fmt:
	docker run -v ${PWD}:/src -w /src/terraform hashicorp/terraform:$(TERRAFORM_VERSION) fmt -recursive

terraform-fmt-check:
	docker run -v ${PWD}:/src -w /src/terraform hashicorp/terraform:$(TERRAFORM_VERSION) fmt -recursive -check

terraform-validate:
	docker run --rm -v ${PWD}:/src -v ${HOME}/.ssh:/root/.ssh -w /src/terraform hashicorp/terraform:$(TERRAFORM_VERSION) init -backend=false
	docker run --rm -v ${PWD}:/src -v ${HOME}/.ssh:/root/.ssh -w /src/terraform hashicorp/terraform:$(TERRAFORM_VERSION) validate

terraform-security-check: clean
	docker run --rm -u 0 -v ${PWD}:/src tfsec/tfsec:latest /src/terraform

# Clean runs in a container to avoid file permission errors on Jenkins
clean:
	docker run --rm -v ${PWD}:/src -w /src/terraform --entrypoint "/bin/sh" hashicorp/terraform:$(TERRAFORM_VERSION) -c "rm -rf /src/terraform/.terraform*"
