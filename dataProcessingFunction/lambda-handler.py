import boto3
import base64
import json
import os


def main(event, context):
    output = []
    success = 0
    failure = 0
    client = boto3.client('sns')

    for record in event['records']:

        try:
            output.append({'recordId': record['recordId'], 'result': 'Ok'})
            response = client.publish(
                TopicArn=os.getenv('TOPIC_ARN'),
                Message=json.dumps(base64.b64decode(record['data']).decode("utf-8"))
            )
            success += 1

        except Exception:
            output.append({'recordId': record['recordId'], 'result': 'DeliveryFailed'})
            failure += 1

    print('Successfully delivered {0} records, failed to deliver {1} records'.format(success, failure))

    return {'records': output}
