import json
import boto3
import logging

logger = logging.getLogger()
logger.setLevel(logging.INFO)


class StepFunctionEvent(object):
    

    def __init__(self):
        self.client = boto3.client('stepfunctions')
        self.default_success_msg = {'message':'success'}
        self.default_error_msg = {'message':'error'}

    def send_success(self, json_msg, task_token):
        msg = self.default_error_msg if not json_msg else json_msg
        response = self.client.send_task_success(
            taskToken=task_token,
            output=json.dumps(msg)
        )
        return response

    def send_error(self, json_msg, task_token):
        msg = self.default_error_msg if not json_msg else json_msg
        response = self.client.send_task_failure(
            taskToken=task_token,
            error=json.dumps(msg)
        )
        return response


def lambda_handler(event, context):
    '''Entrypoint
    See https://github.com/aws-samples/automation-ml-step-data-pipeline
    '''
    
    logger.info(event)
    task_token = json.loads(event['Records'][0]['body'])['taskToken']
    _instance = StepFunctionEvent()
    try:
        _instance.send_success(json_msg=None, task_token=task_token)
        return {'statusCode': 200, 'body': json.dumps('Success')}
    except Exception as e:
        _instance.send_error(json_msg=None, task_token=task_token)
        return {'statusCode': 500, 'body': json.dumps(e)}
