
from aws_cdk import aws_lambda, aws_iam, Duration, Stack
from aws_cdk.aws_lambda import Runtime
from aws_cdk.aws_events import Rule, Schedule
from aws_cdk.aws_events_targets import LambdaFunction, SfnStateMachine
from aws_cdk.aws_stepfunctions import StateMachine, Parallel
from aws_cdk.aws_stepfunctions_tasks import LambdaInvoke
from constructs import Construct


class Challenge2Stack(Stack):

    def __init__(self, scope: Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        # Define the Lambda function
        lambda_function = aws_lambda.DockerImageFunction(
            self, 'LambdaFunction',
            code=aws_lambda.DockerImageCode.from_image_asset('lambda'),
            function_name='AgriculturalIOTInsertFunction',
            timeout=Duration.seconds(900),  # Maximum execution time for a Lambda function is 15 minutes
            memory_size=3008,  # Max memory allocation, adjust based on your requirements
            description='Lambda function for agricultural IOT data insertion',
            environment={  # Environment variables for the function
                'MONGODB_URI': 'mongodb+srv://<username>:<password>@cluster0.mongodb.net/test'  # Replace with your connection string
            }
        )

        # Define the IAM role for the Lambda function
        lambda_function.add_to_role_policy(aws_iam.PolicyStatement(
            effect=aws_iam.Effect.ALLOW,
            actions=['logs:CreateLogGroup', 'logs:CreateLogStream', 'logs:PutLogEvents'],
            resources=['arn:aws:logs:*:*:*']
        ))
        # Define the Step Function state machine
        definition = Parallel(self, 'ParallelStates')
        for i in range(30):  # Adjust this number based on your requirements
            definition.branch(LambdaInvoke(self, f'InvokeLambda{i}', lambda_function=lambda_function))

        state_machine = StateMachine(
            self, 'StateMachine',
            definition=definition,
            timeout=Duration.minutes(5)
        )

        # Define the EventBridge rule to trigger the state machine every minute
        rule = Rule(
            self, 'StateMachineTrigger',
            schedule=Schedule.rate(Duration.minutes(1)),
            targets=[SfnStateMachine(state_machine)]
        )
