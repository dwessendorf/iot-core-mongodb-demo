#!/usr/bin/env python3

from pymongo import MongoClient
import boto3
import random
import json
import os
import base64


mongodb_secrets_arn = os.environ.get('MONGODB_SECRET_ARN')
mongodb_host = os.environ.get('MONGODB_HOST')
mongodb_user = os.environ.get('MONGODB_USER')
mongodb_db = os.environ.get('MONGODB_DB')
mongodb_collection = os.environ.get('MONGODB_COLLECTION')
BATCH_SIZE = 50

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

def lambda_handler(event, context):
    db = cluster[mongodb_db]
    collection = db[mongodb_collection]
    #wait_time = random.uniform(0.01, 30)

    # Prepare the list of documents for bulk insertion
    documents = []

    # For each record in the Kinesis data
    for record in event['Records']:
        # Kinesis data is base64 encoded so decode here
        payload = base64.b64decode(record["kinesis"]["data"])
        data_items = json.loads(payload)

        # Iterate over the data items in the batch
        for data_item in data_items:
            # Append the data item to the list of documents
            documents.append(data_item)
            if len(documents) == BATCH_SIZE:
                # Insert the documents into MongoDB Atlas using insert_many
                result = collection.insert_many(documents)
                print('Status Code:', 'Acknowledged' if result.acknowledged else 'Not Acknowledged')
                print('Number of Documents Inserted:', len(result.inserted_ids))
                documents = []

    return {
        'statusCode': 200,
        'body': json.dumps('Done')
    }

