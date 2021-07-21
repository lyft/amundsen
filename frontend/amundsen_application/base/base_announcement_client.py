# Copyright Contributors to the Amundsen project.
# SPDX-License-Identifier: Apache-2.0

import abc
import logging

from http import HTTPStatus

from flask import jsonify, make_response, Response
from marshmallow import ValidationError

from amundsen_application.models.announcements import Announcements, AnnouncementsSchema


class BaseAnnouncementClient(abc.ABC):
    @abc.abstractmethod
    def __init__(self) -> None:
        pass  # pragma: no cover

    @abc.abstractmethod
    def get_posts(self) -> Announcements:
        """
        Returns an instance of amundsen_application.models.announcements.Announcements, which should match
        amundsen_application.models.announcements.AnnouncementsSchema
        """
        pass  # pragma: no cover

    def _get_posts(self) -> Response:
        def _create_error_response(message: str) -> Response:
            logging.exception(message)
            payload = jsonify({'posts': [], 'msg': message})
            return make_response(payload, HTTPStatus.INTERNAL_SERVER_ERROR)

        try:
            announcements = self.get_posts()
        except Exception as e:
            message = 'Encountered exception getting posts: ' + str(e)
            return _create_error_response(message)

        try:
            data = AnnouncementsSchema().dump(announcements)
            AnnouncementsSchema().load(data)  # validate returned object
            payload = jsonify({'posts': data.get('posts'), 'msg': 'Success'})
            return make_response(payload, HTTPStatus.OK)
        except ValidationError as err:
            message = 'Announcement data dump returned errors: ' + str(err.messages)
            return _create_error_response(message)
