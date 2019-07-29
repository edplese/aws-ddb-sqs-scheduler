import boto3
import os
import time

ddb = boto3.client('dynamodb')
sqs = boto3.client('sqs')

queue_url = os.environ['QUEUE_URL']
table_name = os.environ['TABLE_NAME']

paginator = ddb.get_paginator('query')


# https://stackoverflow.com/questions/312443/how-do-you-split-a-list-into-evenly-sized-chunks
def chunks(l, n):
    """Yield successive n-sized chunks from l."""
    for i in range(0, len(l), n):
        yield l[i:i + n]


def lambda_handler(event, context):
    partition = event['partition']
    current_timestamp = int(time.time()) + 15 * 60
    print(current_timestamp)

    responses = paginator.paginate(
        TableName=table_name,
        KeyConditionExpression='p = :p AND s <= :s',
        ExpressionAttributeValues={
            ':p': {'S': partition},
            ':s': {'S': str(current_timestamp)}
        }
    )

    for response in responses:
        for chunk in chunks(response['Items'], 10):
            current = int(time.time())
            messages = [{
                'DelaySeconds': min(max(0, int(item['s']['S'][:10]) - current), 15 * 60),
                'Id': item['p']['S'] + '_' + item['s']['S'],
                'MessageBody': item['d']['S']
            } for item in chunk]

            sqs.send_message_batch(
                QueueUrl=queue_url,
                Entries=messages
            )

            deletes = [
                {'DeleteRequest': {'Key': {'p': item['p'], 's': item['s']}}}
                for item in chunk
            ]
            ddb.batch_write_item(RequestItems={table_name: deletes})
