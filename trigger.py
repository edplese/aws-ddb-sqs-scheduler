import boto3
import json
import os

client = boto3.client('lambda')

partition_count = int(os.environ['PARTITION_COUNT'])
function_name = os.environ['FUNCTION_NAME']


def lambda_handler(event, context):
    for i in range(partition_count):
        client.invoke(
            FunctionName=function_name,
            InvocationType='Event',
            Payload=json.dumps({'partition': '%0x' % i})
        )
