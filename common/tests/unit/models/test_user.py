# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import flask
import unittest

from marshmallow import ValidationError

from amundsen_common.models.user import UserSchema

app = flask.Flask(__name__)


class UserTest(unittest.TestCase):
    def test_set_user_id_from_email(self) -> None:
        """
        Deserialization and serialization sets user_id from email if no user_id
        :return:
        """
        with app.test_request_context():
            self.assertEqual(
                UserSchema().load({"email": "test@test.com"}).user_id, "test@test.com"
            )

    def test_set_display_name_from_full_name(self) -> None:
        """
        Deserialization and serialization sets display_name from full_name if no display_name and
        full_name is a non-empty string
        :return:
        """
        test_user = {"email": "test@test.com", "full_name": "Test User"}
        with app.test_request_context():
            self.assertEqual(UserSchema().load(test_user).display_name, "Test User")

    def test_set_display_name_from_email(self) -> None:
        """
        Deserialization and serialization sets display_name from email if no display_name and
        full_name is None
        :return:
        """
        with app.test_request_context():
            self.assertEqual(
                UserSchema().load({"email": "test@test.com"}).display_name,
                "test@test.com",
            )

    def test_set_display_name_from_email_if_full_name_empty(self) -> None:
        """
        Deserialization and serialization sets display_name from email if no display_name and
        full_name is ''
        :return:
        """
        test_user = {"email": "test@test.com", "full_name": ""}
        with app.test_request_context():
            self.assertEqual(UserSchema().load(test_user).display_name, "test@test.com")

    def test_profile_url(self) -> None:
        """
        Deserialization and serialization sets profile_url from function defined at GET_PROFILE_URL
        if no profile_url provided'
        :return:
        """
        test_user = {"email": "test@test.com", "GET_PROFILE_URL": lambda _: "testUrl"}

        with app.test_request_context():
            self.assertEqual(UserSchema().load(test_user).profile_url, "testUrl")

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
                UserSchema().load({"display_name": "Test User"})

    def test_str_no_value(self) -> None:
        """
        Test _str_no_value returns True for a string of spaces
        :return:
        """
        self.assertEqual(UserSchema()._str_no_value(" "), True)

    def test_extra_key_does_not_raise(self) -> None:
        """
        Handle extra keys in the user data
        :return:
        """
        test_user = {"email": "test@test.com", "foo": "bar"}
        with app.test_request_context():
            self.assertEqual(UserSchema().load(test_user).email, "test@test.com")
