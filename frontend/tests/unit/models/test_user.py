# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import flask
import unittest

from marshmallow import ValidationError

from amundsen_application.models.user import load_user, dump_user, UserSchema

app = flask.Flask(__name__)
app.config.from_object('amundsen_application.config.LocalConfig')


def mock_get_profile_url(app: str) -> str:
    return 'testUrl'


app.config['GET_PROFILE_URL'] = mock_get_profile_url


class UserTest(unittest.TestCase):
    def test_set_user_id_from_email(self) -> None:
        """
        Deserialization and serialization sets user_id from email if no user_id
        :return:
        """
        with app.test_request_context():
            self.assertEqual(dump_user(load_user({'email': 'test@test.com'})).get('user_id'), 'test@test.com')

    def test_set_display_name_from_full_name(self) -> None:
        """
        Deserialization and serialization sets display_name from full_name if no display_name and
        full_name is a non-empty string
        :return:
        """
        test_user = {
            'email': 'test@test.com',
            'full_name': 'Test User',
        }
        with app.test_request_context():
            self.assertEqual(dump_user(load_user(test_user)).get('display_name'), 'Test User')

    def test_set_display_name_from_email(self) -> None:
        """
        Deserialization and serialization sets display_name from email if no display_name and
        full_name is None
        :return:
        """
        with app.test_request_context():
            self.assertEqual(dump_user(load_user({'email': 'test@test.com'})).get('display_name'), 'test@test.com')

    def test_set_display_name_from_email_if_full_name_empty(self) -> None:
        """
        Deserialization and serialization sets display_name from email if no display_name and
        full_name is ''
        :return:
        """
        test_user = {
            'email': 'test@test.com',
            'full_name': '',
        }
        with app.test_request_context():
            self.assertEqual(dump_user(load_user(test_user)).get('display_name'), 'test@test.com')

    def test_profile_url(self) -> None:
        """
        Deserialization and serialization sets profile_url from app.config['GET_PROFILE_URL']
        if no profile_url provided'
        :return:
        """
        with app.test_request_context():
            self.assertEqual(dump_user(load_user({'email': 'test@test.com'})).get('profile_url'), 'testUrl')

    def test_raise_error_if_no_display_name(self) -> None:
        """
        Error is raised if deserialization of Dict will not generate a display_name
        :return:
        """
        with app.test_request_context():
            with self.assertRaises(ValidationError):
                UserSchema().load({})

    def test_raise_error_if_no_user_id(self) -> None:
        """
        Error is raised if deserialization of Dict will not generate a user_id
        :return:
        """
        with app.test_request_context():
            with self.assertRaises(ValidationError):
                UserSchema().load({'display_name': 'Test User'})

    def test_str_no_value(self) -> None:
        """
        Test _str_no_value returns True for a string of spaces
        :return:
        """
        self.assertEqual(UserSchema()._str_no_value(' '), True)
