# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import base64
import tempfile
import unittest
from typing import Any

from mock import Mock, patch
from pyhocon import ConfigFactory

from databuilder import Scoped
from databuilder.extractor.bigquery_usage_extractor import BigQueryTableUsageExtractor, TableColumnUsageTuple

CORRECT_DATA = {
    "entries": [{
        "protoPayload": {
            "@type": "type.googleapis.com/google.cloud.audit.AuditLog",
            "status": {},
            "authenticationInfo": {
                "principalEmail": "your-user-here@test.com"
            },
            "serviceName": "bigquery.googleapis.com",
            "methodName": "jobservice.jobcompleted",
            "resourceName": "projects/your-project-here/jobs/bquxjob_758c08d1_16a96889839",
            "serviceData": {
                "@type": "type.googleapis.com/google.cloud.bigquery.logging.v1.AuditData",
                "jobCompletedEvent": {
                    "eventName": "query_job_completed",
                    "job": {
                        "jobName": {
                            "projectId": "your-project-here",
                            "jobId": "bquxjob_758c08d1_16a96889839",
                            "location": "US"
                        },
                        "jobConfiguration": {
                            "query": {
                                "query": "select descript from "
                                         "`bigquery-public-data.austin_incidents.incidents_2008`\n",
                                "destinationTable": {
                                    "projectId": "your-project-here",
                                    "datasetId": "_07147a061ddfd6dcaf246cfc5e858a0ccefa7080",
                                    "tableId": "anon1dd83635c62357091e55a5f76fb62d7deebcfa4c"
                                },
                                "createDisposition": "CREATE_IF_NEEDED",
                                "writeDisposition": "WRITE_TRUNCATE",
                                "defaultDataset": {},
                                "queryPriority": "QUERY_INTERACTIVE",
                                "statementType": "SELECT"
                            }
                        },
                        "jobStatus": {
                            "state": "DONE",
                            "error": {}
                        },
                        "jobStatistics": {
                            "createTime": "2019-05-08T08:22:56.349Z",
                            "startTime": "2019-05-08T08:22:56.660Z",
                            "endTime": "2019-05-08T08:23:00.049Z",
                            "totalProcessedBytes": "3637807",
                            "totalBilledBytes": "10485760",
                            "billingTier": 1,
                            "totalSlotMs": "452",
                            "referencedTables": [
                                {
                                    "projectId": "bigquery-public-data",
                                    "datasetId": "austin_incidents",
                                    "tableId": "incidents_2008"
                                }
                            ],
                            "totalTablesProcessed": 1,
                            "queryOutputRowCount": "179524"
                        }
                    }
                }
            }
        },
        "insertId": "-jyqvjse6lwjz",
        "resource": {
            "type": "bigquery_resource",
            "labels": {
                "project_id": "your-project-here"
            }
        },
        "timestamp": "2019-05-08T08:23:00.061Z",
        "severity": "INFO",
        "logName": "projects/your-project-here/logs/cloudaudit.googleapis.com%2Fdata_access",
        "receiveTimestamp": "2019-05-08T08:23:00.310709609Z"
    }]
}  # noqa

FAILURE = {
    "entries": [{
        "protoPayload": {
            "authenticationInfo": {
                "principalEmail": "your-user-here@test.com"
            },
            "methodName": "jobservice.jobcompleted",
            "serviceData": {
                "jobCompletedEvent": {
                    "job": {
                        "jobStatus": {
                            "state": "DONE",
                            "error": {
                                "code": 11,
                                "message": "Some descriptive error message"
                            }
                        },
                        "jobStatistics": {
                            "createTime": "2019-05-08T08:22:56.349Z",
                            "startTime": "2019-05-08T08:22:56.660Z",
                            "endTime": "2019-05-08T08:23:00.049Z",
                            "totalProcessedBytes": "3637807",
                            "totalBilledBytes": "10485760",
                            "referencedTables": [
                                {
                                    "projectId": "bigquery-public-data",
                                    "datasetId": "austin_incidents",
                                    "tableId": "incidents_2008"
                                }
                            ]
                        }
                    }
                }
            },
        },
    }]
}  # noqa

# An empty dict will be ignored, but putting in nextPageToken causes the test
# to loop infinitely, so we need a bogus key/value to ensure that we will try
# to read entries
NO_ENTRIES = {'key': 'value'}  # noqa

KEYFILE_DATA = """
ewogICJ0eXBlIjogInNlcnZpY2VfYWNjb3VudCIsCiAgInByb2plY3RfaWQiOiAieW91ci1wcm9q
ZWN0LWhlcmUiLAogICJwcml2YXRlX2tleV9pZCI6ICJiMDQ0N2U1ODEyYTg5ZTAyOTgxYjRkMWE1
YjE1N2NlNzZkOWJlZTc3IiwKICAicHJpdmF0ZV9rZXkiOiAiLS0tLS1CRUdJTiBQUklWQVRFIEtF
WS0tLS0tXG5NSUlFdkFJQkFEQU5CZ2txaGtpRzl3MEJBUUVGQUFTQ0JLWXdnZ1NpQWdFQUFvSUJB
UUM1UzBYRWtHY2NuOEsxXG5ZbHhRbXlhRWFZK2grYnRacHRVWjJiK2J1cTluNExKU3I3eTdPQWll
ZjBWazIyQnc1TFRsUXRQSUtNVkh6MzJMXG5Ld0lJYmY5Wkwzamd5UC9hNHIveHVhMVdzNFF2YVkz
TGoxRG1ITm40L3hQNXdDY0VscHIxV2RXL05VZ1RQV1A2XG5LZnVDdHhyQTJxbHJNazhyYklXVTRm
WTAzQmFqdzNHT0p4VDBvbXlCVmdGSzJTdGRFUVVYMm9YQVdSNXJyR21qXG5qWTNzb3lNU0NwSWtT
b0h4b1BrVEM0VzZ2a3dJRlk4SUkwbmhsWUZHc3FiZjdkbTBLVEZmVVh5SUFTOHd6RCtlXG54UFVQ
V3k0UXA5cTVyNTVPRmlxdWt3TGNZei9BQXFpYTU3KzhURmhiWXcwUXNsZ2xSaWFLWkVhQyt4M0pD
OEhuXG5KajY2WE5mTEFnTUJBQUVDZ2dFQVMyNFlGYi9QS2ZqamM2RjZBUnBYNExsMFRqVHlqcmw2
c001UzBSdDdRbWRYXG5VSS9YM2NNZXh4NzZhZWRnYURUQ2F6MzhKdFJxRXlTbGI5enZNKzFMY013
QmdraHcxM05OUGlNZkxGZGg3VWNrXG5BUVR6b3VtRjFuWklkSGhEcWZ1QlUzWGhyTGdOQWtBUWpn
cy9KdVJSVU1iekJ2OXcrVFZ4WDcxbzAvWHdoWE5kXG5kSWlWdE1TbnFWQ0J2cEp3ZXBoR3FxNGQ3
VEIzb2F3UUg1QkFGeHk5NGpoT0dwaVFWYW8yQmtPdEVyVVBQYjkrXG5vRzByZTM3WHVtQzZRWENv
VSs4Zm4vcE1YVWVOUitXSm5tY1lndVZqWDl6QzJ3MU13cmVmOFVKa1Q4SHJxZ09KXG5sWnNFcVJr
aHBYUFVzdmt2dWxQTWQ3TitJdlFvYTh0N3ZaZFkrR1lMdVFLQmdRRHd2enY0alhVUStIU1RaVm1p
XG5hQmNMVGRMRE5WNlpuT25aTEhxbDZaQmloTUhZNi9qS2xDN1hqWGJaQ2NqS05MMkE1am9mQ0d5
bHFhNFRrZnArXG5rYmJKQ29KS2tFY1pSWGQ3NEdXb0J1V2d3enY2WWFkcDNxS2x0RndhM1FjMkJ3
SlNlazkrTzd6OGs2d0dvclZJXG5OK3ZNMVd3OWJPa1VaaXh4T2g2V2ZKSTl6UUtCZ1FERkNLQXZ2
b3FUQnErMnovazhLYy9lTHVRdThPWWNXVm9GXG55eXprOTN2QnBXcEVPT1hybnNsUFFtQldUdTN5
UWpRN08zd2t1c0g3VUtJQTg0MDVHbDlwbmJvTmlaSVdBRlpvXG4vVWlVVm5aa3pvZER5Tk9PUjBm
UW5zM1BaeE5peklSSjh2Mm93a2d3MExFYWEwaWUyNU92bFJmQ2pmYlVZL0EzXG5wbU9SVkdFVDl3
S0JnR0Zab3lHRjZoRzd0a0FvR28vT3NZclRwR2RsZkdSM2pDUlNsU0hrQ1l1ZERWbnZTY0o1XG5H
MXYwaTF1R1ZsaFY3VTlqU1p0azU3SXhvLytyNXZRcGJoVnJsM1laVTNiSG5XSk5RaTRvNDlBWFFu
aWo1bk9zXG5JRzhMT0xkd0swdFFtRUxMekx0SjRzanIyZ013NWtkV3ZaWXRzMEEvZXh6Um1DVU5F
SE5mMmk3OUFvR0FESVpkXG4yR3NlVi9aRzJUSWpQOFhRcHVrSUxFdTM5UGxoRlpreXcyTlFCS0ZG
UGd6MzRLQjVYNFp5cFVuaktsRTNETVRkXG5RV0IxMEVueDRtbVpBcFpBbG5BbVVaSDdMVmJjSjFS
aWRydUFUeXdwd1E5VkUyaElrbVJsNU5kQ2pqYzkrWTF1XG52bm1MS1Q4NjR0a0xCcjRpaHpqTkI5
c0tZN251blRzQWZVNkYxVVVDZ1lBMmdlMFdiVEVwRlBuN05YYjZ4citiXG5QK1RFVEVWZzhRS0Z1
OUtHVk03NXI5dmhYblNicmphbGVCSzJFQzBLK2F2d2hHTTd3eXRqM0FrTjRac2NKNWltXG5VZTBw
Z3pVSE1RSVI1OWlGVmt5WVVjZnZMSERZU0xmeW9QVU5RWWduVXBKYlZOczZtWFRqQ3o2UERrb0tX
ZzcyXG4rS3p4RWhubWJzY0NiSFRpQ08wNEtBPT1cbi0tLS0tRU5EIFBSSVZBVEUgS0VZLS0tLS1c
biIsCiAgImNsaWVudF9lbWFpbCI6ICJ0ZXN0LTE2MkB5b3VyLXByb2plY3QtaGVyZS5pYW0uZ3Nl
cnZpY2VhY2NvdW50LmNvbSIsCiAgImNsaWVudF9pZCI6ICIxMDg2NTMzMjY0MzE1NDU2ODg3MTAi
LAogICJhdXRoX3VyaSI6ICJodHRwczovL2FjY291bnRzLmdvb2dsZS5jb20vby9vYXV0aDIvYXV0
aCIsCiAgInRva2VuX3VyaSI6ICJodHRwczovL29hdXRoMi5nb29nbGVhcGlzLmNvbS90b2tlbiIs
CiAgImF1dGhfcHJvdmlkZXJfeDUwOV9jZXJ0X3VybCI6ICJodHRwczovL3d3dy5nb29nbGVhcGlz
LmNvbS9vYXV0aDIvdjEvY2VydHMiLAogICJjbGllbnRfeDUwOV9jZXJ0X3VybCI6ICJodHRwczov
L3d3dy5nb29nbGVhcGlzLmNvbS9yb2JvdC92MS9tZXRhZGF0YS94NTA5L3Rlc3QtMTYyJTQweW91
ci1wcm9qZWN0LWhlcmUuaWFtLmdzZXJ2aWNlYWNjb3VudC5jb20iCn0KCgo=
"""


class MockLoggingClient():
    def __init__(self, data: Any) -> None:
        self.data = data
        self.a = Mock()
        self.a.execute.return_value = self.data
        self.b = Mock()
        self.b.list.return_value = self.a

    def entries(self) -> Any:
        return self.b


# Patch fallback auth method to avoid actually calling google API
@patch('google.auth.default', lambda scopes: ['dummy', 'dummy'])
class TestBigqueryUsageExtractor(unittest.TestCase):

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_basic_extraction(self, mock_build: Any) -> None:
        """
        Test Extraction using mock class
        """
        config_dict = {
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.PROJECT_ID_KEY}': 'bigquery-public-data',
        }
        conf = ConfigFactory.from_dict(config_dict)

        mock_build.return_value = MockLoggingClient(CORRECT_DATA)
        extractor = BigQueryTableUsageExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))
        result = extractor.extract()
        assert result is not None
        self.assertIsInstance(result, tuple)

        (key, value) = result
        self.assertIsInstance(key, TableColumnUsageTuple)
        self.assertIsInstance(value, int)

        self.assertEqual(key.database, 'bigquery')
        self.assertEqual(key.cluster, 'bigquery-public-data')
        self.assertEqual(key.schema, 'austin_incidents')
        self.assertEqual(key.table, 'incidents_2008')
        self.assertEqual(key.email, 'your-user-here@test.com')
        self.assertEqual(value, 1)

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_no_entries(self, mock_build: Any) -> None:
        config_dict = {
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.PROJECT_ID_KEY}': 'bigquery-public-data',
        }
        conf = ConfigFactory.from_dict(config_dict)

        mock_build.return_value = MockLoggingClient(NO_ENTRIES)
        extractor = BigQueryTableUsageExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))
        result = extractor.extract()
        self.assertIsNone(result)

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_key_path(self, mock_build: Any) -> None:
        """
        Test key_path can be used
        """

        with tempfile.NamedTemporaryFile() as keyfile:
            # There are many github scanners looking for API / cloud keys, so in order not to get a
            # false positive triggering everywhere, I base64 encoded the key.
            # This is written to a tempfile as part of this test and then used.
            keyfile.write(base64.b64decode(KEYFILE_DATA))
            keyfile.flush()
            config_dict = {
                f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.PROJECT_ID_KEY}': 'bigquery-public-data',
                f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.KEY_PATH_KEY}': keyfile.name,
            }
            conf = ConfigFactory.from_dict(config_dict)

            mock_build.return_value = MockLoggingClient(CORRECT_DATA)
            extractor = BigQueryTableUsageExtractor()
            extractor.init(Scoped.get_scoped_conf(conf=conf,
                                                  scope=extractor.get_scope()))

            args, kwargs = mock_build.call_args
            creds = kwargs['http'].credentials
            self.assertEqual(creds.project_id, 'your-project-here')
            self.assertEqual(creds.service_account_email, 'test-162@your-project-here.iam.gserviceaccount.com')

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_timestamp_pagesize_settings(self, mock_build: Any) -> None:
        """
        Test timestamp and pagesize can be set
        """
        TIMESTAMP = '2019-01-01T00:00:00.00Z'
        PAGESIZE = 215

        config_dict = {
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.PROJECT_ID_KEY}': 'bigquery-public-data',
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.TIMESTAMP_KEY}': TIMESTAMP,
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.PAGE_SIZE_KEY}': PAGESIZE,
        }
        conf = ConfigFactory.from_dict(config_dict)

        client = MockLoggingClient(CORRECT_DATA)
        mock_build.return_value = client
        extractor = BigQueryTableUsageExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))

        args, kwargs = client.b.list.call_args
        body = kwargs['body']

        self.assertEqual(body['pageSize'], PAGESIZE)
        self.assertEqual(TIMESTAMP in body['filter'], True)

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_failed_jobs_should_not_be_counted(self, mock_build: Any) -> None:
        config_dict = {
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.PROJECT_ID_KEY}': 'bigquery-public-data',
        }
        conf = ConfigFactory.from_dict(config_dict)

        client = MockLoggingClient(FAILURE)
        mock_build.return_value = client
        extractor = BigQueryTableUsageExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))

        result = extractor.extract()
        self.assertIsNone(result)

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_email_filter_not_counted(self, mock_build: Any) -> None:
        config_dict = {
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.PROJECT_ID_KEY}': 'bigquery-public-data',
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.EMAIL_PATTERN}': 'emailFilter',
        }
        conf = ConfigFactory.from_dict(config_dict)

        mock_build.return_value = MockLoggingClient(CORRECT_DATA)
        extractor = BigQueryTableUsageExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))
        result = extractor.extract()
        self.assertIsNone(result)

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_email_filter_counted(self, mock_build: Any) -> None:
        config_dict = {
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.PROJECT_ID_KEY}': 'bigquery-public-data',
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.EMAIL_PATTERN}': '.*@test.com.*',
        }
        conf = ConfigFactory.from_dict(config_dict)

        mock_build.return_value = MockLoggingClient(CORRECT_DATA)
        extractor = BigQueryTableUsageExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))
        result = extractor.extract()
        assert result is not None
        self.assertIsInstance(result, tuple)

        (key, value) = result
        self.assertIsInstance(key, TableColumnUsageTuple)
        self.assertIsInstance(value, int)

        self.assertEqual(key.database, 'bigquery')
        self.assertEqual(key.cluster, 'bigquery-public-data')
        self.assertEqual(key.schema, 'austin_incidents')
        self.assertEqual(key.table, 'incidents_2008')
        self.assertEqual(key.email, 'your-user-here@test.com')
        self.assertEqual(value, 1)

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_not_counting_referenced_table_belonging_to_different_project(self, mock_build: Any) -> None:
        """
        Test result when referenced table belongs to a project different from the PROJECT_ID_KEY of the extractor
        """
        config_dict = {
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.PROJECT_ID_KEY}': 'your-project-here',
        }
        conf = ConfigFactory.from_dict(config_dict)

        mock_build.return_value = MockLoggingClient(CORRECT_DATA)
        extractor = BigQueryTableUsageExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))

        result = extractor.extract()
        assert result is None

    @patch('databuilder.extractor.base_bigquery_extractor.build')
    def test_counting_referenced_table_belonging_to_different_project(self, mock_build: Any) -> None:
        """
        Test result when referenced table belongs to a project different from the PROJECT_ID_KEY of the extractor
        and COUNT_READS_ONLY_FROM_PROJECT is set to False
        """
        config_dict = {
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.PROJECT_ID_KEY}': 'your-project-here',
            f'extractor.bigquery_table_usage.{BigQueryTableUsageExtractor.COUNT_READS_ONLY_FROM_PROJECT_ID_KEY}': False,
        }
        conf = ConfigFactory.from_dict(config_dict)

        mock_build.return_value = MockLoggingClient(CORRECT_DATA)
        extractor = BigQueryTableUsageExtractor()
        extractor.init(Scoped.get_scoped_conf(conf=conf,
                                              scope=extractor.get_scope()))

        result = extractor.extract()
        assert result is not None
        self.assertIsInstance(result, tuple)

        (key, value) = result
        self.assertIsInstance(key, TableColumnUsageTuple)
        self.assertIsInstance(value, int)

        self.assertEqual(key.database, 'bigquery')
        self.assertEqual(key.cluster, 'bigquery-public-data')
        self.assertEqual(key.schema, 'austin_incidents')
        self.assertEqual(key.table, 'incidents_2008')
        self.assertEqual(key.email, 'your-user-here@test.com')
        self.assertEqual(value, 1)
