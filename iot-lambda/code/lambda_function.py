#!/usr/bin/env python3

import logging
from awscrt import io, mqtt, auth, http
from awsiot import mqtt_connection_builder
import time 
import json
import os
import random
from datetime import datetime, timedelta
import boto3
import atexit
import requests

# Define ENDPOINT, CLIENT_ID, PATH_TO_CERTIFICATE, PATH_TO_PRIVATE_KEY, PATH_TO_AMAZON_ROOT_CA_1, MESSAGE, TOPIC, and RANGE

logging.basicConfig(level=logging.INFO) 

RANGE = 5900
BATCH_SIZE = 100
SLEEP_INTERVAL = 0.01

TOPIC = os.environ.get('IOT_TOPIC')
logging.info("Environment variable TOPIC is; {TOPIC}")
CERTIFICATE_ID = os.environ.get("CERTIFICATE_ID")
logging.info( f"Environment variable CERTIFICATE_ID is; {CERTIFICATE_ID}")
CERTIFICATE_PATH = "/tmp/certificate.pem.crt"

PRIVATE_KEY_SECRET_ARN = os.environ['PRIVATE_KEY_SECRET_ARN']
logging.info( f"Environment variable PRIVATE_KEY_SECRET_ARN is; {PRIVATE_KEY_SECRET_ARN}")
PRIVATE_KEY_PATH = "/tmp/private_key.key"

AMAZON_ROOT_CA_1_DOWNLOAD_URL = "https://www.amazontrust.com/repository/AmazonRootCA1.pem"
AMAZON_ROOT_CA_1_PATH = "/tmp/AmazonRootCA1.pem"

response = requests.get(AMAZON_ROOT_CA_1_DOWNLOAD_URL)
if response.status_code == 200:
    with open(AMAZON_ROOT_CA_1_PATH, 'w') as file:
        file.write(response.content.decode())
    logging.info("Amazon Root CA certificate downloaded successfully.")
else:
    logging.info("Failed to download Amazon Root CA certificate.")

session = boto3.Session()
iot_c = session.client('iot')
endpoint = iot_c.describe_endpoint(endpointType = 'iot:Data-ATS')['endpointAddress']
cert = iot_c.describe_certificate(certificateId = CERTIFICATE_ID)['certificateDescription']['certificatePem']

secretsmanager = session.client("secretsmanager")
response = secretsmanager.get_secret_value(SecretId=PRIVATE_KEY_SECRET_ARN)
private_key = response["SecretString"]

with open(PRIVATE_KEY_PATH, "w") as key_file:
    key_file.write(private_key)

with open(CERTIFICATE_PATH,"w") as pem_file:
    pem_file.write(cert)

def generate_synthetic_data(num_records):
    data = []

    for _ in range(num_records):
        current_time = datetime.now().isoformat()
        record = {
            'ts': current_time,
            'vehicleid': random.randint(1, 100),
            'temperature': round(random.uniform(5.0, 40.0), 2),
            'operatingtime': random.randint(0, 1000),
            'fuelusage': round(random.uniform(0.0, 10.0), 2),
            'front_linkage_position': random.randint(0, 100),
            'drivingspeed': random.randint(0, 40),
            'enginestate': random.choice([0, 1]),
            'autopilot_system_state': random.choice([0, 1]),
            'engine_load': round(random.uniform(0.0, 100.0), 2),
            'latitude': round(random.uniform(-90.0, 90.0), 6),
            'longitude': round(random.uniform(-180.0, 180.0), 6),
            'altitude': round(random.uniform(0.0, 1000.0), 2),
            'engine_rotation': round(random.uniform(0.0, 3000.0), 2),
            'front_pme_shaft': round(random.uniform(0.0, 100.0), 2),
            'rear_linkage_position': random.randint(0, 100),
            'four_wheel_driving_state': random.choice(['Engaged', 'Disengaged']),
            'fuel_tank_level': random.randint(0, 100),
            'last_error_msg': random.choice(['No Error', 'Warning: Low Fuel Level', 'Error: Engine Overheating']),
            'engine_temperature': round(random.uniform(60.0, 110.0), 2),
            'connection_state': random.choice(['Connected', 'Disconnected']),
            'lte_connection_level': round(random.uniform(0.0, 100.0), 2),
            'mode': random.choice(['Normal', 'Eco', 'Work'])
        }


        if random.random() < 0.5:
            record.pop('operatingtime')
        if random.random() < 0.5:
            record.pop('autopilot_system_state')
        if random.random() < 0.5:
            record.pop('enginestate')
        if random.random() < 0.5:
            record.pop('temperature')


        if random.random() < 0.3:
            record.pop('front_linkage_position')
            record.pop('rear_linkage_position')
            record.pop('engine_rotation')
            record.pop('four_wheel_driving_state')
        if random.random() < 0.4:
            record.pop('front_pme_shaft')

        data.append(record)


    return data


def send_messages(mqtt_connection, messages):
    if not messages:
        return

    payload = json.dumps(messages)

    # Publish the batched messages
    try:
        mqtt_connection.publish(topic=TOPIC, payload=payload, qos=mqtt.QoS.AT_MOST_ONCE)
        logging.info("Message published successfully.")
    except Exception as e:
        logging.info("Error occurred while publishing the message:", str(e))


def connect_mqtt(client_id):

    # Spin up resources
    event_loop_group = io.EventLoopGroup(1)
    host_resolver = io.DefaultHostResolver(event_loop_group)
    client_bootstrap = io.ClientBootstrap(event_loop_group, host_resolver)



    mqtt_connection = mqtt_connection_builder.mtls_from_path(
                endpoint=endpoint,
                cert_filepath=CERTIFICATE_PATH,
                pri_key_filepath=PRIVATE_KEY_PATH,
                client_bootstrap=client_bootstrap,
                ca_filepath=AMAZON_ROOT_CA_1_PATH,
                client_id=client_id,
                clean_session=False,
                keep_alive_secs=6
                )
    logging.info("Connecting to {} with client ID '{}'...".format(
            endpoint, client_id))

    # Connect to MQTT broker
    logging.info(mqtt_connection.connect().result())
    return mqtt_connection



def lambda_handler(event, context):

    client_id = context.aws_request_id
    mqtt_connection = connect_mqtt(client_id)

    #while True:
    for i in range (RANGE):
        # Generate a single message
        logging.info(f"Batch Run:{i}")
        messages= generate_synthetic_data(BATCH_SIZE)

        send_messages(mqtt_connection, messages)
        messages = []  # Clear the batch


            # Sleep for the specified interval
        time.sleep(SLEEP_INTERVAL)

    mqtt_connection.disconnect().result()
    mqtt_connection = None

    return {
        'statusCode': 200,
        'body': 'Successfully sent messages'
    }


