# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import logging
import re
from collections import namedtuple
from datetime import (
    datetime, timedelta, timezone,
)
from time import sleep
from typing import (
    Any, Dict, Iterator, List, Optional, Tuple,
)

from pyhocon import ConfigTree

from databuilder.extractor.base_bigquery_extractor import BaseBigQueryExtractor

TableColumnUsageTuple = namedtuple('TableColumnUsageTuple', ['database', 'cluster', 'schema',
                                                             'table', 'column', 'email'])

LOGGER = logging.getLogger(__name__)


class BigQueryTableUsageExtractor(BaseBigQueryExtractor):
    """
    An aggregate extractor for bigquery table usage. This class takes the data from
    the stackdriver logging API by filtering on timestamp, bigquery_resource and looking
    for referencedTables in the response.
    """
    TIMESTAMP_KEY = 'timestamp'
    _DEFAULT_SCOPES = ['https://www.googleapis.com/auth/cloud-platform']
    EMAIL_PATTERN = 'email_pattern'
    DELAY_TIME = 'delay_time'
    TABLE_DECORATORS = ['$', '@']
    COUNT_READS_ONLY_FROM_PROJECT_ID_KEY = 'count_reads_only_from_project_id_key'

    def init(self, conf: ConfigTree) -> None:
        BaseBigQueryExtractor.init(self, conf)
        self.timestamp = conf.get_string(
            BigQueryTableUsageExtractor.TIMESTAMP_KEY,
            (datetime.now(timezone.utc) - timedelta(days=1)).strftime(BigQueryTableUsageExtractor.DATE_TIME_FORMAT))

        self.email_pattern = conf.get_string(BigQueryTableUsageExtractor.EMAIL_PATTERN, None)
        self.delay_time = conf.get_int(BigQueryTableUsageExtractor.DELAY_TIME, 100)
        self.table_usage_counts: Dict[TableColumnUsageTuple, int] = {}
        # GCP console allows running queries using tables from a project different from the one the extractor is
        # used for; only usage metadata of referenced tables present in the given project_id_key for the
        # extractor is taken into account and usage metadata of referenced tables from other projects
        # is ignored by "default".
        self.count_reads_only_from_same_project = conf.get_bool(
            BigQueryTableUsageExtractor.COUNT_READS_ONLY_FROM_PROJECT_ID_KEY, True)
        self._count_usage()
        self.iter = iter(self.table_usage_counts)

    def _count_usage(self) -> None:  # noqa: C901
        count = 0
        for entry in self._retrieve_records():
            count += 1
            if count % self.pagesize == 0:
                LOGGER.info(f'Aggregated {count} records')

            if entry is None:
                continue

            try:
                job = entry['protoPayload']['serviceData']['jobCompletedEvent']['job']
            except Exception:
                continue
            if job['jobStatus']['state'] != 'DONE':
                # This job seems not to have finished yet, so we ignore it.
                continue
            if len(job['jobStatus'].get('error', {})) > 0:
                # This job has errors, so we ignore it
                continue

            email = entry['protoPayload']['authenticationInfo']['principalEmail']
            # Query results can be cached and if the source tables remain untouched,
            # bigquery will return it from a 24 hour cache result instead. In that
            # case, referencedTables has been observed to be empty:
            # https://cloud.google.com/logging/docs/reference/audit/bigquery/rest/Shared.Types/AuditData#JobStatistics

            refTables = job['jobStatistics'].get('referencedTables', None)
            if refTables:
                if 'totalTablesProcessed' in job['jobStatistics']:
                    self._create_records(
                        refTables,
                        job['jobStatistics']['totalTablesProcessed'], email,
                        job['jobName']['jobId'])

            refViews = job['jobStatistics'].get('referencedViews', None)
            if refViews:
                if 'totalViewsProcessed' in job['jobStatistics']:
                    self._create_records(
                        refViews, job['jobStatistics']['totalViewsProcessed'],
                        email, job['jobName']['jobId'])

    def _create_records(self, refResources: List[dict], resourcesProcessed: int, email: str,
                        jobId: str) -> None:
        # if email filter is provided, only the email matched with filter will be recorded.
        if self.email_pattern:
            if not re.match(self.email_pattern, email):
                # the usage account not match email pattern
                return

        if len(refResources) != resourcesProcessed:
            LOGGER.warning(f'The number of tables listed in job {jobId} is not consistent')
            return

        for refResource in refResources:
            tableId = refResource['tableId']
            datasetId = refResource['datasetId']

            if self._is_anonymous_dataset(datasetId) or self._is_wildcard_table(tableId):
                continue

            tableId = self._remove_table_decorators(tableId)

            if self._is_sharded_table(tableId):
                tableId = tableId[:-BigQueryTableUsageExtractor.DATE_LENGTH]

            if refResource['projectId'] != self.project_id and self.count_reads_only_from_same_project:
                LOGGER.debug(
                    f'Not counting usage for {refResource} since {tableId} '
                    f'is not present in {self.project_id} '
                    f'and {BigQueryTableUsageExtractor.COUNT_READS_ONLY_FROM_PROJECT_ID_KEY} is True')
                continue
            else:
                key = TableColumnUsageTuple(database='bigquery',
                                            cluster=refResource['projectId'],
                                            schema=datasetId,
                                            table=tableId,
                                            column='*',
                                            email=email)

            new_count = self.table_usage_counts.get(key, 0) + 1
            self.table_usage_counts[key] = new_count

    def _retrieve_records(self) -> Iterator[Optional[Dict]]:
        """
        Extracts bigquery log data by looking at the principalEmail in the authenticationInfo block and
        referencedTables in the jobStatistics and filters out log entries of metadata queries.
        :return: Provides a record or None if no more to extract
        """
        body = {
            'resourceNames': [f'projects/{self.project_id}'],
            'pageSize': self.pagesize,
            'filter': 'protoPayload.methodName="jobservice.jobcompleted" AND '
                      'resource.type="bigquery_resource" AND '
                      'NOT protoPayload.serviceData.jobCompletedEvent.job.jobConfiguration.query.query:('
                      'INFORMATION_SCHEMA OR __TABLES__) AND '
                      f'timestamp >= "{self.timestamp}" AND timestamp < "{self.cutoff_time}"'
        }
        for page in self._page_over_results(body):
            for entry in page['entries']:
                yield entry

    def extract(self) -> Optional[Tuple[Any, int]]:
        try:
            key = next(self.iter)
            return key, self.table_usage_counts[key]
        except StopIteration:
            return None

    def _page_over_results(self, body: Dict) -> Iterator[Dict]:
        response = self.logging_service.entries().list(body=body).execute(
            num_retries=BigQueryTableUsageExtractor.NUM_RETRIES)
        while response:
            if 'entries' in response:
                yield response

            try:
                if 'nextPageToken' in response:
                    body['pageToken'] = response['nextPageToken']
                    response = self.logging_service.entries().list(body=body).execute(
                        num_retries=BigQueryTableUsageExtractor.NUM_RETRIES)
                else:
                    response = None
            except Exception:
                # Add a delay when BQ quota exceeds limitation
                sleep(self.delay_time)

    def _remove_table_decorators(self, tableId: str) -> Optional[str]:
        for decorator in BigQueryTableUsageExtractor.TABLE_DECORATORS:
            tableId = tableId.split(decorator)[0]
        return tableId

    def _is_anonymous_dataset(self, datasetId: str) -> bool:
        # temporary/cached results tables are stored in anonymous datasets that have names starting with '_'
        return datasetId.startswith('_')

    def _is_wildcard_table(self, tableId: str) -> bool:
        return '*' in tableId

    def get_scope(self) -> str:
        return 'extractor.bigquery_table_usage'
