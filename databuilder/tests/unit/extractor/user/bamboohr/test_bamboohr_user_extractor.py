# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import io
import os
import unittest

import responses
from pyhocon import ConfigFactory

from databuilder.extractor.user.bamboohr.bamboohr_user_extractor import BamboohrUserExtractor
from databuilder.models.user import User


class TestBamboohrUserExtractor(unittest.TestCase):
    @responses.activate
    def test_parse_testdata(self) -> None:
        bhr = BamboohrUserExtractor()
        bhr.init(ConfigFactory.from_dict({'api_key': 'api_key', 'subdomain': 'amundsen'}))

        testdata_xml = os.path.join(
            os.path.dirname(os.path.realpath(__file__)),
            '../../../resources/extractor/user/bamboohr/testdata.xml'
        )

        with io.open(testdata_xml) as testdata:
            responses.add(responses.GET, bhr._employee_directory_uri(), body=testdata.read())

        expected = User(
            email='roald@amundsen.io',
            first_name='Roald',
            last_name='Amundsen',
            name='Roald Amundsen',
            team_name='508 Corporate Marketing',
            role_name='Antarctic Explorer',
        )

        actual_users = list(bhr._get_extract_iter())

        self.assertEqual(1, len(actual_users))
        self.assertEqual(repr(expected), repr(actual_users[0]))


if __name__ == '__main__':
    unittest.main()
