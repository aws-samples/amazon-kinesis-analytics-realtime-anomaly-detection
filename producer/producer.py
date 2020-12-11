import boto3
import random
import time
import json
import string
import numpy as np
import botocore.exceptions


# Generate Sensor ID
def get_random_string(length):
    letters = string.ascii_lowercase
    return ''.join(random.choice(letters) for i in range(length))


def main (stream_name):
    client = boto3.client('kinesis', region_name='eu-central-1')

    # Generate data record
    record = {
        "sensor_id": get_random_string(30),
        "temperature": 0.0,
        "rpm": "1500",
        "in_service": True,
    }

    # Generate data records with normal distribution
    mu = 70.0
    sigma = 4.0
    data = np.random.randn(100000) * sigma + mu
    i=0

    while True:
        # Replace temperature with record from normal distribution dataset
        record['temperature'] = data[i]

        # Ingest data into Kinesis with random partition key
        try:
            response = client.put_record(
                StreamName=stream_name,
                Data=json.dumps(record),
                PartitionKey=str(random.randint(1, 9999))
            )
        except botocore.exceptions.ClientError as error:
            raise error

        print(f"Record sent! Temp: {record['temperature']}", )

        # If end of data set is reached start from the beginning
        if i >= 99999:
            i=0
        else:
            i=i+1

        # Throttle data ingestion
        time.sleep(0.2)


if __name__ == '__main__':
    main('anomaly-detection-data-streams-input-data-stream')
