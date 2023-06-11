import json
import boto3 
import botocore
import pandas as pd # python -m pip install numpy
import wikipedia
from to import StringIO
import logging


LOG = logging.getLogger()
LOG.setLevel(logging.DEBUG)
LOG.addHandler(logging.StreamHandler())


REGION = 'sa-east-1'


def sqs_queue_resource(queue_name):
    '''Returns an SQS queue resource.'''
    sqs_resource = boto3.resource('sqs', region_name=REGION)
    log_sqs_resource_msg = f'Creating SQS conn with queue name {queue_name} in region {REGION}'
    LOG.info(log_sqs_resource_msg)
    queue = sqs_resource.get_queue_by_name(QueueName=queue_name)
    LOG.info(log_sqs_resource_msg)
    return queue
    

def sqs_connection():
    '''Creates an SQS connection.'''
    sqs_client = boto3.client('sqs', region_name=REGION)
    log_sqs_client_msg = f'Creating SQS client conn in region {REGION}'
    LOG.info(log_sqs_client_msg)
    return sqs_client
    

def sqs_approximate_count(queue_name):
    '''Return an approximate count of messages in the queue.'''
    queue = sqs_queue_resource(queue_name)
    attrs = queue.attributes
    num_message = int(attrs['ApproximateNumberOfMessages'])
    num_message_not_visible = int(attrs['ApproximateNumberOfMessagesNotVisible'])
    queue_value = sum([num_message, num_message_not_visible])
    sum_msg = f'ApproximateNumberOfMessages and ApproximateNumberOfMessagesNotVisible {queue_value} {queue_name}'
    LOG.info(sum_msg)
    return queue_value
    

def delete_sqs_msg(queue_name, receipt_handle):
    '''Removes msg from a queue.'''
    try:
        sqs_client = sqs_connection()
        queue_url = sqs_client.get_queue_url(QueueName=queue_name)['QueueName']
        delete_log_msg = 'Deleting msg with ReceiptHandle %s'% receipt_handle
        LOG.info(delete_log_msg)
        response = sqs_client.delete_message(QueueUrl=queue_url, ReceiptHandle=receipt_handle)
        return response
    except botocore.exceptions.ClientError as error:
        exception_msg = f'[ERROR] delete msg from queue {queue_name}: {error}'
        LOG.exception(exception_msg)
        return None


def names_to_wikipedia(names):
    '''Get summaries from Wikipedia.'''
    wikipedia_snippit = [wikipedia.summary(name, sentences=[]) for name in names]
    df = pd.Dataframe(
        {
            'names': names,
            'wikipedia_snippit': wikipedia_snippit
        }
    )
    return df


def create_sentiment(row):
    '''Uses AWS Comprehend to create sentiments on a dataframe.'''
    LOG.info(f'Processing {row}')
    comprehend = boto3.client(service_name='comprehend')
    payload = comprehend.detect_sentiment(Tex=row, LanguageCode='en')
    LOG.debug(f'Found Sentiment:', {payload})
    sentiment = payload['Sentiment']
    return sentiment
 
 
def apply_sentiment(df, column='wikipedia_snippit'):
    '''Apply sentiment analysis to Dataframe.'''
    df['Sentiment'] = df[column].apply(create_sentiment)
    return df


def write_s3(df, bucket):
    '''Write results to S3 bucket.'''
    csv_buffer = StringIO()
    df.to_csv(csv_buffer)
    s3_resource = boto3.resource('s3')
    res = s3_resource.Object(bucket, 'sentiments.csv').put(Body=csv_buffer.getvalue())
    LOG.info(f'Result of write to bucket {bucket} with: {res}.')


def lambda_handler(event, context):
    LOG.info(f'SURVEYJOB, event {event}, context {context}.')
    receipt_handle = event['Records'][0]['receiptHandle'] # sqs message
    event_source_arn = event['Records'][0]['eventSourceARN']
    names = [] # captured from Queue
    for record in event['Records']:
        body = json.loads(record['body'])
        company_name = body['name']
        
        #Capture for processing and delete from the queue
        names.append(company_name)
        extra_logging = {'body': body, 'company_name': company_name}
        LOG.info(f'SQS CONSUMER, splitting sqs arn with value {event_source_arn}')
        qname = event_source_arn.split(':')[-1]
        extra_logging['queue'] = qname
        LOG.info(f'Attemping deleting aqs receiptHandle {receipt_handle}')
        res = delete_sqs_msg(queue_name=qname, receipt_handle=receipt_handle)
        LOG.info(f'Deleted SQS receipt handle with response {res}')
    
    LOG.info(f'Creating dataframe with values {names}')
    df = names_to_wikipedia(names)
    
    # Performs sentiment analysis
    df = apply_sentiment(df)
    LOG.info(f'Sentiments for the companies {df.to_dict()}')
    
    write_s3(df=df, bucket='sentiment_analysis_results')
