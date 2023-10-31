# monitor-autorecycle-lambda

Check the status of a giveb component's Auto-Scaling Group (ASG).
- Look up the ASG by finding one that contains the component name.
- Return `recycle_success` if all the instances in the ASG are `Healthy` & `InService`.

## Inputs

These are expected fields in the input to the lambda (the `event`):

| Name          | Purpose                                                                          | Example value            |
| ------------- | -------------------------------------------------------------------------------- | ------------------------ |
| `component`   | the component to check.  The ASG name should _contain_ this string for a match.  | `"public_routing_proxy"` |


## Outputs

The incoming `event` is modified and returned back with these additional values:

| Name                    | Purpose                                | Example value          |
| -------------------     | -------------------------------------- | ---------------------- |
| `recycle_success`       | was the autorecycle successful         | `true`                 |
| `status`                | same as `recycle_success`, but in str  | `"fail"`               |
| `message_content.text`  | human-friendly message                 | `"Autorecycling has successfully completed"` |
| `message_content.color` |                                        | `"danger"`             |

## Context

This lambda is invoked by the `autorecyle` step function: https://github.com/hmrc/webops-terraform/blob/master/components/autorecycle/main.tf

