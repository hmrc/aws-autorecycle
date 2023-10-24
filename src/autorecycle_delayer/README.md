
# aws-autorecycle-delayer-lambda

Lambda to determine if recycling should continue or wait based on the recycle window specified in the lambda Event.


### Input

```
{
    'component': 'component_name',
    'recycle_window': '04:00:00, 05:30:00'
}
```

### Output

```
{
    "time_wait": "2018-03-22T10:45:00+00:00",
    "wait": True
}
```
or
```
{
    "wait": False
}
```

### How it works

* In the above event, the component would be permitted to recycle between 04:00:00 and 05:30:00.  
* If the time now is within the recycle window the lambda will return:  
```
{
    "wait": False
}
``` 
* If the time now is earlier than the recycle window the lamda will return `'wait': True` and the start time of the next recycle window:  
```
{
    "time_wait": "2018-03-22T10:45:00+00:00",
    "wait": True
}
```
* If the time now is greater than the recycle window the time returned will be the start of the recycle window the next day.
* The recycle window can span midnight, setting the recycle window to be between 8pm and 6am, ie.  
```
{
    'component': 'component_name',
    'recycle_window': '20:00:00, 06:00:00'
}
```

### Development
0. `make setup`
1. `make security_checks`
2. `make test`
3. `make clean`

### Using Docker
0. `make ci_docker_build`
1. `make ci_setup`
2. `make ci_security_checks`
3. `make ci_test`
4. `make clean`
