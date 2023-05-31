#!/usr/bin/env python3

from pymongo import MongoClient
import datetime
import random
import time
import os
import uuid
import boto3
import json

mongodb_secrets_arn = os.environ.get('MONGODB_SECRET_ARN')
mongodb_host = os.environ.get('MONGODB_HOST')
mongodb_user = os.environ.get('MONGODB_USER')
mongodb_db = os.environ.get('MONGODB_DB')
mongodb_collection = os.environ.get('MONGODB_COLLECTION')


secretsmanager = boto3.client('secretsmanager')
response = secretsmanager.get_secret_value(
    SecretId=mongodb_secrets_arn  
)

# The secret is stored as a JSON string, so we parse it into a dictionary
secrets = json.loads(response['SecretString'])

# Now we can retrieve the password from the dictionary
mongodb_password = secrets['password']
# Create MongoDB connection string
mongo_uri  = f"mongodb+srv://{mongodb_user}:{mongodb_password}@{mongodb_host}/{mongodb_db}"

cluster = MongoClient(mongo_uri)  # replace with your connection string

wait_time = random.uniform(0.01, 15)

# Sleep for the random duration
time.sleep(wait_time)

# def generate_random_documents(num_docs, request_id):


#     docs = []
#     for _ in range(num_docs):
#         doc = {
#             "_id": str(uuid.uuid4()) + "-" + request_id,  # Assign a unique _id for each document
#             "sensor_id": "sensor_" + str(random.randint(1, 100)),       
#             "sensor_id": "sensor_" + str(random.randint(1, 100)),
#             "location": {
#                 "latitude": round(random.uniform(-90, 90), 6),
#                 "longitude": round(random.uniform(-180, 180), 6)
#             },
#             "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
#             "measurements": {
#                 "temperature": round(random.uniform(-50, 50), 2),
#                 "humidity": round(random.uniform(0, 100), 2),
#                 "soil_moisture": round(random.uniform(0, 100), 2),
#                 "light_intensity": round(random.uniform(0, 100), 2)
#             }
#         }
#         docs.append(doc)

#     return docs

def generate_synthetic_data(num_records, request_id):
    data = []

    for _ in range(num_records):
        current_time = datetime.now().isoformat()
        record = {
            "_id": str(uuid.uuid4()) + "-" + request_id,  # Assign a unique _id for each document
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
          # Simulating time decreasing by 1 minute for each record

    return data



def lambda_handler(event, context):

    db = cluster[mongodb_db]
    collection = db[mongodb_collection]
    # Add artificial wait time to avoid hammering effect

    for _ in range(100):

        random_int = random.randint(80, 200)
        docs_to_insert = generate_synthetic_data(random_int, context.aws_request_id)
        collection.insert_many(docs_to_insert, ordered=False)
        wait_time = random.uniform(0.05, 0.1)
        time.sleep(wait_time)

    return {
        'statusCode': 200,
        'body': 'Successfully inserted documents!'
    }
