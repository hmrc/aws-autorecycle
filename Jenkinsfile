#!/usr/bin/env groovy

buildLambda(
  prepareStage: { env ->
    sh("./batect build-dev-image")
  },
  repo_name: "aws-autorecycle",
  validate_terraform: true
)
