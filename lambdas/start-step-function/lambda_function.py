import json
import os
import boto3
import logging


logger = logging.getLogger()
logger.setLevel(logging.INFO)


STEP_FUNCTION_CLIENT = boto3.client('stepfunctions')
S3_CLIENT = boto3.client('s3')


def process_line(line, key, bucket):
    '''Start a state machine to process the line data.'''

    input= {
        'product': line.split(',')[0],
        'category': line.split(',')[1],
        'file': key,
        'bucket': bucket
    }
    response = STEP_FUNCTION_CLIENT.start_execution(
        stateMachineArn=os.environ['STATE_MACHINE_ARN'],
        input=json.dumps(input, indent=4)
    )


def lambda_handler(event, context):
    '''Process lines in the uploaded file.'''
    
    for record in event['Records']:
        logger.info(f'Record {record}')
        bucket = record['s3']['bucket']['name']
        key = record['s3']['object']['key']
        response = S3_CLIENT.get_object(Bucket=bucket, Key=key)
        lines = response['Body'].read().decode('utf-8').split('\n')
        for line in lines:
            logger.info(f'Line {line}')
            process_line(line, key, bucket)
