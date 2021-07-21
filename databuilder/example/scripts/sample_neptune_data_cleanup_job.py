# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

"""
Shows how to set up a job that uses the neptune staleness removal task
"""
import logging
import os

import boto3
from pyhocon import ConfigFactory

from databuilder.clients.neptune_client import NeptuneSessionClient
from databuilder.job.job import DefaultJob
from databuilder.task.neptune_staleness_removal_task import NeptuneStalenessRemovalTask

session = boto3.Session()

aws_creds = session.get_credentials()
aws_access_key = aws_creds.access_key
aws_access_secret = aws_creds.secret_key
aws_session_token = aws_creds.token
AWS_REGION = os.environ.get("AWS_REGION", 'us-east-1')

neptune_host = os.getenv('CREDENTIALS_NEPTUNE_HOST', 'localhost')
neptune_port = os.getenv('CREDENTIALS_NEPTUNE_PORT', 7687)
neptune_endpoint = f'{neptune_host}:{neptune_port}'


def create_remove_stale_data_job():
    logging.basicConfig(level=logging.INFO)

    target_relations = ['DESCRIPTION', 'DESCRIPTION_OF', 'COLUMN', 'COLUMN_OF', 'TABLE', 'TABLE_OF']
    target_nodes = ['Table', 'Column', 'Programmatic_Description', "Schema"]
    job_config = ConfigFactory.from_dict({
        'task.remove_stale_data': {
            NeptuneStalenessRemovalTask.TARGET_RELATIONS: target_relations,
            NeptuneStalenessRemovalTask.TARGET_NODES: target_nodes,
            NeptuneStalenessRemovalTask.STALENESS_CUT_OFF_IN_SECONDS: 86400,  # 1 day
            'neptune.client': {
                NeptuneSessionClient.NEPTUNE_HOST_NAME: neptune_endpoint,
                NeptuneSessionClient.AWS_REGION: AWS_REGION,
                NeptuneSessionClient.AWS_ACCESS_KEY: aws_access_key,
                NeptuneSessionClient.AWS_SECRET_ACCESS_KEY: aws_access_secret,
                NeptuneSessionClient.AWS_SESSION_TOKEN: aws_session_token
            }
        }
    })
    job = DefaultJob(
        conf=job_config,
        task=NeptuneStalenessRemovalTask()
    )
    return job


if __name__ == '__main__':
    job = create_remove_stale_data_job()
    job.launch()
