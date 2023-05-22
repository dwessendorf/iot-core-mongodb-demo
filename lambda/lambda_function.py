#!/usr/bin/env python3

from pymongo import MongoClient
import random
import time

def lambda_handler(event, context):
    mongo_uri = os.environ.get('MONGODB_URI')
    cluster = MongoClient(mongo_uri) # replace with your connection string
    db = cluster["test"]
    collection = db["test"]

    for _ in range(1000):  # adjust this based on your requirements
        doc = {
            "sensor_id": "sensor_" + str(random.randint(1, 100)),
            "location": {
                "latitude": round(random.uniform(-90, 90), 6),
                "longitude": round(random.uniform(-180, 180), 6)
            },
            "timestamp": time.strftime('%Y-%m-%dT%H:%M:%SZ', time.gmtime()),
            "measurements": {
                "temperature": round(random.uniform(-50, 50), 2),
                "humidity": round(random.uniform(0, 100), 2),
                "soil_moisture": round(random.uniform(0, 100), 2),
                "light_intensity": round(random.uniform(0, 100), 2)
            }
        }
        collection.insert_one(doc)

    return {
        'statusCode': 200,
        'body': 'Successfully inserted documents!'
    }
