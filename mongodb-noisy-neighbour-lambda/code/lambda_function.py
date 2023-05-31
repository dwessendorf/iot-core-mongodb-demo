import os
import time
import boto3
import pymongo
import json
import datetime


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
mongodb_connection_string = f"mongodb+srv://{mongodb_user}:{mongodb_password}@{mongodb_host}/{mongodb_db}"
# Create MongoClient

print(mongodb_connection_string)

client = pymongo.MongoClient(mongodb_connection_string)
    

def lambda_handler(event, context):

    # Select the database
    db = client[mongodb_db]
    
    # Select the collection
    collection = db[mongodb_collection]
    


    for i in range(NR_OF_EXECUTIONS):
        # Get current time

        # Get the current time
        current_time = datetime.datetime.now()

        # Calculate the time five minutes ago
        five_minutes_ago = current_time - datetime.timedelta(minutes=5)

        # Convert the time to ISO format
        five_minutes_ago_iso = five_minutes_ago.isoformat()

        # Define the query
        query = { "ts": { "$gte": five_minutes_ago_iso }, "vehicleid": int(vehicle_id) }
        #query = {  "vehicleid": int(vehicle_id) }
        #print("query:",query)
        query_time = (datetime.datetime.now() - current_time).total_seconds() * 1000
        #print(f"Query time: {query_time}  milliseconds")
        # Query the database
        results = collection.find(query)
        results_list = list(results)  # Convert the Cursor to a list
        #count = len(results_list)
        # print("count:", count)
        # if count > 1:
        #     print(results_list[1] )
        # #print("results:", results_list)
        # Initialize total speed and count
        total_speed = 0
        count = 0
        avg_speed = 0

        # Calculate average speed
        for result in results_list:
            total_speed += result['drivingspeed']
            count += 1
        if count > 0:
            avg_speed = total_speed / count
        
        total_execution_time = (datetime.datetime.now() - current_time).total_seconds() * 1000
        
        print(f"{datetime.datetime.now()}: Average speed in the last 5 minutes: {avg_speed}, Query time: {query_time}  milliseconds, Total time: {total_execution_time}  milliseconds", )

        # Wait for 2 seconds
        time.sleep(2)
