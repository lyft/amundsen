# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import datetime
import logging
import os
import time
from os import listdir
from os.path import isfile, join
from typing import List, Tuple

from amundsen_gremlin.neptune_bulk_loader.api import NeptuneBulkLoaderApi, NeptuneBulkLoaderLoadStatusErrorLogEntry
from boto3.session import Session
from pyhocon import ConfigTree

from databuilder.publisher.base_publisher import Publisher

LOGGER = logging.getLogger(__name__)


class NeptuneCSVPublisher(Publisher):
    """
    This Publisher takes two folders for input and publishes to Neptune.
    One folder will contain CSV file(s) for Node where the other folder will contain CSV file(s) for Relationship.

    This publisher uses the bulk api found in
    https://github.com/amundsen-io/amundsengremlin/blob/master/amundsen_gremlin/neptune_bulk_loader/api.py

    which is a client for the the api found
    https://docs.aws.amazon.com/neptune/latest/userguide/bulk-load.html
    https://docs.aws.amazon.com/neptune/latest/userguide/bulk-load-tutorial-format-gremlin.html
    """

    # A directory that contains CSV files for nodes
    NODE_FILES_DIR = 'node_files_directory'
    # A directory that contains CSV files for relationships
    RELATION_FILES_DIR = 'relation_files_directory'

    # --- AWS CONFIGURATION ---
    # S3 bucket to upload files to
    AWS_S3_BUCKET_NAME = 'bucket_name'
    # S3 location where amundsen data can be exported to and Neptune can access
    AWS_BASE_S3_DATA_PATH = 'base_amundsen_data_path'

    NEPTUNE_HOST = 'neptune_host'

    # AWS CONFIGURATION
    AWS_REGION = 'aws_region'
    AWS_ACCESS_KEY = 'aws_access_key'
    AWS_SECRET_ACCESS_KEY = 'aws_secret_access_key'
    AWS_SESSION_TOKEN = 'aws_session_token'
    AWS_IAM_ROLE_NAME = 'aws_iam_role_name'

    FAIL_ON_ERROR = "fail_on_error"
    STATUS_POLLING_PERIOD = "status_polling_period"

    def __init__(self) -> None:
        super(NeptuneCSVPublisher, self).__init__()

    def init(self, conf: ConfigTree) -> None:
        self._boto_session = Session(
            aws_access_key_id=conf.get_string(NeptuneCSVPublisher.AWS_ACCESS_KEY, default=None),
            aws_secret_access_key=conf.get_string(NeptuneCSVPublisher.AWS_SECRET_ACCESS_KEY, default=None),
            aws_session_token=conf.get_string(NeptuneCSVPublisher.AWS_SESSION_TOKEN, default=None),
            region_name=conf.get_string(NeptuneCSVPublisher.AWS_REGION, default=None)
        )

        self.node_files_dir = conf.get_string(NeptuneCSVPublisher.NODE_FILES_DIR)
        self.relation_files_dir = conf.get_string(NeptuneCSVPublisher.RELATION_FILES_DIR)

        self._neptune_host = conf.get_string(NeptuneCSVPublisher.NEPTUNE_HOST)

        neptune_bulk_endpoint_uri = "wss://{host}/gremlin".format(
            host=self._neptune_host
        )

        self.bucket_name = conf.get_string(NeptuneCSVPublisher.AWS_S3_BUCKET_NAME)

        self.neptune_api_client = NeptuneBulkLoaderApi(
            session=self._boto_session,
            endpoint_uri=neptune_bulk_endpoint_uri,
            s3_bucket_name=self.bucket_name,
            iam_role_name=conf.get_string(NeptuneCSVPublisher.AWS_IAM_ROLE_NAME, default=None)
        )
        self.base_amundsen_data_path = conf.get_string(NeptuneCSVPublisher.AWS_BASE_S3_DATA_PATH)
        self.fail_on_error = conf.get_bool(NeptuneCSVPublisher.FAIL_ON_ERROR, default=False)
        self.status_polling_period = conf.get_int(NeptuneCSVPublisher.STATUS_POLLING_PERIOD, default=5)

    def publish_impl(self) -> None:
        if not self._is_upload_required():
            return

        datetime_portion = datetime.datetime.now().strftime("%Y_%m_%d_%H_%M_%S")
        s3_folder_location = "{base_directory}/{datetime_portion}".format(
            base_directory=self.base_amundsen_data_path,
            datetime_portion=datetime_portion,
        )

        self.upload_files(s3_folder_location)

        bulk_upload_response = self.neptune_api_client.load(
            s3_object_key=s3_folder_location,
            failOnError=self.fail_on_error
        )

        try:
            load_id = bulk_upload_response['payload']['loadId']
        except KeyError:
            raise Exception("Failed to load csv. Response: {0}".format(str(bulk_upload_response)))

        load_status = "LOAD_NOT_STARTED"
        all_errors: List[NeptuneBulkLoaderLoadStatusErrorLogEntry] = []
        while load_status in ("LOAD_IN_PROGRESS", "LOAD_NOT_STARTED", "LOAD_IN_QUEUE"):
            time.sleep(self.status_polling_period)
            load_status, errors = self._poll_status(load_id)
            all_errors.extend(errors)

        for error in all_errors:
            exception_message = """
            Error Code: {error_code}
            Error Message: {error_message}
            Failed File: {s3_path}
            """.format(
                error_code=error.get('errorCode'),
                error_message=error.get('errorMessage'),
                s3_path=error.get('fileName')
            )
            LOGGER.exception(exception_message)

    def _poll_status(self, load_id: str) -> Tuple[str, List[NeptuneBulkLoaderLoadStatusErrorLogEntry]]:
        load_status_response = self.neptune_api_client.load_status(
            load_id=load_id,
            errors=True
        )
        load_status_payload = load_status_response.get('payload', {})
        try:
            load_status = load_status_payload['overallStatus']['status']
        except KeyError:
            raise Exception("Failed to check status of {0} response: {1}".format(
                str(load_id),
                repr(load_status_response)
            ))
        return load_status, load_status_payload.get('errors', {}).get('errorLogs', [])

    def _get_file_paths(self) -> List[str]:
        node_names = [
            join(self.node_files_dir, f) for f in listdir(self.node_files_dir)
            if isfile(join(self.node_files_dir, f))
        ]
        edge_names = [
            join(self.relation_files_dir, f) for f in listdir(self.relation_files_dir)
            if isfile(join(self.relation_files_dir, f))
        ]
        return node_names + edge_names

    def _is_upload_required(self) -> bool:
        file_names = self._get_file_paths()
        return len(file_names) > 0

    def upload_files(self, s3_folder_location: str) -> None:
        file_paths = self._get_file_paths()
        for file_location in file_paths:
            with open(file_location, 'rb') as file_csv:
                file_name = os.path.basename(file_location)
                s3_object_key = "{s3_folder_location}/{file_name}".format(
                    s3_folder_location=s3_folder_location,
                    file_name=file_name
                )
                self.neptune_api_client.upload(
                    f=file_csv,
                    s3_object_key=s3_object_key
                )

    def get_scope(self) -> str:
        return 'publisher.neptune_csv_publisher'
