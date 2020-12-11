from aws_cdk import (
    aws_kinesis as kinesis,
    aws_kinesisanalytics as kinesis_analytics,
    aws_iam as iam,
    aws_kinesisfirehose as firehose,
    aws_s3 as s3,
    aws_lambda as _lambda,
    aws_ec2 as ec2,
    aws_sns as sns,
    core)


class AnomalyDetectionDataStreamsStack(core.Stack):

    def __init__(self, scope: core.Construct, id: str, **kwargs) -> None:
        super().__init__(scope, id, **kwargs)

        output_bucket = s3.Bucket(self, 'outputBucket',
                                  removal_policy=core.RemovalPolicy.DESTROY)

        input_data_stream = kinesis.Stream(self, 'inputDataStream',
                                           stream_name='anomaly-detection-data-streams-input-data-stream')

        delivery_stream_role = iam.Role(self, 'deliveryStreamRole',
                                        assumed_by=iam.ServicePrincipal('firehose.amazonaws.com'),
                                        inline_policies=[iam.PolicyDocument(
                                            statements=[iam.PolicyStatement(
                                                effect=iam.Effect.ALLOW,
                                                actions=['kinesis:DescribeStream'],
                                                resources=[input_data_stream.stream_arn]
                                            )]
                                        )]

                                        )
        input_data_stream.grant_read(delivery_stream_role)

        output_bucket.grant_write(delivery_stream_role)

        anomaly_topic = sns.Topic(self, 'anomalyDetectionTopic')

        data_processing_function = _lambda.Function(self, "dataProcessingFunction",
                                                    runtime=_lambda.Runtime.PYTHON_3_7,
                                                    handler="lambda-handler.main",
                                                    code=_lambda.Code.asset("./dataProcessingFunction"),
                                                    environment={
                                                        'TOPIC_ARN': anomaly_topic.topic_arn
                                                    }
                                                    )

        delivery_stream = firehose.CfnDeliveryStream(self, 'deliveryStream',
                                                     s3_destination_configuration=firehose.CfnDeliveryStream.S3DestinationConfigurationProperty(
                                                         bucket_arn=output_bucket.bucket_arn,
                                                         role_arn=delivery_stream_role.role_arn
                                                     ),
                                                     kinesis_stream_source_configuration=firehose.CfnDeliveryStream.KinesisStreamSourceConfigurationProperty(
                                                         kinesis_stream_arn=input_data_stream.stream_arn,
                                                         role_arn=delivery_stream_role.role_arn
                                                     ),
                                                     delivery_stream_type='KinesisStreamAsSource'
                                                     )



        anomaly_topic.grant_publish(data_processing_function)

        anomalie_detection_app_role = iam.Role(self, 'anomalieDetectionAppRole',
                                               assumed_by=iam.ServicePrincipal('kinesisanalytics.amazonaws.com'),
                                               managed_policies=[
                                                   iam.ManagedPolicy.from_aws_managed_policy_name(
                                                       'AmazonKinesisReadOnlyAccess')
                                               ],
                                               inline_policies=[iam.PolicyDocument(
                                                   statements=[iam.PolicyStatement(
                                                       effect=iam.Effect.ALLOW,
                                                       resources=[
                                                           data_processing_function.function_arn,
                                                       ],
                                                       actions=[
                                                           "lambda:GetFunctionConfiguration",
                                                           "lambda:InvokeFunction",
                                                       ]
                                                   )]
                                               )])

        # Load Application Code
        with open('anomalie_detection_sql/application.sql', 'r') as file:
            app_code = file.read()

        anomalie_detection_app = kinesis_analytics.CfnApplication(self, 'anomalieDetectionApp',
                                                                  inputs=[
                                                                      kinesis_analytics.CfnApplication.InputProperty(
                                                                          name_prefix='SOURCE_SQL_STREAM',
                                                                          kinesis_streams_input=kinesis_analytics.CfnApplication.KinesisStreamsInputProperty(
                                                                              resource_arn=input_data_stream.stream_arn,
                                                                              role_arn=anomalie_detection_app_role.role_arn
                                                                          ),
                                                                          input_schema=kinesis_analytics.CfnApplication.InputSchemaProperty(
                                                                              record_columns=[
                                                                                  kinesis_analytics.CfnApplication.RecordColumnProperty(
                                                                                      name="sensor_id",
                                                                                      sql_type="CHAR(30)",
                                                                                      mapping="$.sensor_id"
                                                                                  ),
                                                                                  kinesis_analytics.CfnApplication.RecordColumnProperty(
                                                                                      name="temperature",
                                                                                      sql_type="DOUBLE",
                                                                                      mapping="$.temperature"
                                                                                  ),
                                                                                  kinesis_analytics.CfnApplication.RecordColumnProperty(
                                                                                      name="rpm",
                                                                                      sql_type="DOUBLE",
                                                                                      mapping="$.rpm"
                                                                                  ),
                                                                                  kinesis_analytics.CfnApplication.RecordColumnProperty(
                                                                                      name="in_service",
                                                                                      sql_type="BOOLEAN",
                                                                                      mapping="$.in_service"
                                                                                  ),
                                                                              ],
                                                                              record_format=kinesis_analytics.CfnApplication.RecordFormatProperty(
                                                                                  record_format_type='JSON',
                                                                                  mapping_parameters=kinesis_analytics.CfnApplication.MappingParametersProperty(
                                                                                      json_mapping_parameters=kinesis_analytics.CfnApplication.JSONMappingParametersProperty(
                                                                                          record_row_path='$'
                                                                                      )
                                                                                  )
                                                                              )
                                                                          )
                                                                      )],
                                                                  application_code=app_code
                                                                  )

        anomalie_detection_app_output_lambda = kinesis_analytics.CfnApplicationOutput(self,
                                                                                      'anomalieDetectionAppOutputLambda',
                                                                                      application_name=core.Fn.ref(
                                                                                          anomalie_detection_app.logical_id),
                                                                                      output=kinesis_analytics.CfnApplicationOutput.OutputProperty(
                                                                                          lambda_output=kinesis_analytics.CfnApplicationOutput.LambdaOutputProperty(
                                                                                              resource_arn=data_processing_function.function_arn,
                                                                                              role_arn=anomalie_detection_app_role.role_arn
                                                                                          ),
                                                                                          destination_schema=kinesis_analytics.CfnApplicationOutput.DestinationSchemaProperty(
                                                                                              record_format_type='JSON'
                                                                                          ),
                                                                                          name='PROCESS_STREAM'
                                                                                      )

                                                                                      )
        vpc = ec2.Vpc(self, "VPC",
                      nat_gateways=1,
                      subnet_configuration=[
                          ec2.SubnetConfiguration(name="private", subnet_type=ec2.SubnetType.PRIVATE),
                          ec2.SubnetConfiguration(name="public", subnet_type=ec2.SubnetType.PUBLIC),
                      ]
                      )

        # AMI
        amzn_linux = ec2.MachineImage.latest_amazon_linux(
            generation=ec2.AmazonLinuxGeneration.AMAZON_LINUX_2,
            edition=ec2.AmazonLinuxEdition.STANDARD,
            virtualization=ec2.AmazonLinuxVirt.HVM,
            storage=ec2.AmazonLinuxStorage.GENERAL_PURPOSE
        )
        producer_role = iam.Role(self, "producerInstanceRole",
                                 assumed_by=iam.ServicePrincipal("ec2.amazonaws.com")
                                 )

        producer_role.add_managed_policy(
            iam.ManagedPolicy.from_aws_managed_policy_name("AmazonSSMManagedInstanceCore"))
        input_data_stream.grant_write(producer_role)


        user_data = '#!/bin/bash\n yum update -y\n yum install python3 -y\n sudo yum install -y jq\n pip3 install boto3 --user\n pip3 install numpy --user\n curl https://bigdatainsider-anomalydetection-article-fra.s3.eu-central-1.amazonaws.com/producer/producer.py -o /tmp/producer.py'

        producer_instance = ec2.Instance(self, 'producerInstance',
                                         instance_type=ec2.InstanceType('t2.micro'),
                                         machine_image=amzn_linux,
                                         vpc=vpc,
                                         role=producer_role,
                                         user_data=ec2.UserData.custom(user_data)
                                         )

