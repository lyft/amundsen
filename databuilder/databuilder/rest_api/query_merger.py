# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

from typing import Any, Dict

from databuilder.rest_api.base_rest_api_query import BaseRestApiQuery


class QueryMerger:
    """
    To be used in rest_api_query

    e.g. Assuming
            query_merger = QueryMerger(query_to_merge=spaces_query, merge_key='dashboard_group_id'),
         where spaces_query yields a record like
            {
             'dashboard_group_id': 'ggg',
             'dashboard_group': 'dashboard group'
            },
         and RestApiQuery's inner_rest_api_query.execute() returns a record of
            {
             'dashboard_id': 'ddd',
             'dashboard_name': 'dashboard_name',
             'dashboard_group_id': 'ggg'
             },
         the final yield record_dict from RestApiQuery(query_merger=query_merger).execute() will be
            {
             'dashboard_id': 'ddd',
             'dashboard_name': 'dashboard_name',
             'dashboard_group_id': 'ggg',
             'dashboard_group': 'dashboard group'
            }
    """
    def __init__(self,
                 query_to_merge: BaseRestApiQuery,
                 merge_key: str,
                 ) -> None:
        self._query_to_merge = query_to_merge
        self._merge_key = merge_key
        self._computed_query_result: Dict[Any, Any] = dict()

    def merge_into(self, record_dict: dict) -> None:
        """
        Merge results of query_to_merge into record_dict. Update record_dict in place.

        :param record_dict: the record_dict to be updated in place
        :return:
        """
        # compute query results for easy lookup later to find the exact record to merge
        if not self._computed_query_result:
            self._computed_query_result = self._compute_query_result()

        value_of_merge_key = record_dict.get(self._merge_key)
        record_dict_to_merge = self._computed_query_result.get(value_of_merge_key)
        if not record_dict_to_merge:
            raise Exception(f'{self._merge_key} {value_of_merge_key} not found in query_to_merge results')
        # we don't want the query merger to overwrite values of existing keys in record_dict
        filterd_record_dict_to_merge = {
            key: record_dict_to_merge[key] for key in record_dict_to_merge if key not in record_dict
        }
        record_dict.update(filterd_record_dict_to_merge)

    def _compute_query_result(self) -> Dict[Any, Any]:
        """
        Transform the query result to a dictionary.

        Assuming merge_key is 'dashboard_id' and self._query_to_merge.execute() returns
            iter([{'dashboard_id': 'd1', 'dashboard_name': 'n1'}, {'dashboard_id': 'd2', 'dashboard_name': 'n2'}]),
        the returned dict of this method will look like
            {
             'd1': {'dashboard_id': 'd1', 'dashboard_name': 'n1'},
             'd2': {'dashboard_id': 'd2', 'dashboard_name': 'n2'},
            }

        :return: a dictionary
        """
        computed_query_results: Dict[Any, Any] = dict()
        iterator = self._query_to_merge.execute()

        while True:
            try:
                record = next(iterator)
            except StopIteration:
                return computed_query_results

            value_of_merge_key = record[self._merge_key]
            if value_of_merge_key in computed_query_results:
                raise Exception(
                    f'merge_key {self._merge_key} value {value_of_merge_key} is not unique across the query results'
                )

            computed_query_results[value_of_merge_key] = record
