
from aws_cdk import aws_lambda, aws_iam, Duration, Stack, aws_iot , aws_kinesis,  aws_lambda_event_sources, aws_secretsmanager, SecretValue
from aws_cdk.aws_lambda import Runtime
from aws_cdk.aws_events import Rule, Schedule
from aws_cdk.aws_events_targets import LambdaFunction, SfnStateMachine

from aws_cdk.aws_stepfunctions import StateMachine, Parallel
from aws_cdk.aws_stepfunctions_tasks import LambdaInvoke
from constructs import Construct
import os, time


class IotCoreMongodbDemoStack(Stack):

    def __init__(self, scope: Construct, construct_id: str, **kwargs) -> None:
        super().__init__(scope, construct_id, **kwargs)


        #time.sleep(5 * 60)
  
        ########################################################################################  
        ########################################################################################  
        # Configuration
        ########################################################################################  
        ########################################################################################  
        
        IOT_TOPIC = "topic"
        PRIVATE_KEY_PATH = "./certificates/private_key.key"
        CERTIFICATE_SIGNING_REQUEST_PATH = "./certificates/signing_request.csr"
        
        IOT_PRODUCER_ACTIVE = True
        KINESIS_READER_ACTIVE = True
        MONGODB_QUERY_ACTIVE = True
        NOISY_NEIGHBOUR_ACTIVE = True
        NR_OF_LOAD_GENERATORS_ACTIVE = 0
        
        KINESIS_READER_BATCH_SIZE = 50
        
        MONGODB_DB = "agridb"
        MONGODB_COL = "agricol"

        # Retrieve MongoDB host from environment variable
        MONGODB_HOST = os.getenv("MONGODB_HOST")

        if not MONGODB_HOST:
            raise ValueError("Environment variable MONGODB_HOST is not set")
        
        # Retrieve MongoDB user from environment variable
        MONGODB_USER = os.getenv("MONGODB_USER")

        if not MONGODB_USER:
            raise ValueError("Environment variable MONGODB_USER is not set")

        # Retrieve MongoDB password from environment variable
        MONGODB_PW = os.getenv("MONGODB_PW")

        if not MONGODB_PW:
            raise ValueError("Environment variable MONGODB_PW is not set")


        ########################################################################################  
        ########################################################################################  
        # Secret Manager Secrets for MongoDb access and IOT authentication
        ########################################################################################  
        ########################################################################################  

        # Define the MongoDB secret
        mongodb_secret = aws_secretsmanager.Secret(self, "AgriMongoDBSecret",
            description="MongoDB User and Password",
            secret_name="AgriMongoDBSecret",
            generate_secret_string=aws_secretsmanager.SecretStringGenerator(
                secret_string_template = '{"username": "%s", "password": "%s"}' % (MONGODB_USER, MONGODB_PW),
                generate_string_key='mongodb'
            )
        )

        # Upload certificate for iot mqtt connection
        with open(PRIVATE_KEY_PATH, "r") as key_file:
            private_key = key_file.read()

        private_key_secret = aws_secretsmanager.Secret(self, "AgriPrivateKeySecret",
            description="Private Key Secret for IOT Authentication",
            secret_name="AgriPrivateKeySecret",
            secret_string_value=SecretValue.unsafe_plain_text(private_key)
        )


        ########################################################################################  
        ########################################################################################  
        # Kinesis Stream
        ########################################################################################  
        ########################################################################################  

        # Define the Kinesis stream
        kinesis_stream = aws_kinesis.Stream(self, "AgriKinesisStream")

        # Define a role for IoT to access Kinesis
        role = aws_iam.Role(self, "AgriIoTAccessRole",
            assumed_by=aws_iam.ServicePrincipal("iot.amazonaws.com")
        )
        kinesis_stream.grant_write(role)

        ########################################################################################  
        ########################################################################################  
        # IOT Core
        ########################################################################################  
        ########################################################################################  

        # Define the AWS IoT topic rule
        iot_topic_rule = aws_iot.CfnTopicRule(self, "AgriIoTTopicRule",
            topic_rule_payload=aws_iot.CfnTopicRule.TopicRulePayloadProperty(
                sql=f"SELECT * FROM '{IOT_TOPIC}'",  # adjust according to your needs
                rule_disabled=False,
                actions=[aws_iot.CfnTopicRule.ActionProperty(
                    kinesis=aws_iot.CfnTopicRule.KinesisActionProperty(
                        role_arn=role.role_arn,
                        stream_name=kinesis_stream.stream_name,
                    )
                )]
            ),
            rule_name="AgriIoTRule",
        )

        # Define an access management policy for the IOT topic
        aws_iot_policy = aws_iot.CfnPolicy(
            self, 
            "AgriIoTPolicy",
            policy_name="AgriIoTPolicy",
            policy_document={
                "Version": "2012-10-17",
                "Statement": [{
                    "Effect": "Allow",
                    "Action": "iot:*",
                    "Resource": "*"
                }]
            }
        )

        # Load the certificate signing request to a variable
        with open(CERTIFICATE_SIGNING_REQUEST_PATH, 'r') as csr_file:
            csr_content = csr_file.read()

        # Create the IoT certificate using the certificate signing request
        aws_iot_cert = aws_iot.CfnCertificate(
            self,
            "AgriIoTCert",
            certificate_signing_request=csr_content,
            status="ACTIVE"
        )

        # Attach the policy to the certificate
        aws_iot.CfnPolicyPrincipalAttachment(
            self,
            "AgriPolicyPrincipalAttachment",
            policy_name=aws_iot_policy.policy_name,
            principal=aws_iot_cert.attr_arn
        )

        ########################################################################################  
        ########################################################################################  
        # IOT Core Producer Lambda
        ########################################################################################  
        ########################################################################################  

        # Create a Lambda Layer covering all python dependencies        
        lambda_layer_iot = aws_lambda.LayerVersion(self, "AgriIOTLambdaLayer",
            code=aws_lambda.Code.from_asset("iot-lambda/lambda-layer"),
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],  # or any python version you want
            license="Apache-2.0",
            description="A layer to hold common utilities for AgriIOTLambdaFunction",
        )

        # Define the Lambda function
        lambda_function_iot = aws_lambda.Function(
            self, 'AgriIOTLambdaFunction',
            code=aws_lambda.Code.from_asset('iot-lambda/code'),  # point this to your lambda function directory
            handler='lambda_function.lambda_handler',  # replace with your lambda function file name and method
            runtime=aws_lambda.Runtime.PYTHON_3_9,  # replace with your Python version
            function_name='AgriIOTInsertFunction',
            timeout=Duration.seconds(120),
            memory_size=3008,
            description='Lambda function for agricultural IOT data insertion',
            layers = [lambda_layer_iot],
            environment={
                'IOT_TOPIC' : IOT_TOPIC,
                'PRIVATE_KEY_SECRET_ARN' : private_key_secret.secret_arn,
                'CERTIFICATE_ID' : aws_iot_cert.attr_id,
            }
        )

        # Add an IAM policy to get the certificate
        lambda_function_iot.add_to_role_policy(aws_iam.PolicyStatement(
            actions=["iot:DescribeCertificate"],
            resources=[aws_iot_cert.attr_arn], 
            )
        )

        # Add an IAM policy to get and publish to the endpoint
        lambda_function_iot.add_to_role_policy(aws_iam.PolicyStatement(
            actions=["iot:DescribeEndpoint", "iot:Publish" ],
            resources=['*'], 
            )
        )

        # Add an IAM policy to get the certificate secret
        lambda_function_iot.add_to_role_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=['secretsmanager:GetSecretValue'],
            resources=[ private_key_secret.secret_arn]
        ))

        # Add an EventBridgeRule that triggers the Lambda
        lambda_function_iot_rule = Rule(
            self, 'AgriLambdaIOTProducerRule',
            schedule=Schedule.rate(Duration.minutes(2)),
            enabled=IOT_PRODUCER_ACTIVE,
            targets=[LambdaFunction(lambda_function_iot, max_event_age=Duration.seconds(120), retry_attempts=1)]  
        )

        ########################################################################################  
        ########################################################################################  
        # Kinesis Reader Lambda
        ########################################################################################  
        ########################################################################################  

        # Create a Lambda Layer covering all python dependencies    
        lambda_layer_kinesis_reader = aws_lambda.LayerVersion(self, "AgriKinesisReaderLambdaLayer",
            code=aws_lambda.Code.from_asset("kinesis-reader-lambda/lambda-layer"),
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],  # or any python version you want
            license="Apache-2.0",
            description="A layer to hold common utilities",
        )

        # Define the Lambda function
        lambda_function_kinesis_reader = aws_lambda.Function(
            self, 'AgriLambdaFunctionKinesisReader',
            code=aws_lambda.Code.from_asset('kinesis-reader-lambda/code'),  # point this to your lambda function directory
            handler='lambda_function.lambda_handler',  # replace with your lambda function file name and method
            runtime=aws_lambda.Runtime.PYTHON_3_9,  # replace with your Python version
            function_name='AgriKinesisReaderFunction',
            timeout=Duration.seconds(900),
            memory_size=3008,
            description='Lambda function for reading from Kinesis and inserting into MongoDB.',
            layers = [lambda_layer_kinesis_reader],
            environment={
                'MONGODB_HOST': MONGODB_HOST,
                'MONGODB_USER': MONGODB_USER,
                'MONGODB_SECRET_ARN': mongodb_secret.secret_arn,
                'MONGODB_DB': MONGODB_DB,
                'MONGODB_COLLECTION': MONGODB_COL,
            }
        )
        # Define the IAM role for the Lambda function
        lambda_function_kinesis_reader.add_to_role_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents', 'secretsmanager:GetSecretValue'],
            resources=['arn:aws:logs:*:*:*', mongodb_secret.secret_arn]
        ))

        # Add the event source 
        if KINESIS_READER_ACTIVE:
            lambda_function_kinesis_reader.add_event_source(aws_lambda_event_sources.KinesisEventSource(kinesis_stream, 
                starting_position=aws_lambda.StartingPosition.TRIM_HORIZON,
                batch_size=KINESIS_READER_BATCH_SIZE # Adjust batch size according to your needs
            ))


        ########################################################################################  
        ########################################################################################  
        # MongoDB Query Lambda
        ########################################################################################  
        ########################################################################################  

        # Create a Lambda Layer covering all python dependencies    
        lambda_layer_mongodb_query = aws_lambda.LayerVersion(self, "AgriMongoDBQueryLayer",
            code=aws_lambda.Code.from_asset("mongodb-query-lambda/lambda-layer"),
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],  # or any python version you want
            license="Apache-2.0",
            description="A layer to hold common utilities",
        )

        # Define the Lambda function
        lambda_function_mongodb_query = aws_lambda.Function(
            self, 'AgriLambdaFunctionMongoDBQuery',
            code=aws_lambda.Code.from_asset('mongodb-query-lambda/code'),  # point this to your lambda function directory
            handler='lambda_function.lambda_handler',  # replace with your lambda function file name and method
            runtime=aws_lambda.Runtime.PYTHON_3_9,  # replace with your Python version
            function_name='AgriMongodbQueryFunction',
            timeout=Duration.seconds(300),
            memory_size=3008,
            description='Lambda function for querieng agricultural IOT data from MongoDB',
            layers = [lambda_layer_mongodb_query],
            environment={
                'MONGODB_HOST': MONGODB_HOST,
                'MONGODB_USER': MONGODB_USER,
                'MONGODB_SECRET_ARN': mongodb_secret.secret_arn,
                'MONGODB_DB': MONGODB_DB,
                'MONGODB_COLLECTION': MONGODB_COL,
                'VEHICLE_ID' : "1"
            }
        )
        # Define the IAM role for the Lambda function
        lambda_function_mongodb_query.add_to_role_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents', 'secretsmanager:GetSecretValue'],
            resources=['arn:aws:logs:*:*:*', mongodb_secret.secret_arn, ]
        ))

        # Add an EventBridgeRule that triggers the Lambda
        lambda_function_mongodb_query_rule = Rule(
            self, 'AgriLambdaMongoDBQueryRule',
            schedule=Schedule.rate(Duration.minutes(5)),
            enabled=MONGODB_QUERY_ACTIVE,
            targets=[LambdaFunction(lambda_function_mongodb_query, max_event_age=Duration.seconds(120), retry_attempts=1)]  
        )

        ########################################################################################  
        ########################################################################################  
        # MongoDB Noisy Neighbour Lambda
        ########################################################################################  
        ########################################################################################  

        # Create a Lambda Layer covering all python dependencies    
        lambda_layer_mongodb_noisy_neighbour = aws_lambda.LayerVersion(self, "AgriMongoDBNoisyNeighbourLayer",
            code=aws_lambda.Code.from_asset("mongodb-noisy-neighbour-lambda/lambda-layer"),
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],  # or any python version you want
            license="Apache-2.0",
            description="A layer to hold common utilities",
        )

        # Define the Lambda function
        lambda_function_mongodb_noisy_neighbour = aws_lambda.Function(
            self, 'AgriLambdaFunctionMongoDBNoisyNeighbour',
            code=aws_lambda.Code.from_asset('mongodb-noisy-neighbour-lambda/code'),  # point this to your lambda function directory
            handler='lambda_function.lambda_handler',  # replace with your lambda function file name and method
            runtime=aws_lambda.Runtime.PYTHON_3_9,  # replace with your Python version
            function_name='AgriMongodbNoisyNeighbourFunction',
            timeout=Duration.seconds(300),
            memory_size=3008,
            description='Lambda function for querieng agricultural IOT data from MongoDB',
            layers = [lambda_layer_mongodb_noisy_neighbour],
            environment={
                'MONGODB_HOST': MONGODB_HOST,
                'MONGODB_USER': MONGODB_USER,
                'MONGODB_SECRET_ARN': mongodb_secret.secret_arn,
                'MONGODB_DB': MONGODB_DB,
                'MONGODB_COLLECTION': MONGODB_COL,
                'VEHICLE_ID' : "1"
            }
        )
        # Define the IAM role for the Lambda function
        lambda_function_mongodb_noisy_neighbour.add_to_role_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents', 'secretsmanager:GetSecretValue'],
            resources=['arn:aws:logs:*:*:*', mongodb_secret.secret_arn, ]
        ))
        
         # Add an EventBridgeRule that triggers the Lambda      
        lambda_function_mongodb_noisy_neighbour_rule = Rule(
            self, 'AgriLambdaNoisyNeighbourRule',
            schedule=Schedule.rate(Duration.minutes(5)),
            enabled=NOISY_NEIGHBOUR_ACTIVE,
            targets=[LambdaFunction(lambda_function_mongodb_noisy_neighbour, max_event_age=Duration.seconds(120), retry_attempts=1)]  
        )      
        
 
        ########################################################################################  
        ########################################################################################  
        # Load Generation Lambda Function
        ########################################################################################  
        ########################################################################################    
  

        # Create a Lambda Layer covering all python dependencies            
        lambda_layer_load = aws_lambda.LayerVersion(self, "AgriLambdaLoadGenLambdaLayer",
            code=aws_lambda.Code.from_asset("load-lambda/lambda-layer"),
            compatible_runtimes=[aws_lambda.Runtime.PYTHON_3_9],  # or any python version you want
            license="Apache-2.0",
            description="A layer to hold common utilities for AgriLambdaFunctionLoadGen",
        )

        # Define the Lambda function
        lambda_function_load = aws_lambda.Function(
            self, 'AgriLambdaFunctionLoadGen',
            code=aws_lambda.Code.from_asset('load-lambda/code'),  # point this to your lambda function directory
            handler='lambda_function.lambda_handler',  # replace with your lambda function file name and method
            runtime=aws_lambda.Runtime.PYTHON_3_9,  # replace with your Python version
            function_name='AgriLoadInsertFunction',
            timeout=Duration.seconds(120),
            memory_size=3008,
            description='Lambda function for agricultural IOT data insertion',
            layers = [lambda_layer_load],
            environment={
                'MONGODB_HOST': MONGODB_HOST,
                'MONGODB_USER': MONGODB_USER,
                'MONGODB_SECRET_ARN': mongodb_secret.secret_arn,
                'MONGODB_DB': MONGODB_DB,
                'MONGODB_COLLECTION': MONGODB_COL
            }
        )

        # Define the IAM role for the Lambda function
        lambda_function_load.add_to_role_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents', 'secretsmanager:GetSecretValue'],
            resources=['arn:aws:logs:*:*:*', mongodb_secret.secret_arn]
        ))

        
        # Define the Step Function state machine
        definition = Parallel(self, 'AgriStateMachineParallelStates')
        for i in range(25):  # Adjust this number based on your requirements
            definition.branch(LambdaInvoke(self, f'InvokeLambda{i}', lambda_function=lambda_function_load))

        state_machine_1 = StateMachine(
            self, 'AgriLoadGenerationStateMachine',
            definition=definition,
            timeout=Duration.minutes(5)
        )

        # Define the EventBridge rule to trigger the state machine every minute
        for i in range(10):  # Adjust this number based on your requirements
            if i < NR_OF_LOAD_GENERATORS_ACTIVE:
                LOAD_GENERATOR_ACTIVE = True
            else:
                LOAD_GENERATOR_ACTIVE = False
            
            rule = Rule(
            self, f'AgriStateMachineTrigger{i}',
            schedule=Schedule.rate(Duration.minutes(1)),
            enabled=LOAD_GENERATOR_ACTIVE,
            targets=[SfnStateMachine(state_machine_1)]
        )



