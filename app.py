#!/usr/bin/env python3

from aws_cdk import core

from article_anomaly_detection_data_streams.article_anomaly_detection_data_streams_stack import \
    AnomalyDetectionDataStreamsStack

app = core.App()
AnomalyDetectionDataStreamsStack(app, "anomaly-detection-data-streams")

app.synth()
