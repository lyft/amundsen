# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import unittest
from typing import Any, Dict

from search_service import create_app


class TestSwagger(unittest.TestCase):

    def setUp(self) -> None:
        config_module_class = 'search_service.config.LocalConfig'
        self.app = create_app(config_module_class=config_module_class)
        self.app_context = self.app.app_context()
        self.app_context.push()

    def tearDown(self) -> None:
        self.app_context.pop()

    def test_should_get_swagger_docs(self) -> None:
        response = self.app.test_client().get('/apidocs/')
        self.assertEqual(response.status_code, 200)

    def test_should_get_swagger_json(self) -> None:
        response = self.app.test_client().get('/apispec_1.json')

        self.assertEqual(response.status_code, 200)

    def test_should_have_a_component_from_each_reference(self) -> None:
        response = self.app.test_client().get('/apispec_1.json')

        for reference in list(TestSwagger.find('$ref', response.json)):  # type: ignore
            path_to_component = reference[2:].split('/')

            json_response_to_reduce = response.json
            for key in path_to_component:
                try:
                    json_response_to_reduce = json_response_to_reduce[key]  # type: ignore
                except KeyError:
                    self.fail(f'The following $ref does not have a valid component to reference. $ref: {reference}')

    # This is a requirement from Flasgger not Swagger
    def test_should_have_type_for_each_query_parameter(self) -> None:
        response = self.app.test_client().get('/apispec_1.json')

        for request_params in list(TestSwagger.find('parameters', response.json)):  # type: ignore
            for param in request_params:
                if param['in'] == 'query' and 'type' not in param.keys():
                    self.fail(f'The following query parameter is missing a type: {param}')

    def test_should_have_all_endpoints_in_swagger(self) -> None:
        paths_excluded_from_swagger = ['/apidocs/index.html', '/apispec_1.json', '/apidocs/',
                                       '/flasgger_static/{path:filename}', '/static/{path:filename}']

        response = self.app.test_client().get('/apispec_1.json')

        paths_in_swagger = response.json.get('paths').keys()  # type: ignore
        for endpoint in [rule.rule for rule in self.app.url_map.iter_rules()]:
            endpoint = endpoint.replace('<', '{').replace('>', '}')
            if endpoint not in paths_excluded_from_swagger and endpoint not in paths_in_swagger:
                self.fail(f'The following endpoint is not in swagger: {endpoint}')

    @staticmethod
    def find(key: str, json_response: Dict[str, Any]) -> Any:
        for json_key, json_value in json_response.items():
            if json_key == key:
                yield json_value
            elif isinstance(json_value, dict):
                for result in TestSwagger.find(key, json_value):
                    yield result
