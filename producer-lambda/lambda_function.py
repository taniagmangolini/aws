import json
import boto3 # pip install boto3 --target .. 
import logging
#from pythonjsonlogger import jsonlogger # pip install python-json-logger --target ..


DYNAMODB = boto3.resource('dynamodb')
TABLE = 'testtable'
QUEUE = 'producer'
SQS = boto3.client('sqs')

LOG = logging.getLogger()
LOG.setLevel(logging.INFO)
logHandler = logging.StreamHandler()
#formatter = jsonlogger.JsonFormatter()
#logHandler.setFormatter(formatter)
LOG.addHandler(logHandler)


def scan_table(table):
    '''Scans table and return results'''
    
    LOG.info(f'Scanning table {table} ...')
    producer_table = DYNAMODB.Table(table)
    response = producer_table.scan()
    items = response['Items']
    LOG.info(f'Found {len(items)} items.')
    return items


def send_sqs_message(msg, queue_name, delay=0):
    '''Send SQS message'''
    
    queue_url = SQS.get_queue_url(QueueName=queue_name)['QueueUrl']
    queue_send_log_msg = 'Send message to queue url: %s, with body: %s'%(queue_url, msg)
    LOG.info(queue_url, msg)
    response = SQS.send_message(
        QueueUrl=queue_url,
        MessageBody=json.dumps(msg),
        DelaySeconds=delay
    )
    queue_send_log_msg = 'Message response: %s for queue url:: %s'%(response, queue_url)
    LOG.info(queue_send_log_msg)
    return response


def send_emissions(table, queue_name):
    '''Scan table and Send emissions to the queue'''
    
    items = scan_table(table=table)
    for item in items:
        LOG.info(f'Sending item {item} to queue {queue_name}...')
        response = send_sqs_message(item, queue_name=queue_name)
        LOG.debug(response)


def lambda_handler(event, context):
    '''Entrypoint'''
    
    extra_logging = {'table': TABLE, 'queue': QUEUE}
    LOG.info(f'event {event}, context {context}', extra=extra_logging)
    send_emissions(table=TABLE, queue_name=QUEUE)
