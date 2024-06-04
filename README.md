# illumio-lambda-kinesis-feed

Simple lambda to feed all your Illumio PCE audit and traffic events to AWS Kinesis data streams.
This makes it simple to forward all traffic to e.g. S3 or AWS OpenSearch service using a AWS Firehose.

The function queries the Illumio Core PCE events and traffic APIs and returns data in raw JSON format
to hand over to the AWS Kinesis ARN specified in the KINESIS_ARN environment variable. Kinesis can then
be used to transport the data to other destinations.

## Dependencies
The script imports the following Python libraries:

* boto3: The Amazon Web Services (AWS) SDK for Python, which allows Python developers to write software that makes use of AWS services like Amazon S3, Amazon EC2, etc.
* json: A standard Python library for working with JSON data.
* logging: A standard Python library for generating logging messages.
* signal: A standard Python library for handling signals.
* os: A standard Python library for interacting with the operating system.
* datetime: A standard Python library for working with dates and times.
* illumio: A custom library for interacting with the Illumio Policy Compute Engine (PCE).
* botocore.exceptions: A part of the boto3 library for handling exceptions.

### Environment Variables

The script uses the following environment variables:

* KINESIS_ARN: The Amazon Resource Name (ARN) of the Kinesis stream.
* pce_secret: The name of the secret stored in AWS Secrets Manager that contains the PCE API credentials and other related information.
* aws_region: The AWS region where the Secrets Manager is located.

### Functions
The script defines the following functions:

get_secret(): This function retrieves the secret (named by the pce_secret environment variable) from AWS Secrets Manager. The secret is expected to be a JSON string containing the PCE API credentials and other related information.

lambda_handler(event, context): This is the main function that AWS Lambda calls when the Lambda function is invoked. It establishes a connection to the PCE, checks the connection, and calculates a timestamp 5 minutes before the current time.

## Usage
This script is intended to be deployed as an AWS Lambda function. The Lambda function can be triggered by various AWS services. The event and context parameters of the lambda_handler function will be populated by AWS Lambda when the function is invoked.

Please note that this is a high-level overview of the script. For detailed information about how the script works, you should refer to the script's source code and any associated documentation.

## Deploying your function

### ZIP deployment

* https://docs.aws.amazon.com/lambda/latest/dg/python-package.html

### Docker deployment

* https://docs.aws.amazon.com/lambda/latest/dg/python-image.html

## IAM

A example role document is included.