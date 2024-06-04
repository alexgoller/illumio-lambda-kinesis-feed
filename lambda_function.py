import boto3
import json
import logging
import signal
import os
from datetime import datetime, timezone, timedelta
from illumio import *
from botocore.exceptions import ClientError


LOGGER = logging.getLogger()
LOGGER.setLevel(logging.INFO)

kinesis_client = boto3.client('kinesis')
kinesis_arn    = os.environ.get('KINESIS_ARN')

def get_secret():

    if os.environ.get('pce_secret'):
        secret_name = os.environ.get('pce_secret')
    
    if os.environ.get('aws_region'):
        region_name = os.environ.get('aws_region')

    # Create a Secrets Manager client
    session = boto3.session.Session()
    client = session.client(
        service_name='secretsmanager',
        region_name=region_name
    )

    try:
        get_secret_value_response = client.get_secret_value(
            SecretId=secret_name
        )
    except ClientError as e:
        # For a list of exceptions thrown, see
        # https://docs.aws.amazon.com/secretsmanager/latest/apireference/API_GetSecretValue.html
        raise e

    # Decrypts secret using the associated KMS key.
    secret = get_secret_value_response['SecretString']
    return(secret)

def lambda_handler(event, context):
    # Your custom message
    """
    param pce_api_user: API user name
    param pce_api_key: API key
    param pce_org: PCE org
    param pce_fqdn: PCE FQDN
    param pce_port: PCE port
    """

    pce_data = json.loads(get_secret())

    try:
        # PCE API setup
        pce = PolicyComputeEngine(pce_data['pce_api_host'], port=int(pce_data['pce_api_port']), org_id= int(pce_data['pce_api_org']))
        pce.set_credentials(pce_data['pce_api_key'], pce_data['pce_api_secret'])
        if pce.check_connection():
            print("PCE connection established")
        else:
            print("PCE connection failed")

        current_time_utc = datetime.now(timezone.utc)
        time_minus_5_minutes = current_time_utc - timedelta(minutes=5)
        time_rfc3339 = time_minus_5_minutes.isoformat()

        # use timestamp[gte] to poll only since the last poll operation
        events = pce.events.get(params = {'max_results': 100, "timestamp[gte]": time_rfc3339 })
        print(events)

        for event in events:
            print(event)
            partitionKey = event.href
            print(event.href)
            stream_name = kinesis_arn.split(':')[-1].split('/')[-1]
            event_data = event.to_json()
            print(f'Event type: {type(event)}')
            print(f'Event data type: {type(event_data)}')

            # Send event to Kinesis
            response = kinesis_client.put_record(
                StreamName=stream_name,
                Data=json.dumps(event_data).encode('utf-8'),
                PartitionKey = partitionKey
            )
            
            print(f'Event sent to Kinesis: {response}')
            LOGGER.info(f'Success - exported event to kinesis: {event}')

        start_date = time_rfc3339
        end_date = current_time_utc.isoformat()

        traffic_query = TrafficQuery.build(
            start_date = start_date,
            end_date = end_date,
            include_services = [],
            exclude_services = [
                { "port": 53 },
                { "port": 88 },
                { "port": 137 },
                { "port": 138 },
                { "port": 139 },
                { "port": 5355 },
                { "proto": 58 },
                { "proto": "udp" },
                { "proto": "icmp" }
            ],
            exclude_destinations = [
                {
                    "transmission": "broadcast"
                },
                {
                    "transmission": "multicast"
                }
            ],
            max_results = 10000
        )

        all_traffic = pce.get_traffic_flows_async(
            query_name = 'all-traffic',
            traffic_query = traffic_query,
        )

        for res in all_traffic:
            event = res.to_json()
            src_ip = event['src']['ip']
            dst_ip = event['dst']['ip']
            first_detected = event['timestamp_range']['first_detected']
            last_detected = event['timestamp_range']['last_detected']
            partitionKey = f"{src_ip}-{dst_ip}-{first_detected}-{last_detected}"
            
            stream_name = kinesis_arn.split(':')[-1].split('/')[-1]

            response = kinesis_client.put_record(
                StreamName=stream_name,
                Data=json.dumps(event).encode('utf-8'),
                PartitionKey = partitionKey
            )

            print(f'Traffic flow sent to Kinesis: {response}')
            LOGGER.info(f'Success - exported traffic flow to kinesis: {event}')

        return {
            'statusCode': 200,
            'body': json.dumps('Events sent to Kinesis successfully')
        }
    except Exception as e:
        LOGGER.info('Failed - exception thrown during processing: {}'.format(e))

def timeout_handler(_signal, _frame):
    '''Handle SIGALRM'''
    raise Exception('Time exceeded')

signal.signal(signal.SIGALRM, timeout_handler)

