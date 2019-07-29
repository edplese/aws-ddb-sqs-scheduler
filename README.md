# aws-ddb-sqs-scheduler

This is an ad-hoc scheduler for AWS. A schedule is created by calling a Lambda function and passing in a payload and trigger time and then at that time the payload is made available on an SQS queue.

The primary scheduling mechanism used is the `DelaySeconds` feature of SQS. This has a maximum delay of 15 minutes and DynamoDB is used for storage longer than this.

## Goals
- High capacity
- ~1 second accuracy
- Unlimited delay for schedule
- Minimal latency when many events are scheduled for the same time
- At least once triggering of schedules
- Serverless
- SAM/CF with zero external dependencies

## Scheduling
1. A schedule is created by invoking the Lambda function and passing in the trigger timestamp in epoch seconds any string data:
`{"timestamp": 1564378340, "data": "some payload"}`
2. If the timestamp is less than 15 minutes in the future (the max delay for SQS) then a message is sent to SQS with a `DelaySeconds` of the calculated delay for the message.
3. Otherwise the event is written to DynamoDB with a random partition as the hash key and the timestamp concatenated with a random string as the range key. Multiple partitions are used to avoid the 3k/second capacity limit per hash key in DynamoDB.
4. Every 10 minutes a Lambda function is triggered for each partition to query DynamoDB for schedules triggering within the next 15 minutes, send them to SQS, and then delete them from DynamoDB.

## Deployment
```
aws cloudformation package \
        --template-file template.yml \
        --s3-bucket <your-s3-bucket> \
        --output-template-file package.yml
aws cloudformation deploy \
        --capabilities CAPABILITY_AUTO_EXPAND CAPABILITY_IAM \
        --stack-name aws-ddb-sqs-scheduler \
        --template-file package.yml \
        --parameter-overrides PartitionCount=1
```

## Future Work
- Performance testing
- Improve input validation and error handling
- Publish to Service Application Repository
- Dynamic partioning
- Add concurrency to `feed.py`