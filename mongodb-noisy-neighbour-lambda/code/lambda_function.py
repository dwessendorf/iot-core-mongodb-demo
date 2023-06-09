import os
import time
import boto3
import pymongo
import json
import datetime
import random
import pprint


mongodb_secrets_arn = os.environ.get('MONGODB_SECRET_ARN')
mongodb_host = os.environ.get('MONGODB_HOST')
mongodb_user = os.environ.get('MONGODB_USER')
mongodb_db = os.environ.get('MONGODB_DB')
mongodb_collection = os.environ.get('MONGODB_COLLECTION')
NR_OF_EXECUTIONS = 1000


# Add vehicleid here, it can be passed from the event or as an environment variable
vehicle_id = os.environ.get('VEHICLE_ID')

# Create a Secrets Manager client
secretsmanager = boto3.client('secretsmanager')
response = secretsmanager.get_secret_value(
    SecretId=mongodb_secrets_arn  
)

# The secret is stored as a JSON string, so we parse it into a dictionary
secrets = json.loads(response['SecretString'])

# Now we can retrieve the password from the dictionary
mongodb_password = secrets['password']

# Create MongoDB connection string
#mongodb_connection_string = f"mongodb+srv://{mongodb_user}:{mongodb_password}@{mongodb_host}/{mongodb_db}?readPreference=secondary&readPreferenceTags=nodeType:ANALYTICS&readConcernLevel=local"
mongodb_connection_string = f"mongodb+srv://{mongodb_user}:{mongodb_password}@{mongodb_host}/{mongodb_db}?readPreference=secondary&readConcernLevel=local"
# Create MongoClient


print(mongodb_connection_string)

client = pymongo.MongoClient(mongodb_connection_string)
    

def lambda_handler(event, context):

    # Select the database
    db = client[mongodb_db]
    
    # Select the collection
    collection = db[mongodb_collection]

    current_time = datetime.datetime.now()
    end_time = current_time + datetime.timedelta(seconds=900)
    # Query the collection
    
    while current_time < end_time:
        # Get current time

        vehicle_id = random.randint(1,50000)

        # Get the current time
        current_time = datetime.datetime.now()

        # Calculate the time five minutes ago
        one_minute_ago = current_time - datetime.timedelta(minutes=15)

        # Convert the time to ISO format
        one_minute_ago_iso = one_minute_ago.isoformat()

        # Run the query
        results = collection.aggregate([
                {"$match": {
                    "ts": {"$gte": one_minute_ago_iso},
                    "vehicleid": vehicle_id
                }},
                {"$lookup": {
                    "from": "agricol",
                    "localField": "vehicleid",
                    "foreignField": "vehicleid",
                    "as": "vehicle_info"
                }},
                {"$unwind": "$vehicle_info"},
                {"$group": {
                    "_id": None,
                    "avg_speed": {"$avg": "$drivingspeed"},
                    "avg_vehicle_speed": {"$avg": "$vehicle_info.drivingspeed"}
                }}
            ]
        )

        results_list = list(results)  # Convert the Cursor to a list
        query_time = datetime.datetime.now() - current_time

        # Initialize variables
        avg_speed = 0
        avg_vehicle_speed = 0

        # Get the average speed and vehicle speed from the query results
        for result in results_list:
            avg_speed = result['avg_speed']
            avg_vehicle_speed = result['avg_vehicle_speed']
    
        print(f"{datetime.datetime.now()}: VehicleID: {vehicle_id}, Avg. speed (last minute): {round(avg_speed,2)}, Avg. speed (total): {round(avg_vehicle_speed,2)}, Query time: {query_time}" )

        # Sleep for 5 seconds
        time.sleep(5)
        current_time = datetime.datetime.now()
