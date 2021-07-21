# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import copy
import logging
from typing import (
    Any, Callable, Dict, Iterator, List, Union,
)

import requests
from jsonpath_rw import parse
from retrying import retry

from databuilder.rest_api.base_rest_api_query import BaseRestApiQuery
from databuilder.rest_api.query_merger import QueryMerger

LOGGER = logging.getLogger(__name__)


class RestApiQuery(BaseRestApiQuery):
    """
    A generic REST API Query that can be joined with other REST API query.
    Major feature of RestApiQuery is the fact that it is joinable with other RestApiQuery.

    Two main problems RestAPIQuery is trying to solve is:
      1. How to retrieve values that I want from the REST API's result. (value extraction)
      2. Most of the cases, one call is not enough. How to join the queries together to get the result that I want?

    On "1" value extraction: RestApiQuery uses JSONPath which is similar product as XPATH of XML.
    https://goessner.net/articles/JsonPath/

    On "2" join: The idea on joining REST API is the fact that previous query's result is used to query subsequent
    query.

    To bring this into implementation:
      1. It accepts prior RestApiQuery as a constructor -- Decorator pattern
      2. When URL is formed, it uses previous query's result to compute the URL
        e.g: Previous record: {"dashboard_id": "foo"},
             URL before: http://foo.bar/dashboard/{dashboard_id}
             URL after compute: http://foo.bar/dashboard/foo

    With this pattern RestApiQuery supports 1:1 and 1:N JOIN relationship.
    (GROUP BY or any other aggregation, sub-query join is not supported)


    Supports basic HTTP authentication.

    Extension point is available for other authentication scheme such as Oauth.
    Extension point is available for pagination.

    All extension point is designed for subclass because there's no exact standard on Oauth and pagination.

    (How it would work with Tableau/Looker is described in docstring of _authenticate method)
    """

    def __init__(self,
                 query_to_join: BaseRestApiQuery,
                 url: str,
                 params: Dict[str, Any],
                 json_path: str,
                 field_names: List[str],
                 fail_no_result: bool = False,
                 skip_no_result: bool = False,
                 json_path_contains_or: bool = False,
                 can_skip_failure: Callable = None,
                 query_merger: QueryMerger = None,
                 **kwargs: Any
                 ) -> None:
        """
        :param query_to_join: Previous query to JOIN. RestApiQuerySeed can be used for the first query
        :param url: URL string. It will use <str>.format operation using record that comes from previous query to
        substitute any variable that URL has.
        e.g: Previous record: {"dashboard_id": "foo"},
             URL before: http://foo.bar/dashboard/{dashboard_id}
             URL after compute: http://foo.bar/dashboard/foo

        :param params: A keyword arguments that pass into requests.get function.
            https://requests.readthedocs.io/en/master/user/quickstart/#make-a-request
        :param json_path: A JSONPath expression. https://github.com/kennknowles/python-jsonpath-rw
        Example:
            JSON result:
            [{"report_id": "1", "report_name": "first report", "foo": "bar"},
             {"report_id": "2", "report_name": "second report"}]

            JSON PATH:
            [*].[report_id,report_name]

            ["1", "first report", "2", "second report"]
        :param field_names: Field names to be used on the result. Result is dictionary where field_name will be the key
         and the values extracted via JSON PATH will be the value.

            JSON Path result:
                ["1", "first report", "2", "second report"]

            field_names:
                ["dashboard_id", "dashboard_description"]

            {"dashboard_id": "1", "dashboard_description": "first report"}
            {"dashboard_id": "2", "dashboard_description": "second report"}

        :param fail_no_result: If there's no result from the query it will make it fail.
        :param skip_no_result: If there's no result from the query, it will skip this record.
        :param json_path_contains_or: JSON Path expression accepts | ( OR ) operation, mostly to extract values in
        different level. In this case, JSON Path will extract the value from first expression and then second,
        and so forth.
        :param query_merger: to update record_dict yield by this rest api query with the query_merger's query results.

        Example:
            JSON result:
            [{"report_id": "1", "report_name": "first report", "foo": {"bar": "baz"}},
             {"report_id": "2", "report_name": "second report", "foo": {"bar": "box"}}]

            JSON PATH:
            ([*].report_id) | ([*].(foo.bar))

            ["1", "2", "baz", "box"]

        :param can_skip_failure A function that can determine if it can skip the failure. See BaseFailureHandler for
        the function interface

        """
        self._inner_rest_api_query = query_to_join
        self._url = url
        self._params = params
        self._json_path = json_path
        if ',' in json_path and '|' in json_path:
            raise Exception('RestApiQuery does not support "and (,)" and "or (|)" at the same time')

        self._jsonpath_expr = parse(self._json_path)
        self._fail_no_result = fail_no_result
        self._skip_no_result = skip_no_result
        self._field_names = field_names
        self._json_path_contains_or = json_path_contains_or
        self._can_skip_failure = can_skip_failure
        self._more_pages = False
        self._query_merger = query_merger

    def execute(self) -> Iterator[Dict[str, Any]]:  # noqa: C901
        self._authenticate()

        for record_dict in self._inner_rest_api_query.execute():

            first_try = True  # To control pagination. Always pass the while loop on the first try
            while first_try or self._more_pages:
                first_try = False

                url = self._preprocess_url(record=record_dict)

                try:
                    response = self._send_request(url=url)
                except Exception as e:
                    if self._can_skip_failure and self._can_skip_failure(exception=e):
                        continue
                    raise e

                response_json: Union[List[Any], Dict[str, Any]] = response.json()

                # value extraction via JSON Path
                result_list: List[Any] = [match.value for match in self._jsonpath_expr.find(response_json)]

                if not result_list:
                    log_msg = f'No result from URL: {self._url}, JSONPATH: {self._json_path} , ' \
                              f'response payload: {response_json}'
                    LOGGER.info(log_msg)

                    self._post_process(response)

                    if self._fail_no_result:
                        raise Exception(log_msg)

                    if self._skip_no_result:
                        continue

                    yield copy.deepcopy(record_dict)

                sub_records = RestApiQuery._compute_sub_records(result_list=result_list,
                                                                field_names=self._field_names,
                                                                json_path_contains_or=self._json_path_contains_or)

                for sub_record in sub_records:
                    if not sub_record or len(sub_record) != len(self._field_names):
                        # skip the record
                        continue
                    new_record_dict = copy.deepcopy(record_dict)
                    for field_name in self._field_names:
                        new_record_dict[field_name] = sub_record.pop(0)
                    if self._query_merger:
                        self._query_merger.merge_into(new_record_dict)
                    yield new_record_dict

                self._post_process(response)

    def _preprocess_url(self, record: Dict[str, Any]) -> str:
        """
        Performs variable substitution using a dict comes as a record from previous query.
        :param record:
        :return: a URL that is ready to be called.
        """
        return self._url.format(**record)

    @retry(stop_max_attempt_number=5, wait_exponential_multiplier=1000, wait_exponential_max=10000)
    def _send_request(self, url: str) -> requests.Response:
        """
        Performs HTTP GET operation with retry on failure.
        :param url:
        :return:
        """
        LOGGER.info('Calling URL %s', url)
        response = requests.get(url, **self._params)
        response.raise_for_status()
        return response

    @classmethod
    def _compute_sub_records(cls,
                             result_list: List[Any],
                             field_names: List[str],
                             json_path_contains_or: bool = False,
                             ) -> List[List[Any]]:
        """
        The behavior of JSONPATH is different when it's extracting multiple fields using AND(,) vs OR(|)
        If it uses AND(,), first n records will be first record. If it uses OR(|), it will list first field of all
        records, and then second field of all records etc.

        For example, when we have 3 fields to extract using "AND(,)" in JSONPATH:
            Result from JSONPATH:
            ['1', 'a', 'x', '2', 'b', 'y', '3', 'c', 'z']

            Resulting 3 records (means that original JSON has an array of size 3):
            ['1', 'a', 'x'], ['2', 'b', 'y'], ['3', 'c', 'z']

        When we have two fields and extracting using "OR(|)" in JSONPATH, the result is follow:
            Result from JSONPATH:
            ['1', '2', '3', 'a', 'b', 'c']

            Resulting 3 records (means that original JSON has an array of size 3):
            ['1', 'a'], ['2', 'b'], ['3', 'c']

        :param result_list:
        :param field_names:
        :param json_path_contains_or:
        :return:
        """

        if not field_names:
            raise Exception('Field names should not be empty')

        if not json_path_contains_or:
            return [result_list[i:i + len(field_names)] for i in range(0, len(result_list), len(field_names))]

        result = []
        num_subresult = int(len(result_list) / len(field_names))
        for i in range(num_subresult):
            sub_result = [result_list[j] for j in range(i, len(result_list), num_subresult)]
            result.append(sub_result)

        return result

    def _post_process(self, response: requests.Response) -> None:
        """
        Extension point for post-processing such thing as pagination
        :return:
        """
        pass

    def _authenticate(self) -> None:
        """
        Extension point to support other authentication mechanism such as Oauth.
        Subclass this class and implement authentication process.

        This assumes that most of authentication process can work with updating member variable such as url and params

        For example, Tableau's authentication pattern is that of Oauth where you need to call end point with JSON
        payload via POST method. This call will return one-time token along with LUID. On following calls,
        one time token needs to be added on header, and LUID needs to be used to form URL to fetch information.

        This is why url and params is part of RestApiQuery's member variable and above operation can be done by
        mutating these two values.

        Another Dashboard product Looker uses Oauth for authentication, and it can be done in similar way as Tableau.

        :return: None
        """
        pass
