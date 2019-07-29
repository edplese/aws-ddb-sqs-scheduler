import boto3
import os
import random
import string
import time

ddb = boto3.client('dynamodb')
sqs = boto3.client('sqs')

chars = string.ascii_letters + string.digits
partition_count = int(os.environ['PARTITION_COUNT'])

queue_url = os.environ['QUEUE_URL']
table_name = os.environ['TABLE_NAME']


def randstring(length):
    return ''.join(random.choice(chars) for n in range(length))


def lambda_handler(event, context):
    data = event['data']
    target_timestamp = event['timestamp']
    current_timestamp = int(time.time())
    delay = max(0, target_timestamp - current_timestamp)

    if delay <= 15 * 60:
        sqs.send_message(
            DelaySeconds=delay,
            MessageBody=data,
            QueueUrl=queue_url
        )
        return "scheduled"
    else:
        for i in range(3):
            try:
                partition = '%0x' % random.randint(0, partition_count - 1)
                key = str(target_timestamp) + '_' + randstring(8)
                ddb.put_item(
                    TableName=table_name,
                    Item={
                        'p': {'S': partition},
                        's': {'S': key},
                        'd': {'S': data}
                    },
                    ConditionExpression='attribute_not_exists(d)'
                )
                return "scheduled"
            except client.exceptions.ConditionalCheckFailedException:
                print("exception")
        return "not scheduled"
