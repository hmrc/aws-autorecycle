
# aws-autorecycle-scale-asg-lambda


This Lambda will accept a payload event such as which is sent from the aws-autorecycle-inoke-stepfunctions-lambda: 

``{
  "component": "component_name_a",
  "account_id": "1234",
  "success_channel": "event-<environment>-issues",
}``

Ensure the component you want to recycle has the relevant [configuration file](https://github.com/hmrc/aws-autorecycle-invoke-stepfunctions-lambda/blob/master/autorecycle_invoke_stepfunctions/config/asgs.json "aws-autorecycle-inoke-stepfunctions-lambda").

**IF YOU NEED TO RECYCLE A COMPONENT WITH A SUFFIX OF `_<AZ>`**

**THEN ADD ONLY ONE TO THE ABOVE FILE OR INSTANCES WILL BE RECYCLED AT THE SAME TIME**

This is beacuse this lambda handles ASG's accross multiple availability zones such as like this [example](https://github.com/hmrc/aws-autorecycle-invoke-stepfunctions-lambda/blob/master/autorecycle_invoke_stepfunctions/config/asgs.json#L58 "Example component with underscore")

When this lambda is invoked in a loop by the step function and it will show Cloudwatch logs similar to this as it checks and scales instances in an ASG which need to be recycled.
````
[INFO]  Checking latest scaling activity on this ASG: "example_a"
[INFO]  Checking latest scaling activity on this ASG: "example_b"
[INFO]  Executing scaling policy:recycle-scale-in on this ASG: "example_a"
[DEBUG] Scaling activity is progress...
[DEBUG] Initiating with the following event: {'sample': 'event'}
[INFO]  Checking latest scaling activity on this ASG: "example_a"
[INFO]  Checking latest scaling activity on this ASG: "example_b"
[INFO]  Initiating scale out policy
[INFO]  Executing scaling policy:recycle-scale-out on this ASG: "example_a"
[DEBUG] Initiating with the following event: {'sample': 'event'}
[INFO]  Checking latest scaling activity on this ASG: "example_a"
[INFO]  Checking latest scaling activity on this ASG: "example_b"
[INFO]  Autorecycling has successfully completed 
````
In order to use this lambda you must create a [scale in and scale out policy](https://github.com/hmrc/webops-terraform/blob/master/components/public-monolith-activemq/auto_scaling_policy.tf "Example scaling policy")
