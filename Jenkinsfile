#!/usr/bin/env groovy

buildLambda(
  prepareStage: { env ->
    sh("cat ${SSH_KEY_PATH} > ${HOME}/.ssh/id_rsa")
    sh("./batect build-dev-image")
  },
  repo_name: "aws-autorecycle",
  validate_terraform: true
)
